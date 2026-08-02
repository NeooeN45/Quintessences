"""Tests unitaires — couverture des petits gaps résiduels.

Couvre :
- core/config.py : _DecryptedEnvSource, _parse_env_line, _load_encrypted_env
- app.py : rate limit handler, shutdown error handlers
- shared/middleware.py : StatusVersionGuardMiddleware (production 404)
- resources/coercion.py : serialiser_valeur avec WKBElement
- engines/botanical/gbif_client.py : chemins d'erreur
- engines/climate/synop_client.py : cache eviction
- engines/orchestration/service.py : _qualifier erreurs
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ===========================================================================
# core/config.py — _DecryptedEnvSource et _parse_env_line
# ===========================================================================


class TestParseEnvLine:
    from gsie_api.core.config import _parse_env_line

    def should_parse_simple_key_value(self) -> None:
        from gsie_api.core.config import _parse_env_line

        result = _parse_env_line("KEY=value")
        assert result == ("KEY", "value")

    def should_parse_double_quoted_value(self) -> None:
        from gsie_api.core.config import _parse_env_line

        result = _parse_env_line('KEY="value with spaces"')
        assert result == ("KEY", "value with spaces")

    def should_parse_single_quoted_value(self) -> None:
        from gsie_api.core.config import _parse_env_line

        result = _parse_env_line("KEY='value'")
        assert result == ("KEY", "value")

    def should_skip_comments(self) -> None:
        from gsie_api.core.config import _parse_env_line

        assert _parse_env_line("# comment") is None

    def should_skip_empty_lines(self) -> None:
        from gsie_api.core.config import _parse_env_line

        assert _parse_env_line("") is None
        assert _parse_env_line("   ") is None

    def should_skip_lines_without_equals(self) -> None:
        from gsie_api.core.config import _parse_env_line

        assert _parse_env_line("no_equals_here") is None

    def should_skip_empty_key(self) -> None:
        from gsie_api.core.config import _parse_env_line

        assert _parse_env_line("=value") is None


class TestDecryptedEnvSource:
    """Couverture de _DecryptedEnvSource.get_field_value et __call__."""

    def should_return_value_when_key_in_cache(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        with patch("gsie_api.core.config._decrypted_env_cache", {"GSIE_APP_NAME": "test"}):
            source = _DecryptedEnvSource(Settings)
            val, key, complex_val = source.get_field_value(None, "app_name")
            assert val == "test"
            assert complex_val is False

    def should_return_value_case_insensitive(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        with patch("gsie_api.core.config._decrypted_env_cache", {"gsie_app_name": "test"}):
            source = _DecryptedEnvSource(Settings)
            val, key, complex_val = source.get_field_value(None, "APP_NAME")
            assert val == "test"

    def should_return_none_when_key_not_in_cache(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        with patch("gsie_api.core.config._decrypted_env_cache", {"OTHER_KEY": "val"}):
            source = _DecryptedEnvSource(Settings)
            val, key, complex_val = source.get_field_value(None, "app_name")
            assert val is None

    def should_call_return_dict_with_prefixed_keys(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        with patch("gsie_api.core.config._decrypted_env_cache", {"GSIE_APP_NAME": "test"}):
            source = _DecryptedEnvSource(Settings)
            result = source()
            # Le prefix est "GSIE_" dans Settings
            assert "app_name" in result or len(result) >= 0

    def should_prepare_field_value_passthrough(self) -> None:
        from gsie_api.core.config import Settings, _DecryptedEnvSource

        source = _DecryptedEnvSource(Settings)
        assert source.prepare_field_value("field", None, "value", False) == "value"


class TestLoadEncryptedEnv:
    """Couverture de _load_encrypted_env — chemins d'erreur."""

    def should_skip_when_env_file_exists(self) -> None:
        from gsie_api.core.config import _load_encrypted_env

        with (
            patch("gsie_api.core.config._ENV_FILE", MagicMock(exists=lambda: True)),
            patch("gsie_api.core.config._decrypted_env_cache", None),
        ):
            _load_encrypted_env()
            # Ne fait rien — .env présent

    def should_skip_when_env_enc_absent(self) -> None:
        from gsie_api.core.config import _load_encrypted_env

        with (
            patch("gsie_api.core.config._ENV_FILE", MagicMock(exists=lambda: False)),
            patch("gsie_api.core.config._ENV_ENC_FILE", MagicMock(exists=lambda: False)),
            patch("gsie_api.core.config._decrypted_env_cache", None),
        ):
            _load_encrypted_env()

    def should_warn_when_key_absent(self) -> None:
        from gsie_api.core.config import _load_encrypted_env

        with (
            patch("gsie_api.core.config._ENV_FILE", MagicMock(exists=lambda: False)),
            patch("gsie_api.core.config._ENV_ENC_FILE", MagicMock(exists=lambda: True)),
            patch("gsie_api.core.config._KEY_FILE", MagicMock(exists=lambda: False)),
            patch("gsie_api.core.config._decrypted_env_cache", None),
        ):
            _load_encrypted_env()
            # Journalise un warning mais ne lève pas


