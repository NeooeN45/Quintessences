"""Hydratation stationnelle fail-closed (`DEC-000072`).

    station_id → StationContexte

Le contrat v1 du Reasoning Engine laissait l'assemblage du `StationContexte`
à l'appelant (« le branchement direct sur les moteurs se fera sans rupture
de contrat »). Ce module est ce branchement, borné à ce que la base connaît
déjà : aucun appel réseau externe n'est fait pendant l'hydratation.

Règles non négociables, toutes vérifiables dans le rapport persisté :

* **Ancre obligatoire** — `station_id` désigne d'abord une `Place` non
  supprimée ; à défaut, la soumission FieldIntake **acceptée** la plus
  récente qui la cible. Sans ancre : refus, l'identifiant est nommé.
* **Provenance complète ou rien** — un bloc exige source résolvable, date
  et niveau de preuve. Le niveau provient de la donnée lorsqu'elle le
  porte ; sinon il est **déclaré par l'appelant** (même philosophie que les
  qualifications et l'état global d'`AnalyseRequest`), et tout niveau
  déclaré utilisé est listé dans le rapport. Jamais de valeur par défaut,
  jamais de table de conversion confiance → niveau (`GSIE-CON-002`,
  `ADR-009`).
* **Quarantaine étanche** — les soumissions `quarantined`/`rejected` ne
  sont jamais lues pour leurs valeurs. Leur nombre est rapporté, pas leur
  contenu.
* **Aucun silence** — observation inconnue, payload non conforme, bloc
  faute de niveau : tout est nommé dans le `RapportHydratation`, qui
  accompagne la réponse et la preuve `analysis_run`.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.core.logging import get_logger
from gsie_api.data.field_intake_station import StationIntake
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

logger = get_logger("gsie_api.orchestration.hydration")

__all__ = [
    "BlocNonConstructible",
    "HydratationVideError",
    "RapportHydratation",
    "ResultatHydratation",
    "StationContexteHydrator",
    "StationIntrouvableError",
]

SCHEMA_VERSION_HYDRATATION: Literal["hydratation_station.v0.1"] = "hydratation_station.v0.1"

# Blocs dont le niveau de preuve peut être déclaré par l'appelant.
# `correlations` en est exclue : une corrélation hydratée proviendra du
# Correlation Engine (tranche future), jamais d'une déclaration.
BLOCS_NIVEAU_DECLARABLE: frozenset[str] = frozenset(
    {"geographie", "climat", "pedologie", "botanique", "peuplement"}
)

# Mapping observation_type (station_intake.v0.1) → bloc de StationContexte.
# Déclaré et versionné : une observation qui n'y figure pas n'est pas
# rangée d'office, elle est rapportée (`DEC-000072` §3).
_BLOC_PAR_OBSERVATION: dict[str, str] = {
    "stems_per_ha": "peuplement",
    "basal_area_m2_ha": "peuplement",
    "mean_diameter_cm": "peuplement",
    "dominant_height_m": "peuplement",
    "volume_m3_ha": "peuplement",
    "pH": "pedologie",
    "depth_cm": "pedologie",
    "annual_precipitation_mm": "climat",
    "annual_temperature_c": "climat",
    "hydric_deficit_mm": "climat",
}


class StationIntrouvableError(Exception):
    """Aucune ancre (Place, FieldIntake acceptée) pour ce `station_id`."""


class HydratationVideError(Exception):
    """La station existe mais aucun bloc n'a pu être construit.

    Le message nomme chaque manque : une erreur « contexte vide » sans
    motif obligerait l'appelant à deviner quelle provenance compléter.
    """


class BlocNonConstructible(BaseModel):
    """Un bloc demandé par les données mais faute de provenance complète."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nom_bloc: str = Field(min_length=1, max_length=50)
    motif: str = Field(min_length=1, max_length=500)


