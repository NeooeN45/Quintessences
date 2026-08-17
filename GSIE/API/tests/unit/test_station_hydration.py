"""Tests unitaires — hydratation stationnelle fail-closed (DEC-000072).

Ce que ces tests éprouvent, et qui est l'essentiel : l'hydrateur ne peut
rien inventer. Un bloc sans provenance complète n'est pas construit, une
observation hors du mapping déclaré est rapportée et non rangée, et un
niveau de preuve déclaré par l'appelant reste visible dans le rapport.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from gsie_api.data.field_intake_station import StationIntake
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.orchestration.hydration import (
    StationContexteHydrator,
    _bloc_geographie,
    _blocs_depuis_intake,
    _valider_niveaux_declares,
)
from gsie_api.engines.orchestration.schemas import AnalyseRequest
from gsie_api.engines.reasoning.schemas import SourceMoteurContexte
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel
from gsie_api.infrastructure.models.spatial_temporal import PlaceModel

_SOURCE = SourceReference(
    type_source=SourceType.referentiel_officiel,
    auteur="INRAE (2008)",
    reference="Référentiel pédologique français, édition 2008",
)

_DATE = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)


def _observation(
    observation_type: str,
    value: float,
    *,
    unit: str,
    observed_at: datetime = _DATE,
) -> dict:
    return {
        "observation_type": observation_type,
        "value": value,
        "unit": unit,
        "method_id": "methode-test",
        "method_version": "1.0",
        "observed_at": observed_at.isoformat(),
    }


def _station(*observations: dict) -> StationIntake:
    return StationIntake.model_validate(
        {
            "context": {"parcelle": "test"},
            "observations": list(observations),
        }
    )


def _intake(
    station: StationIntake | None = None, *, payload: dict | None = None
) -> FieldIntakeModel:
    brut = payload if payload is not None else {"station": station.model_dump(mode="json")}
    return FieldIntakeModel(
        id=uuid4(),
        submitted_by=uuid4(),
        application_key="geosylva-test",
        client_event_id="evt-1",
        kind="observation",
        observed_at=_DATE,
        status="accepted",
        payload=brut,
        provenance={"application_key": "geosylva-test"},
        payload_hash="a" * 64,
    )


# --- _valider_niveaux_declares ----------------------------------------------


def should_accept_declared_levels_on_known_blocks() -> None:
    _valider_niveaux_declares({"geographie": EvidenceLevel.C, "peuplement": EvidenceLevel.E})


def should_reject_declared_level_on_unknown_block() -> None:
    with pytest.raises(ValueError, match="blocs inconnus ou non déclarables"):
        _valider_niveaux_declares({"correlations": EvidenceLevel.A})


# --- _bloc_geographie --------------------------------------------------------


def _place(**overrides: object) -> PlaceModel:
    base: dict[str, object] = {"id": uuid4(), "srid": 2154}
    base.update(overrides)
    return PlaceModel(**base)  # type: ignore[arg-type]


def _resource(place_id: UUID) -> ResourceModel:
    return ResourceModel(id=place_id, type="place", gsie_id="PLC-0001", created_at=_DATE)


def should_build_geographie_bloc_with_all_values() -> None:
    place = _place(label="La Vergne", area_m2=12500.0)
    bloc = _bloc_geographie(place, _resource(place.id), EvidenceLevel.E, 2.35, 45.6)

    assert bloc.source_moteur == SourceMoteurContexte.gis
    assert bloc.evidence_level == EvidenceLevel.E
    assert bloc.valeurs == {
        "srid": 2154,
        "label": "La Vergne",
        "area_m2": 12500.0,
        "longitude": 2.35,
        "latitude": 45.6,
    }
    assert bloc.source.reference == "PLC-0001"
    assert bloc.date_observation == _DATE


def should_build_geographie_bloc_with_srid_only_when_place_is_bare() -> None:
    place = _place()
    bloc = _bloc_geographie(place, _resource(place.id), EvidenceLevel.E, None, None)

    assert bloc.valeurs == {"srid": 2154}


def should_fall_back_to_uuid_reference_when_gsie_id_missing() -> None:
    place = _place()
    resource = _resource(place.id)
    resource.gsie_id = None

    bloc = _bloc_geographie(place, resource, EvidenceLevel.E, None, None)

    assert bloc.source.reference == f"resource:{place.id}"


# --- _blocs_depuis_intake ----------------------------------------------------


def should_map_observations_to_declared_blocks() -> None:
    station = _station(
        _observation("stems_per_ha", 300.0, unit="stems_per_ha"),
        _observation("pH", 5.2, unit="pH"),
        _observation("annual_precipitation_mm", 950.0, unit="mm"),
    )
    blocs, non_mappees, non_constructibles, utilises = _blocs_depuis_intake(
        _intake(station),
        station,
        {
            "peuplement": EvidenceLevel.E,
            "pedologie": EvidenceLevel.D,
            "climat": EvidenceLevel.D,
        },
    )

    assert set(blocs) == {"peuplement", "pedologie", "climat"}
    assert blocs["peuplement"].valeurs == {"stems_per_ha": 300.0}
    assert blocs["peuplement"].source_moteur == SourceMoteurContexte.terrain
    assert blocs["pedologie"].valeurs == {"pH": 5.2}
    assert non_mappees == []
    assert non_constructibles == []
    assert utilises == ["climat", "pedologie", "peuplement"]


def should_report_unmapped_observation_instead_of_filing_it() -> None:
    station = _station(
        _observation("stems_per_ha", 300.0, unit="stems_per_ha"),
        {
            "observation_type": "canopy_cover_pct",
            "value": 80.0,
            "unit": "%",
            "method_id": "m",
            "method_version": "1.0",
            "observed_at": _DATE.isoformat(),
        },
    )
    blocs, non_mappees, _, _ = _blocs_depuis_intake(
        _intake(station), station, {"peuplement": EvidenceLevel.E}
    )

    assert set(blocs) == {"peuplement"}
    assert non_mappees == ["canopy_cover_pct"]


def should_refuse_block_without_declared_level_and_name_it() -> None:
    station = _station(_observation("stems_per_ha", 300.0, unit="stems_per_ha"))
    blocs, _, non_constructibles, utilises = _blocs_depuis_intake(_intake(station), station, {})

    assert blocs == {}
    assert utilises == []
    assert [echec.nom_bloc for echec in non_constructibles] == ["peuplement"]
    assert "niveau de preuve absent" in non_constructibles[0].motif


def should_keep_latest_observation_date_per_block() -> None:
    ancienne = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
    recente = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    station = _station(
        _observation("stems_per_ha", 300.0, unit="stems_per_ha", observed_at=ancienne),
        _observation("basal_area_m2_ha", 24.0, unit="m2/ha", observed_at=recente),
    )
    blocs, _, _, _ = _blocs_depuis_intake(
        _intake(station), station, {"peuplement": EvidenceLevel.E}
    )

    assert blocs["peuplement"].date_observation == recente


def should_cite_the_intake_as_source_of_terrain_blocks() -> None:
    station = _station(_observation("stems_per_ha", 300.0, unit="stems_per_ha"))
    intake = _intake(station)
    blocs, _, _, _ = _blocs_depuis_intake(intake, station, {"peuplement": EvidenceLevel.E})

    source = blocs["peuplement"].source
    assert source.type_source == SourceType.observation_terrain
    assert source.auteur == "application geosylva-test"
    assert source.reference == f"field_intake:{intake.id}"
    assert source.version_source == "station_intake.v0.1"


# --- Contrat AnalyseRequest (DEC-000072 §4) -----------------------------------


def _requete_brute(**overrides: object) -> dict:
    base: dict[str, object] = {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "regles": [
            {
                "identifiant": "regle-01",
                "condition": "peuplement_stems_per_ha > 100",
                "enonce_conclusion": "Peuplement dense.",
                "source": _SOURCE.model_dump(mode="json"),
                "evidence_level": "B",
                "niveau_confiance": 0.8,
            }
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-01",
                "role": "atout",
                "domaine_element": "sylvicole",
            }
        ],
        "etat_global": {
            "etat": "sain",
            "justification": "Peuplement suivi sur placette",
            "source": _SOURCE.model_dump(mode="json"),
            "evidence_level": "B",
        },
        "question": "Quelle conduite sylvicole ?",
        "objectif_forestier": "production",
    }
    base.update(overrides)
    return base


def should_accept_request_without_contexte_for_hydration() -> None:
    requete = AnalyseRequest.model_validate(
        _requete_brute(niveaux_preuve_declares={"peuplement": "E"})
    )

    assert requete.contexte is None
    assert requete.niveaux_preuve_declares == {"peuplement": EvidenceLevel.E}


def should_reject_declared_levels_when_contexte_is_provided() -> None:
    contexte = {
        "peuplement": {
            "source_moteur": "TERRAIN",
            "source": _SOURCE.model_dump(mode="json"),
            "evidence_level": "E",
            "valeurs": {"stems_per_ha": 300},
        }
    }
    with pytest.raises(ValidationError, match="niveaux_preuve_declares sans effet"):
        AnalyseRequest.model_validate(
            _requete_brute(contexte=contexte, niveaux_preuve_declares={"peuplement": "E"})
        )


def should_reject_declared_level_on_unknown_block_in_request() -> None:
    with pytest.raises(ValidationError, match="blocs inconnus ou non déclarables"):
        AnalyseRequest.model_validate(_requete_brute(niveaux_preuve_declares={"geologie": "E"}))


def should_refuse_reasoning_request_without_any_contexte() -> None:
    requete = AnalyseRequest.model_validate(_requete_brute())

    with pytest.raises(ValueError, match="contexte stationnel absent"):
        requete.vers_requete_raisonnement()


# --- _centroide et _hydrater_terrain (branches sans base) ---------------------


async def should_return_no_coordinates_when_place_has_no_geometry() -> None:
    place = _place(geometry=None)

    assert await StationContexteHydrator(None)._centroide(place) == (None, None)  # type: ignore[arg-type]


class _ResultatVide:
    def first(self) -> None:
        return None


class _SessionSansLigne:
    async def execute(self, _statement: object) -> _ResultatVide:
        return _ResultatVide()


async def should_return_no_coordinates_when_centroid_query_finds_nothing() -> None:
    place = _place(geometry=object())

    assert await StationContexteHydrator(_SessionSansLigne())._centroide(place) == (  # type: ignore[arg-type]
        None,
        None,
    )


def should_report_accepted_intake_without_station_payload() -> None:
    intake = _intake(payload={"observations_libres": {}})

    blocs, non_mappees, non_constructibles, utilises = StationContexteHydrator(
        None  # type: ignore[arg-type]
    )._hydrater_terrain(intake, {})

    assert blocs == {}
    assert non_mappees == []
    assert utilises == []
    assert [echec.nom_bloc for echec in non_constructibles] == ["station"]
    assert "sans bloc station" in non_constructibles[0].motif


def should_report_non_compliant_station_payload() -> None:
    intake = _intake(payload={"station": {"inattendu": True}})

    _, _, non_constructibles, _ = StationContexteHydrator(None)._hydrater_terrain(intake, {})  # type: ignore[arg-type]

    assert [echec.nom_bloc for echec in non_constructibles] == ["station"]
    assert "non conforme" in non_constructibles[0].motif


# --- Garde anti-quarantaine ---------------------------------------------------


def _intake_modele(*, status: str) -> FieldIntakeModel:
    return FieldIntakeModel(
        id=uuid4(),
        submitted_by=uuid4(),
        application_key="geosylva-test",
        client_event_id="evt-1",
        kind="observation",
        observed_at=_DATE,
        status=status,
        payload={"station": {"context": {"parcelle": "test"}, "observations": []}},
        provenance={"application_key": "geosylva-test"},
        payload_hash="c" * 64,
    )


class _ResultatIntakes:
    def __init__(self, intakes: list[FieldIntakeModel]) -> None:
        self._intakes = intakes

    def scalars(self) -> "_ResultatIntakes":
        return self

    def __iter__(self) -> Iterator[FieldIntakeModel]:
        return iter(self._intakes)


class _SessionAvecIntakes:
    def __init__(self, intakes: list[FieldIntakeModel]) -> None:
        self._intakes = intakes

    async def execute(self, _statement: object) -> _ResultatIntakes:
        return _ResultatIntakes(self._intakes)


async def should_only_read_accepted_intake_and_ignore_quarantined_and_rejected() -> None:
    """La quarantaine est etanche : comptee, jamais lue pour ses valeurs."""
    quarantaine = _intake_modele(status="quarantined")
    rejetee = _intake_modele(status="rejected")

    intake, ignorees = await StationContexteHydrator(
        _SessionAvecIntakes([quarantaine, rejetee])
    )._charger_intake_acceptee(uuid4())

    assert intake is None
    assert ignorees == 2