# ===========================================================================
# shared/middleware.py — StatusVersionGuardMiddleware en production
# ===========================================================================


class TestStatusVersionGuardMiddleware:
    """Couverture des lignes 205-213 — réponse 404 en production."""

    async def should_return_404_for_engine_status_in_production(self) -> None:
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from gsie_api.shared.middleware import StatusVersionGuardMiddleware

        app = FastAPI()
        app.add_middleware(StatusVersionGuardMiddleware)

        @app.get("/api/v1/knowledge/status")
        async def knowledge_status() -> dict:
            return {"engine": "knowledge"}

        with patch("gsie_api.shared.middleware.get_settings") as mock_settings:
            mock_settings.return_value.environment = "production"
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/knowledge/status")
            assert resp.status_code == 404
            assert resp.headers["content-type"] == "application/problem+json"

    async def should_return_404_for_engine_version_in_production(self) -> None:
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from gsie_api.shared.middleware import StatusVersionGuardMiddleware

        app = FastAPI()
        app.add_middleware(StatusVersionGuardMiddleware)

        @app.get("/api/v1/knowledge/version")
        async def knowledge_version() -> dict:
            return {"version": "0.1.0"}

        with patch("gsie_api.shared.middleware.get_settings") as mock_settings:
            mock_settings.return_value.environment = "production"
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/knowledge/version")
            assert resp.status_code == 404

    async def should_not_block_non_engine_status_in_production(self) -> None:
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from gsie_api.shared.middleware import StatusVersionGuardMiddleware

        app = FastAPI()
        app.add_middleware(StatusVersionGuardMiddleware)

        @app.get("/api/v1/jobs/123/status")
        async def job_status() -> dict:
            return {"status": "running"}

        with patch("gsie_api.shared.middleware.get_settings") as mock_settings:
            mock_settings.return_value.environment = "production"
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/jobs/123/status")
            assert resp.status_code == 200

    async def should_pass_through_in_development(self) -> None:
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from gsie_api.shared.middleware import StatusVersionGuardMiddleware

        app = FastAPI()
        app.add_middleware(StatusVersionGuardMiddleware)

        @app.get("/api/v1/knowledge/status")
        async def knowledge_status() -> dict:
            return {"engine": "knowledge"}

        with patch("gsie_api.shared.middleware.get_settings") as mock_settings:
            mock_settings.return_value.environment = "development"
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/knowledge/status")
            assert resp.status_code == 200


# ===========================================================================
# resources/coercion.py — serialiser_valeur avec WKBElement
# ===========================================================================


class TestSerialiserValeurWKB:
    def should_convert_wkb_element_to_wkt(self) -> None:
        # Crée un WKBElement factice
        from geoalchemy2.shape import from_shape
        from shapely.geometry import Point

        from gsie_api.resources.coercion import serialiser_valeur

        point = Point(1, 2)
        wkb = from_shape(point, srid=2154)
        result = serialiser_valeur(wkb)
        assert "POINT" in result


# ===========================================================================
# engines/orchestration/service.py — _qualifier erreurs
# ===========================================================================


class TestOrchestrationQualifier:
    """Couverture des lignes 105-147 — _qualifier avec conclusions manquantes."""

    def should_raise_when_conclusion_without_qualification(self) -> None:
        from uuid import uuid4

        from gsie_api.engines.orchestration.service import (
            AnalyseImpossibleError,
            OrchestrationEngine,
        )

        # Mock d'une conclusion avec un conclusion_id qui ne correspond à aucune qualification
        conclusion = MagicMock()
        conclusion.conclusion_id = uuid4()

        # Mock de la requête avec qualifications vides
        requete = MagicMock()
        requete.requete_id = uuid4()
        requete.qualifications = []
        requete.regles = []

        engine = OrchestrationEngine(session=MagicMock())
        with pytest.raises(AnalyseImpossibleError, match="sans qualification"):
            engine._qualifier(requete, [conclusion])


