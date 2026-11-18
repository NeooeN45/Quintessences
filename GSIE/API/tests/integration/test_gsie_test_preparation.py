"""Preuve PostgreSQL/PostGIS du flux Forge bundle → préparation GSIE."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.data.gsie_test_bundle import (
    GsiePreparationBundle,
    GsieTestBundleImporter,
    GsieTestBundleImportError,
)
from gsie_api.engines.orchestration.preparation import StationPreparationService
from gsie_api.infrastructure.models.field_intake import FieldIntakeModel
from gsie_api.infrastructure.models.prov import CitationModel, SourceModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_NOW = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
_SOURCE = {
    "type_source": "referentiel_officiel",
    "auteur": "INRAE",
    "date_publication": "2025-01-01",
    "reference": "https://example.org/source",
}


def _bundle() -> GsiePreparationBundle:
    return GsiePreparationBundle.model_validate(
        {
            "schema_version": "gsie_test_preparation.v0.1",
            "bundle_id": str(uuid4()),
            "station_id": str(uuid4()),
            "submitted_by": str(uuid4()),
            "generated_at": _NOW.isoformat(),
            "place": {
                "label": "Station GSIE TEST",
                "srid": 2154,
                "geometry_wkt": "POINT (400000 6500000)",
                "source": _SOURCE,
            },
            "observations": [
                {
                    "observation_type": "pH",
                    "value": 5.2,
                    "unit": "pH",
                    "method_id": "forge-test-ph",
                    "method_version": "1.0",
                    "observed_at": _NOW.isoformat(),
                }
            ],
            "rules": [
                {
                    "connaissance_id": str(uuid4()),
                    "type": "regle",
                    "titre": "Acidité du sol",
                    "description": "Règle accepted issue du bundle Forge",
                    "domaine_scientifique": "pedologie",
                    "contenu_normalise": {"variable": "pH", "operateur": "<", "valeur": "5.5"},
                    "evidence_level": "B",
                    "source": _SOURCE,
                    "statut": "accepted",
                    "qualificateurs": {
                        "variable": "pH",
                        "operateur": "<",
                        "valeur": "5.5",
                        "enonce_conclusion": "Le sol est acide.",
                        "niveau_confiance": "0.8",
                        "role": "contrainte",
                        "domaine_element": "pedologique",
                    },
                    "domaines_validite": [{"parametre": "station", "minimum": 0}],
                }
            ],
            "etat_global": {
                "schema_version": "global_state.v0.1",
                "etat": "vigueur_reduite",
                "justification": "Déficit hydrique observé.",
                "evidence_level": "B",
                "observed_at": _NOW.isoformat(),
                "source": _SOURCE,
            },
        }
    )


async def should_prepare_rules_and_sourced_state_in_real_test_db(
    db_session: AsyncSession,
) -> None:
    bundle = _bundle()
    importer = GsieTestBundleImporter(db_session, database_role="test")
    await importer.import_bundle(bundle)
    await db_session.commit()

    citation = (
        await db_session.execute(
            select(CitationModel).where(CitationModel.target_id == bundle.rules[0].connaissance_id)
        )
    ).scalar_one()
    source = await db_session.get(SourceModel, citation.source_id)
    assert source is not None
    assert source.title == _SOURCE["reference"]
    intake = (
        await db_session.execute(
            select(FieldIntakeModel).where(
                FieldIntakeModel.application_key == "forge-gsie-test",
                FieldIntakeModel.client_event_id == str(bundle.bundle_id),
            )
        )
    ).scalar_one()
    assert len(intake.payload_hash) == 64
    assert len(str(intake.provenance["bundle_hash"])) == 64

    with pytest.raises(GsieTestBundleImportError, match="déjà présente"):
        await importer.import_bundle(bundle)

    prepared = await StationPreparationService(db_session).prepare(
        bundle.station_id, niveaux_declares={"pedologie": "B"}
    )

    assert prepared.rapport.regles_selectionnees
    assert prepared.rapport.etat_global_field_intake == prepared.etat_global_field_intake
    assert prepared.etat_global.justification == "Déficit hydrique observé."
    assert prepared.etat_global.source.reference == _SOURCE["reference"]
    assert prepared.etat_global.source.auteur == _SOURCE["auteur"]
