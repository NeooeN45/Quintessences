"""Tests du contrat d'import Forge → GSIE TEST."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from gsie_api.data.gsie_test_bundle import (
    GsiePreparationBundle,
    GsieTestBundleImporter,
    GsieTestBundleImportError,
)

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
                "label": "Station test",
                "srid": 2154,
                "geometry_wkt": "POINT (400000 6500000)",
                "source": _SOURCE,
            },
            "observations": [
                {
                    "observation_type": "pH",
                    "value": 5.2,
                    "unit": "pH",
                    "method_id": "terrain-ph",
                    "method_version": "1.0",
                    "observed_at": _NOW.isoformat(),
                }
            ],
            "rules": [
                {
                    "connaissance_id": str(uuid4()),
                    "type": "regle",
                    "titre": "Acidité du sol",
                    "description": "Règle de test",
                    "domaine_scientifique": "pedologie",
                    "contenu_normalise": {"variable": "pH"},
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
                    "domaines_validite": [{"parametre": "station"}],
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


async def should_refuse_bundle_import_outside_test_database() -> None:
    importer = GsieTestBundleImporter(None, database_role="development")  # type: ignore[arg-type]

    with pytest.raises(GsieTestBundleImportError, match="database_role"):
        await importer.import_bundle(_bundle())


def should_reject_invalid_geometry() -> None:
    payload = _bundle().model_dump(mode="json")
    payload["place"]["geometry_wkt"] = "POINT ("

    with pytest.raises(ValueError, match="WKT valide"):
        GsiePreparationBundle.model_validate(payload)


def should_reject_unsupported_srid() -> None:
    payload = _bundle().model_dump(mode="json")
    payload["place"]["srid"] = 4326

    with pytest.raises(ValueError, match="SRID non supporté"):
        GsiePreparationBundle.model_validate(payload)


def should_reject_missing_rule_derivation_qualifier() -> None:
    payload = _bundle().model_dump(mode="json")
    del payload["rules"][0]["qualificateurs"]["variable"]

    with pytest.raises(ValueError, match="qualificateur"):
        GsiePreparationBundle.model_validate(payload)