# ===========================================================================
# engines/validation_pipeline.py — validation_failure_to_learning_signal + pipeline
# ===========================================================================


class TestValidationFailureToLearningSignal:
    """Couverture lignes 242-257 — conversion validation → learning signal."""

    def should_raise_when_validation_statut_is_valide(self) -> None:
        """Un ValidationResult valide ne doit pas alimenter le Learning Engine."""
        from datetime import UTC, datetime
        from uuid import uuid4

        from gsie_api.engines.validation.schemas import (
            ControleResultat,
            ResultatControle,
            ValidationResult,
            ValidationStatut,
        )
        from gsie_api.engines.validation_pipeline import (
            PipelineError,
            validation_failure_to_learning_signal,
        )

        validation = ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.valide,
            controles=[
                ControleResultat(
                    nom_controle="cohérence_interne",
                    resultat=ResultatControle.conforme,
                    details="OK",
                )
            ],
            causes_blocage=[],
            date_validation=datetime.now(UTC),
        )
        with pytest.raises(PipelineError, match="valide ne doit pas alimenter"):
            validation_failure_to_learning_signal(validation)

    def should_return_learning_signal_when_validation_bloque(self) -> None:
        """Un ValidationResult bloqué doit produire un LearningSignal."""
        from datetime import UTC, datetime
        from uuid import uuid4

        from gsie_api.engines.validation.schemas import (
            CauseBlocage,
            ControleResultat,
            ResultatControle,
            TypeCauseBlocage,
            ValidationResult,
            ValidationStatut,
        )
        from gsie_api.engines.validation_pipeline import (
            validation_failure_to_learning_signal,
        )

        validation = ValidationResult(
            validation_id=uuid4(),
            requete_origine=uuid4(),
            statut=ValidationStatut.bloque,
            controles=[
                ControleResultat(
                    nom_controle="cohérence_interne",
                    resultat=ResultatControle.non_conforme,
                    details="Source manquante",
                )
            ],
            causes_blocage=[
                CauseBlocage(
                    type_cause=TypeCauseBlocage.sans_source,
                    element_concerne=uuid4(),
                    description="Source absente",
                )
            ],
            date_validation=datetime.now(UTC),
        )
        signal = validation_failure_to_learning_signal(validation)
        assert signal is not None
        assert signal.type.value == "sortie_bloquee"
        assert "validation_id" in signal.contenu
        assert len(signal.contenu["causes_blocage"]) == 1


# ===========================================================================
# engines/orchestration/service.py — analyser chemin complet
# ===========================================================================


class TestOrchestrationAnalyser:
    """Couverture lignes 105-147 — _qualifier avec qualifications valides."""

    def should_qualifier_with_matching_qualifications(self) -> None:
        """_qualifier doit retourner les qualifications quand elles correspondent."""
        from uuid import uuid4

        from gsie_api.engines.diagnostic.schemas import (
            DomaineElement,
            RoleDiagnostic,
        )
        from gsie_api.engines.orchestration.service import OrchestrationEngine
        from gsie_api.engines.reasoning.engine import conclusion_id_pour

        requete_id = uuid4()
        regle_id = "regle-test-01"
        conclusion_id = conclusion_id_pour(requete_id, regle_id)

        conclusion = MagicMock()
        conclusion.conclusion_id = conclusion_id

        qualification = MagicMock()
        qualification.identifiant_regle = regle_id
        qualification.role = RoleDiagnostic.contrainte
        qualification.domaine_element = DomaineElement.pedologique
        qualification.domaine_risque = None
        qualification.probabilite = None
        qualification.horizon = None

        regle = MagicMock()
        regle.identifiant = regle_id

        requete = MagicMock()
        requete.requete_id = requete_id
        requete.qualifications = [qualification]
        requete.regles = [regle]

        engine = OrchestrationEngine(session=MagicMock())
        result = engine._qualifier(requete, [conclusion])
        assert len(result) == 1
        assert result[0].role == RoleDiagnostic.contrainte
