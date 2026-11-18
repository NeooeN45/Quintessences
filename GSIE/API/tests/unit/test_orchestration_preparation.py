"""Contrat fail-closed de préparation d'une analyse stationnelle."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from gsie_api.engines.diagnostic.schemas import EtatGlobal
from gsie_api.engines.evidence.schemas import EvidenceLevel, SourceReference, SourceType
from gsie_api.engines.orchestration.hydration import (
    RapportHydratation,
    ResultatHydratation,
)
from gsie_api.engines.orchestration.preparation import (
    EtatGlobalNonSourceError,
    ReglesQualifieesAbsentesError,
    StationPreparationService,
    VersionRegleManquanteError,
)
from gsie_api.engines.reasoning.schemas import (
    BlocContexte,
    RegleInference,
    SourceMoteurContexte,
    StationContexte,
)
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel

_NOW = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
_SOURCE = SourceReference(
    type_source=SourceType.observation_terrain,
    auteur="Forge",
    date_publication="2026-08-18",
    reference="forge://gsie-test/rule-1",
)


def _hydration(station_id):
    contexte = StationContexte(
        pedologie=BlocContexte(
            source_moteur=SourceMoteurContexte.terrain,
            source=_SOURCE,
            evidence_level=EvidenceLevel.B,
            valeurs={"pH": 5.2},
            date_observation=_NOW,
        )
    )
    rapport = RapportHydratation(
        station_id=station_id,
        blocs_construits=["pedologie"],
        niveaux_declares_utilises=["pedologie"],
    )
    return ResultatHydratation(contexte=contexte, rapport=rapport)


def _rule() -> RegleInference:
    return RegleInference(
        identifiant="rule-1",
        condition="pedologie_pH < 5.5",
        enonce_conclusion="Le sol est acide.",
        source=_SOURCE,
        evidence_level=EvidenceLevel.B,
        niveau_confiance=0.8,
    )


def _accepted_intake(station_id):
    return FieldIntakeModel(
        id=uuid4(),
        submitted_by=uuid4(),
        application_key="forge-gsie-test",
        client_event_id="state-1",
        kind="observation",
        observed_at=_NOW,
        status="accepted",
        payload={
            "etat_global": {
                "schema_version": "global_state.v0.1",
                "etat": "vigueur_reduite",
                "justification": "Déficit hydrique observé sur la station.",
                "evidence_level": "B",
                "observed_at": _NOW.isoformat(),
                "source": _SOURCE.model_dump(mode="json"),
            }
        },
        provenance={"source": "Forge"},
        payload_hash="a" * 64,
        target_resource_id=station_id,
    )


class _ResultatScalars:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


@pytest.mark.asyncio
async def should_return_preparation_with_rules_and_sourced_state() -> None:
    station_id = uuid4()
    session = AsyncMock()
    session.execute.return_value = _ResultatScalars(_accepted_intake(station_id))
    service = StationPreparationService(session)

    with (
        patch(
            "gsie_api.engines.orchestration.preparation.StationContexteHydrator.hydrate",
            new=AsyncMock(return_value=_hydration(station_id)),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.regles_applicables",
            new=AsyncMock(return_value=([_rule()], ["discarded-rule"])),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.qualifications_regles",
            new=AsyncMock(
                return_value={"rule-1": {"role": "contrainte", "domaine_element": "pedologique"}}
            ),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.versions_regles",
            new=AsyncMock(return_value={"rule-1": 1}),
        ),
    ):
        result = await service.prepare(station_id)

    assert result.regles == [_rule()]
    assert result.rapport.regles_ecartees == ["discarded-rule"]
    assert result.etat_global.etat == EtatGlobal.vigueur_reduite
    assert result.rapport.etat_global_field_intake == result.etat_global_field_intake
    assert result.rapport.contexte_snapshot == result.contexte
    assert result.rapport.regles_snapshot == result.regles
    assert result.rapport.etat_global_snapshot == result.etat_global
    assert result.rapport.regles_versions == {"rule-1": 1}
    assert len(result.rapport.regles_fingerprint["rule-1"]) == 64
    assert len(result.rapport.etat_global_fingerprint) == 64


@pytest.mark.asyncio
async def should_refuse_when_no_qualified_rule_exists() -> None:
    station_id = uuid4()
    session = AsyncMock()
    service = StationPreparationService(session)

    with (
        patch(
            "gsie_api.engines.orchestration.preparation.StationContexteHydrator.hydrate",
            new=AsyncMock(return_value=_hydration(station_id)),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.regles_applicables",
            new=AsyncMock(return_value=([], ["rule-1 : qualification absente"])),
        ),
        pytest.raises(ReglesQualifieesAbsentesError, match="AUCUNE_REGLE_QUALIFIEE"),
    ):
        await service.prepare(station_id)


@pytest.mark.asyncio
async def should_refuse_when_rule_version_is_missing() -> None:
    station_id = uuid4()
    session = AsyncMock()
    service = StationPreparationService(session)

    with (
        patch(
            "gsie_api.engines.orchestration.preparation.StationContexteHydrator.hydrate",
            new=AsyncMock(return_value=_hydration(station_id)),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.regles_applicables",
            new=AsyncMock(return_value=([_rule()], [])),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.qualifications_regles",
            new=AsyncMock(
                return_value={"rule-1": {"role": "contrainte", "domaine_element": "pedologique"}}
            ),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.versions_regles",
            new=AsyncMock(return_value={}),
        ),
        pytest.raises(VersionRegleManquanteError, match="VERSION_REGLE_MANQUANTE"),
    ):
        await service.prepare(station_id)


@pytest.mark.asyncio
async def should_refuse_when_global_state_has_no_accepted_source() -> None:
    station_id = uuid4()
    session = AsyncMock()
    session.execute.return_value = _ResultatScalars(None)
    service = StationPreparationService(session)

    with (
        patch(
            "gsie_api.engines.orchestration.preparation.StationContexteHydrator.hydrate",
            new=AsyncMock(return_value=_hydration(station_id)),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.regles_applicables",
            new=AsyncMock(return_value=([_rule()], [])),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.qualifications_regles",
            new=AsyncMock(
                return_value={"rule-1": {"role": "contrainte", "domaine_element": "pedologique"}}
            ),
        ),
        patch(
            "gsie_api.engines.orchestration.preparation.KnowledgeEngine.versions_regles",
            new=AsyncMock(return_value={"rule-1": 1}),
        ),
        pytest.raises(EtatGlobalNonSourceError, match="ETAT_GLOBAL_NON_SOURCE"),
    ):
        await service.prepare(station_id)