class RapportHydratation(BaseModel):
    """Trace complète de l'assemblage — persistée avec la preuve d'analyse."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["hydratation_station.v0.1"] = SCHEMA_VERSION_HYDRATATION
    station_id: UUID
    ancre_place: UUID | None = None
    ancre_field_intake: UUID | None = None
    soumissions_quarantaine_ignorees: int = Field(
        default=0, ge=0, description="Soumissions non relues, jamais lues pour leurs valeurs"
    )
    blocs_construits: list[str] = Field(default_factory=list)
    blocs_non_constructibles: list[BlocNonConstructible] = Field(default_factory=list)
    niveaux_declares_utilises: list[str] = Field(
        default_factory=list,
        description="Blocs dont le niveau de preuve est déclaré par l'appelant",
    )
    observations_non_mappees: list[str] = Field(
        default_factory=list,
        description="observation_type absents du mapping déclaré, jamais rangés d'office",
    )


class ResultatHydratation(BaseModel):
    """Contexte assemblé et son rapport — indissociables (`GSIE-CON-004`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contexte: StationContexte
    rapport: RapportHydratation


def _source_place(gsie_id: str | None, place_id: UUID, cree_le: datetime) -> SourceReference:
    """La resource Place est citée elle-même : déclarée par une application
    de terrain, elle est une observation, pas un référentiel."""
    return SourceReference(
        type_source=SourceType.observation_terrain,
        auteur="registre Quintessences — resource place",
        reference=gsie_id or f"resource:{place_id}",
        date_publication=cree_le.date().isoformat(),
    )


def _bloc_geographie(
    place: PlaceModel,
    resource: ResourceModel,
    niveau: EvidenceLevel,
    longitude: float | None,
    latitude: float | None,
) -> BlocContexte:
    """Bloc géographique depuis la Place — seules les valeurs présentes."""
    valeurs: dict[str, float | int | str | bool] = {"srid": place.srid}
    if place.label is not None:
        valeurs["label"] = place.label
    if place.area_m2 is not None:
        valeurs["area_m2"] = place.area_m2
    if longitude is not None and latitude is not None:
        valeurs["longitude"] = longitude
        valeurs["latitude"] = latitude
    return BlocContexte(
        source_moteur=SourceMoteurContexte.gis,
        source=_source_place(resource.gsie_id, place.id, resource.created_at),
        evidence_level=niveau,
        valeurs=valeurs,
        date_observation=resource.created_at,
    )


def _blocs_depuis_intake(
    intake: FieldIntakeModel,
    station: StationIntake,
    niveaux_declares: dict[str, EvidenceLevel],
) -> tuple[dict[str, BlocContexte], list[str], list[BlocNonConstructible], list[str]]:
    """Assemble les blocs terrain d'une soumission acceptée.

    Retourne les blocs construits, les `observation_type` non mappés, les
    blocs faute de niveau déclaré et les niveaux déclarés réellement
    utilisés. Aucune valeur n'est inventée ni rangée hors du mapping.
    """
    valeurs_par_bloc: dict[str, dict[str, float | int | str | bool]] = {}
    dates_par_bloc: dict[str, datetime] = {}
    non_mappees: list[str] = []
    for observation in station.observations:
        nom_bloc = _BLOC_PAR_OBSERVATION.get(observation.observation_type)
        if nom_bloc is None:
            non_mappees.append(observation.observation_type)
            continue
        valeurs_par_bloc.setdefault(nom_bloc, {})[observation.observation_type] = observation.value
        date_courante = dates_par_bloc.get(nom_bloc)
        if date_courante is None or observation.observed_at > date_courante:
            dates_par_bloc[nom_bloc] = observation.observed_at

    blocs: dict[str, BlocContexte] = {}
    non_constructibles: list[BlocNonConstructible] = []
    niveaux_utilises: list[str] = []
    source = SourceReference(
        type_source=SourceType.observation_terrain,
        auteur=f"application {intake.application_key}",
        reference=f"field_intake:{intake.id}",
        version_source=station.schema_version,
        date_publication=intake.observed_at.date().isoformat(),
    )
    for nom_bloc in sorted(valeurs_par_bloc):
        niveau = niveaux_declares.get(nom_bloc)
        if niveau is None:
            non_constructibles.append(
                BlocNonConstructible(
                    nom_bloc=nom_bloc,
                    motif=(
                        "niveau de preuve absent : la soumission terrain n'en porte "
                        "pas et l'appelant n'en déclare pas — aucun niveau n'est "
                        "inventé (DEC-000072 §2)"
                    ),
                )
            )
            continue
        blocs[nom_bloc] = BlocContexte(
            source_moteur=SourceMoteurContexte.terrain,
            source=source,
            evidence_level=niveau,
            valeurs=valeurs_par_bloc[nom_bloc],
            date_observation=dates_par_bloc[nom_bloc],
        )
        niveaux_utilises.append(nom_bloc)
    return blocs, non_mappees, non_constructibles, niveaux_utilises


def _valider_niveaux_declares(niveaux_declares: dict[str, EvidenceLevel]) -> None:
    inconnus = sorted(set(niveaux_declares) - BLOCS_NIVEAU_DECLARABLE)
    if inconnus:
        raise ValueError(
            f"niveaux déclarés pour des blocs inconnus ou non déclarables : {inconnus} ; "
            f"blocs acceptés : {sorted(BLOCS_NIVEAU_DECLARABLE)}"
        )


class StationContexteHydrator:
    """Assemble un `StationContexte` depuis la base, fail-closed.

    Même session que l'appelant : l'hydratation participe à la transaction
    de l'analyse, et la preuve persistée conserve le contexte exactement
    utilisé (rejouabilité, `DEC-000071`).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def hydrate(
        self,
        station_id: UUID,
        *,
        niveaux_declares: dict[str, EvidenceLevel] | None = None,
    ) -> ResultatHydratation:
        """Assemble le contexte ou refuse en nommant ce qui manque.

        Raises:
            StationIntrouvableError: aucune Place ni soumission acceptée.
            HydratationVideError: ancre présente, aucun bloc constructible.
            ValueError: niveau déclaré pour un bloc inconnu.
        """
        niveaux = dict(niveaux_declares or {})
        _valider_niveaux_declares(niveaux)

        place, resource = await self._charger_place(station_id)
        intake, quarantaine_ignorees = await self._charger_intake_acceptee(station_id)

        if place is None and intake is None:
            raise StationIntrouvableError(
                f"station {station_id} introuvable : ni Place enregistrée ni "
                "soumission terrain acceptée ne la désignent"
            )

        blocs: dict[str, BlocContexte] = {}
        non_constructibles: list[BlocNonConstructible] = []
        niveaux_utilises: list[str] = []
        non_mappees: list[str] = []

        if place is not None and resource is not None:
            bloc_geo, manque_geo = await self._hydrater_geographie(place, resource, niveaux)
            if bloc_geo is not None:
                blocs["geographie"] = bloc_geo
                if "geographie" in niveaux:
                    niveaux_utilises.append("geographie")
            if manque_geo is not None:
                non_constructibles.append(manque_geo)

        if intake is not None:
            blocs_terrain, ignorees, manques_terrain, utilises_terrain = self._hydrater_terrain(
                intake, niveaux
            )
            blocs.update(blocs_terrain)
            non_mappees.extend(ignorees)
            non_constructibles.extend(manques_terrain)
            niveaux_utilises.extend(utilises_terrain)

        if not blocs:
            manques = "; ".join(f"{echec.nom_bloc} : {echec.motif}" for echec in non_constructibles)
            raise HydratationVideError(
                f"station {station_id} : aucun bloc constructible — "
                f"{manques or 'aucune donnée stationnelle disponible'}"
            )

        rapport = RapportHydratation(
            station_id=station_id,
            ancre_place=place.id if place is not None else None,
            ancre_field_intake=intake.id if intake is not None else None,
            soumissions_quarantaine_ignorees=quarantaine_ignorees,
            blocs_construits=sorted(blocs),
            blocs_non_constructibles=non_constructibles,
            niveaux_declares_utilises=sorted(niveaux_utilises),
            observations_non_mappees=sorted(non_mappees),
        )
        logger.info(
            "hydratation_station",
            station_id=str(station_id),
            blocs_construits=rapport.blocs_construits,
            blocs_non_constructibles=[echec.nom_bloc for echec in non_constructibles],
        )
        return ResultatHydratation(
            contexte=StationContexte(
                geographie=blocs.get("geographie"),
                climat=blocs.get("climat"),
                pedologie=blocs.get("pedologie"),
                botanique=blocs.get("botanique"),
                peuplement=blocs.get("peuplement"),
            ),
            rapport=rapport,
        )

    async def _charger_place(
        self, station_id: UUID
    ) -> tuple[PlaceModel | None, ResourceModel | None]:
        statement = (
            select(PlaceModel, ResourceModel)
            .join(ResourceModel, PlaceModel.id == ResourceModel.id)
            .where(PlaceModel.id == station_id, ResourceModel.deleted_at.is_(None))
        )
        row = (await self._session.execute(statement)).first()
        if row is None:
            return None, None
        place, resource = row
        return place, resource

    async def _charger_intake_acceptee(
        self, station_id: UUID
    ) -> tuple[FieldIntakeModel | None, int]:
        """Plus récente soumission acceptée ciblant la station.

        Le tri est déterministe (date puis identifiant) : deux exécutions
        lisent la même soumission. Les soumissions en quarantaine ou
        rejetées sont comptées, jamais lues pour leurs valeurs.
        """
        statement = (
            select(FieldIntakeModel)
            .where(FieldIntakeModel.target_resource_id == station_id)
            .order_by(FieldIntakeModel.observed_at.desc(), FieldIntakeModel.id.desc())
        )
        soumissions = list((await self._session.execute(statement)).scalars())
        acceptees = [s for s in soumissions if s.status == "accepted"]
        ignorees = len(soumissions) - len(acceptees)
        return (acceptees[0] if acceptees else None), ignorees

    async def _hydrater_geographie(
        self,
        place: PlaceModel,
        resource: ResourceModel,
        niveaux: dict[str, EvidenceLevel],
    ) -> tuple[BlocContexte | None, BlocNonConstructible | None]:
        niveau = niveaux.get("geographie")
        if niveau is None:
            return None, BlocNonConstructible(
                nom_bloc="geographie",
                motif=(
                    "niveau de preuve absent : la Place n'en porte pas et "
                    "l'appelant n'en déclare pas (DEC-000072 §2)"
                ),
            )
        longitude, latitude = await self._centroide(place)
        return _bloc_geographie(place, resource, niveau, longitude, latitude), None

    async def _centroide(self, place: PlaceModel) -> tuple[float | None, float | None]:
        if place.geometry is None:
            return None, None
        statement = select(
            func.ST_X(func.ST_Centroid(PlaceModel.geom_4326)),
            func.ST_Y(func.ST_Centroid(PlaceModel.geom_4326)),
        ).where(PlaceModel.id == place.id)
        row = (await self._session.execute(statement)).first()
        if row is None or row[0] is None or row[1] is None:
            return None, None
        return float(row[0]), float(row[1])

    def _hydrater_terrain(
        self,
        intake: FieldIntakeModel,
        niveaux: dict[str, EvidenceLevel],
    ) -> tuple[dict[str, BlocContexte], list[str], list[BlocNonConstructible], list[str]]:
        station_brute = intake.payload.get("station")
        if station_brute is None:
            return (
                {},
                [],
                [
                    BlocNonConstructible(
                        nom_bloc="station",
                        motif="soumission acceptée sans bloc station (station_intake.v0.1)",
                    )
                ],
                [],
            )
        try:
            station = StationIntake.model_validate(station_brute)
        except ValueError:
            return (
                {},
                [],
                [
                    BlocNonConstructible(
                        nom_bloc="station",
                        motif="payload station non conforme à station_intake.v0.1",
                    )
                ],
                [],
            )
        return _blocs_depuis_intake(intake, station, niveaux)
