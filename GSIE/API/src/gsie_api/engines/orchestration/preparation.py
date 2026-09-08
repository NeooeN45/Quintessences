"""Préparation fail-closed d'une analyse stationnelle.

Cette couche assemble uniquement des entrées déjà qualifiées : contexte hydraté,
règles applicables du Knowledge Engine et état global provenant d'un FieldIntake
accepté. Elle ne déduit aucun état et ne transforme aucune confiance en preuve.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from gsie_api.engines.diagnostic.schemas import EtatGlobalDeclare
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference  # noqa: TC001
from gsie_api.engines.knowledge.engine import KnowledgeEngine
from gsie_api.engines.orchestration.hydration import StationContexteHydrator
from gsie_api.engines.orchestration.schemas import QualificationParRegle
from gsie_api.engines.reasoning.schemas import (  # noqa: TC001
    RegleInference,
    StationContexte,
)
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

SCHEMA_VERSION_PREPARATION: Literal["analyse_preparation.v0.1"] = "analyse_preparation.v0.1"


class PreparationError(ValueError):
    """Erreur nommée empêchant une préparation scientifique."""


class ReglesQualifieesAbsentesError(PreparationError):
    """Aucune règle accepted et qualifiée n'est disponible."""


class QualificationRegleManquanteError(PreparationError):
    """Une règle applicable ne porte pas de qualification complète."""


class EtatGlobalNonSourceError(PreparationError):
    """Aucun état global accepté et sourcé n'est disponible."""


class VersionRegleManquanteError(PreparationError):
    """Une règle sélectionnée ne porte pas de version persistée."""


class EtatGlobalPayload(BaseModel):
    """État explicite fourni par un bundle accepté, jamais déduit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["global_state.v0.1"]
    etat: str = Field(min_length=1, max_length=50)
    justification: str = Field(min_length=1, max_length=1000)
    evidence_level: EvidenceLevel
    observed_at: datetime
    source: SourceReference

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at doit être horodaté avec un fuseau")
        return value.astimezone(UTC)


class RapportPreparation(BaseModel):
    """Preuve immuable de la sélection qui précède l'orchestration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["analyse_preparation.v0.1"] = SCHEMA_VERSION_PREPARATION
    station_id: UUID
    regles_selectionnees: list[str] = Field(default_factory=list)
    regles_ecartees: list[str] = Field(default_factory=list)
    regles_versions: dict[str, int] = Field(default_factory=dict)
    regles_fingerprint: dict[str, str] = Field(default_factory=dict)
    regles_snapshot: list[RegleInference] = Field(default_factory=list)
    qualifications_utilisees: list[QualificationParRegle] = Field(default_factory=list)
    etat_global_field_intake: UUID
    etat_global_snapshot: EtatGlobalDeclare
    etat_global_fingerprint: str = Field(min_length=64, max_length=64)
    contexte_snapshot: StationContexte
    contexte_fingerprint: str = Field(min_length=64, max_length=64)
    causes_blocage: list[str] = Field(default_factory=list)


class ResultatPreparation(BaseModel):
    """Entrées figées prêtes pour le contrat interne d'orchestration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contexte: StationContexte
    rapport: RapportPreparation
    regles: list[RegleInference]
    qualifications: list[QualificationParRegle]
    etat_global: EtatGlobalDeclare
    etat_global_field_intake: UUID


class StationPreparationService:
    """Prépare une analyse avec les seules connaissances admissibles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def prepare(
        self,
        station_id: UUID,
        *,
        niveaux_declares: dict[str, EvidenceLevel] | None = None,
        evidence_min: EvidenceLevel | None = None,
    ) -> ResultatPreparation:
        hydration = await StationContexteHydrator(self._session).hydrate(
            station_id, niveaux_declares=niveaux_declares
        )
        variables = _variables_connues(hydration.contexte)
        knowledge = KnowledgeEngine(self._session)
        regles, ecartees = await knowledge.regles_applicables(
            station_id, variables_connues=variables, evidence_min=evidence_min
        )
        if not regles:
            raise ReglesQualifieesAbsentesError(
                f"AUCUNE_REGLE_QUALIFIEE pour station {station_id} : "
                f"{ecartees or ['aucune règle applicable']}"
            )
        qualifications = await self._qualifications(knowledge, regles)
        versions = await knowledge.versions_regles([r.identifiant for r in regles])
        _require_versions(regles, versions)
        intake = await self._charger_etat_accepte(station_id)
        etat_global = _etat_global(intake)
        rapport = RapportPreparation(
            station_id=station_id,
            regles_selectionnees=[r.identifiant for r in regles],
            regles_ecartees=ecartees,
            regles_versions=versions,
            regles_fingerprint=_fingerprints_regles(regles, qualifications, versions),
            regles_snapshot=regles,
            qualifications_utilisees=qualifications,
            etat_global_field_intake=intake.id,
            etat_global_snapshot=etat_global,
            etat_global_fingerprint=_fingerprint(etat_global),
            contexte_snapshot=hydration.contexte,
            contexte_fingerprint=_fingerprint(hydration.contexte),
        )
        return ResultatPreparation(
            contexte=hydration.contexte,
            rapport=rapport,
            regles=regles,
            qualifications=qualifications,
            etat_global=etat_global,
            etat_global_field_intake=intake.id,
        )

    async def _qualifications(
        self, knowledge: KnowledgeEngine, regles: list[RegleInference]
    ) -> list[QualificationParRegle]:
        brutes = await knowledge.qualifications_regles([r.identifiant for r in regles])
        result: list[QualificationParRegle] = []
        for regle in regles:
            try:
                result.append(
                    QualificationParRegle(
                        identifiant_regle=regle.identifiant,
                        **_qualification_fields(brutes[regle.identifiant]),
                    )
                )
            except (KeyError, ValueError) as exc:
                raise QualificationRegleManquanteError(
                    f"QUALIFICATION_REGLE_MANQUANTE pour règle {regle.identifiant}"
                ) from exc
        return result

    async def _charger_etat_accepte(self, station_id: UUID) -> FieldIntakeModel:
        statement = (
            select(FieldIntakeModel)
            .where(
                FieldIntakeModel.target_resource_id == station_id,
                FieldIntakeModel.status == "accepted",
            )
            .order_by(FieldIntakeModel.observed_at.desc(), FieldIntakeModel.id.desc())
        )
        intake = (await self._session.execute(statement)).scalars().first()
        if intake is None:
            raise EtatGlobalNonSourceError(
                f"ETAT_GLOBAL_NON_SOURCE pour station {station_id} : "
                "aucun FieldIntake accepted ne porte un état global"
            )
        try:
            EtatGlobalPayload.model_validate(intake.payload.get("etat_global"))
        except (AttributeError, TypeError, ValueError) as exc:
            raise EtatGlobalNonSourceError(
                f"ETAT_GLOBAL_NON_SOURCE pour FieldIntake {intake.id}"
            ) from exc
        return intake


def _variables_connues(contexte: StationContexte) -> dict[str, str]:
    variables: dict[str, str] = {}
    for bloc in ("geographie", "climat", "pedologie", "botanique", "peuplement"):
        contenu = getattr(contexte, bloc)
        if contenu is None:
            continue
        for nom in contenu.valeurs:
            variables[nom] = f"{bloc}_{nom}"
    return variables


def _qualification_fields(qualificateurs: dict[str, str]) -> dict[str, Any]:
    champs = ("role", "domaine_element", "domaine_risque", "probabilite", "horizon")
    return {cle: qualificateurs[cle] for cle in champs if cle in qualificateurs}


def _etat_global(intake: FieldIntakeModel) -> EtatGlobalDeclare:
    payload = EtatGlobalPayload.model_validate(intake.payload["etat_global"])
    try:
        return EtatGlobalDeclare(
            etat=payload.etat,
            justification=payload.justification,
            source=payload.source,
            evidence_level=payload.evidence_level,
        )
    except ValueError as exc:
        raise EtatGlobalNonSourceError(
            f"ETAT_GLOBAL_NON_SOURCE pour FieldIntake {intake.id}"
        ) from exc


def _require_versions(regles: list[RegleInference], versions: dict[str, int]) -> None:
    attendues = {regle.identifiant for regle in regles}
    manquantes = sorted(attendues - versions.keys())
    if manquantes:
        raise VersionRegleManquanteError(
            f"VERSION_REGLE_MANQUANTE pour règles : {', '.join(manquantes)}"
        )


def _fingerprints_regles(
    regles: list[RegleInference],
    qualifications: list[QualificationParRegle],
    versions: dict[str, int],
) -> dict[str, str]:
    qualifications_par_regle = {
        qualification.identifiant_regle: qualification for qualification in qualifications
    }
    return {
        regle.identifiant: _fingerprint(
            {
                "regle": regle.model_dump(mode="json"),
                "qualification": qualifications_par_regle[regle.identifiant].model_dump(
                    mode="json"
                ),
                "version": versions[regle.identifiant],
            }
        )
        for regle in regles
    }


def _fingerprint(value: BaseModel | dict[str, Any]) -> str:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "EtatGlobalNonSourceError",
    "QualificationRegleManquanteError",
    "RapportPreparation",
    "ReglesQualifieesAbsentesError",
    "ResultatPreparation",
    "StationPreparationService",
    "VersionRegleManquanteError",
]
