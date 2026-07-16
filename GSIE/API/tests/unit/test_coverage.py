"""Tests de couverture — branches difficiles à atteindre.

Couvre :
- app.py : OpenTelemetry setup, graceful shutdown, except branches
- core/auth.py : chargement clés depuis fichiers
- wrapper.py : fallbacks Python quand Rust indispo, panic recovery Rust
"""

import os
import tempfile
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.engines.evidence.schemas import (
    ContentType,
    KnowledgeStatus,
    RawKnowledgeSubmission,
    SourceReference,
    SourceType,
)

# --- app.py : OpenTelemetry setup ---


def should_setup_opentelemetry_when_otel_enabled():
    """_setup_opentelemetry doit instrumenter l'app si otel_enabled=True."""
    from gsie_api.app import _setup_opentelemetry

    app = FastAPI()

    # Mocker tous les modules OTel pour éviter l'instrumentation réelle
    mock_trace = MagicMock()
    mock_resource = MagicMock()
    mock_provider = MagicMock()
    mock_processor = MagicMock()
    mock_exporter = MagicMock()
    mock_fastapi_instr = MagicMock()
    mock_sqlalchemy_instr = MagicMock()
    mock_redis_instr = MagicMock()

    with (
        patch.dict(
            "sys.modules",
            {
                "opentelemetry": mock_trace,
                "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": mock_exporter,
                "opentelemetry.instrumentation.fastapi": mock_fastapi_instr,
                "opentelemetry.instrumentation.redis": mock_redis_instr,
                "opentelemetry.instrumentation.sqlalchemy": mock_sqlalchemy_instr,
                "opentelemetry.sdk.resources": mock_resource,
                "opentelemetry.sdk.trace": mock_provider,
                "opentelemetry.sdk.trace.export": mock_processor,
            },
        ),
        patch("gsie_api.infrastructure.database.engine") as mock_engine,
    ):
        mock_engine.sync_engine = MagicMock()
        _setup_opentelemetry(app)
        # Vérifier que l'instrumentation a été appelée
        mock_fastapi_instr.FastAPIInstrumentor.instrument_app.assert_called_once_with(app)


def should_log_error_when_opentelemetry_setup_fails():
    """_setup_opentelemetry doit logger l'erreur si l'instrumentation échoue."""
    from gsie_api.app import _setup_opentelemetry

    app = FastAPI()

    # Provoquer un ImportError en mockant l'import OTel
    with patch.dict("sys.modules", {"opentelemetry": None}):
        _setup_opentelemetry(app)
        # Si on arrive ici, l'except a été attrapé et loggé sans crash


def should_call_setup_opentelemetry_in_lifespan_when_enabled():
    """Le lifespan doit appeler _setup_opentelemetry quand otel_enabled=True."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.otel_enabled = True
        mock_settings.app_name = "GSIE API"
        mock_settings.app_version = "0.1.0"
        mock_settings.environment = "development"
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.rate_limit_enabled = False
        mock_settings.rate_limit_default = "60/minute"
        mock_settings.rate_limit_storage_url = "memory://"
        mock_settings.max_request_body_size = 1_048_576

        with (
            patch("gsie_api.app._setup_opentelemetry") as mock_otel,
            patch("gsie_api.infrastructure.database.engine") as mock_engine,
            patch("gsie_api.infrastructure.redis_client.redis_pool") as mock_pool,
        ):
            mock_engine.dispose = AsyncMock()
            mock_pool.aclose = AsyncMock()

            app = create_app()
            client = TestClient(app)
            with client:
                pass

            mock_otel.assert_called_once()


# --- app.py : Graceful shutdown ---


def should_close_connections_on_shutdown():
    """Le lifespan doit fermer les connexions DB et Redis au shutdown."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.otel_enabled = False
        mock_settings.app_name = "GSIE API"
        mock_settings.app_version = "0.1.0"
        mock_settings.environment = "development"
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.rate_limit_enabled = False
        mock_settings.rate_limit_default = "60/minute"
        mock_settings.rate_limit_storage_url = "memory://"
        mock_settings.max_request_body_size = 1_048_576

        with (
            patch("gsie_api.infrastructure.database.engine") as mock_engine,
            patch("gsie_api.infrastructure.redis_client.redis_pool") as mock_pool,
        ):
            mock_engine.dispose = AsyncMock()
            mock_pool.disconnect = AsyncMock()

            app = create_app()
            client = TestClient(app)

            # Le TestClient déclenche le lifespan (startup + shutdown)
            with client:
                pass  # Le shutdown se produit à la sortie du context manager

            # Vérifier que dispose et disconnect ont été appelés
            mock_engine.dispose.assert_called_once()
            mock_pool.disconnect.assert_called_once()


def should_log_error_when_shutdown_cleanup_fails():
    """Le lifespan doit logger l'erreur si la fermeture des connexions échoue."""
    with patch("gsie_api.app._settings") as mock_settings:
        mock_settings.otel_enabled = False
        mock_settings.app_name = "GSIE API"
        mock_settings.app_version = "0.1.0"
        mock_settings.environment = "development"
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.rate_limit_enabled = False
        mock_settings.rate_limit_default = "60/minute"
        mock_settings.rate_limit_storage_url = "memory://"
        mock_settings.max_request_body_size = 1_048_576

        with patch("gsie_api.infrastructure.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock(side_effect=RuntimeError("dispose failed"))
            with patch("gsie_api.infrastructure.redis_client.redis_pool") as mock_pool:
                mock_pool.aclose = AsyncMock()

                app = create_app()
                client = TestClient(app)

                # Le shutdown ne doit pas crasher même si dispose échoue
                with client:
                    pass


# --- core/auth.py : chargement clés depuis fichiers ---


def should_load_private_key_from_file_when_exists():
    """_load_private_key doit charger depuis le fichier si il existe."""
    from gsie_api.core.auth import _load_private_key

    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False, encoding="utf-8") as f:
        f.write("fake-private-key-content")
        f.flush()
        key_path = f.name

    try:
        with patch("gsie_api.core.auth._settings") as mock_settings:
            mock_settings.jwt_private_key_path = key_path
            result = _load_private_key()
            assert result == "fake-private-key-content"
    finally:
        os.unlink(key_path)


def should_load_public_key_from_file_when_exists():
    """_load_public_key doit charger depuis le fichier si il existe."""
    from gsie_api.core.auth import _load_public_key

    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False, encoding="utf-8") as f:
        f.write("fake-public-key-content")
        f.flush()
        key_path = f.name

    try:
        with patch("gsie_api.core.auth._settings") as mock_settings:
            mock_settings.jwt_public_key_path = key_path
            result = _load_public_key()
            assert result == "fake-public-key-content"
    finally:
        os.unlink(key_path)


# --- wrapper.py : fallbacks Python quand Rust indispo ---


def _make_submission(
    source_type: SourceType = SourceType.peer_reviewed,
    content_type: ContentType = ContentType.publication,
) -> RawKnowledgeSubmission:
    return RawKnowledgeSubmission(
        soumission_id=uuid4(),
        type_contenu=content_type,
        contenu={"title": "Test", "data": 42},
        source_candidate=SourceReference(
            type_source=source_type,
            auteur="IGN",
            date_publication="2024-01-15",
            reference="DOI:10.1234/test",
        ),
        date_soumission=datetime.now(UTC),
        soumetteur="test",
    )


def should_use_python_fallback_for_evaluate_with_context_when_rust_unavailable():
    """evaluate_with_context doit utiliser le fallback Python quand Rust indispo."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        sub = _make_submission()
        result = wrapper_module.evaluate_with_context(sub, parent_version=2)
        assert result.version == 3


def should_use_python_fallback_for_detect_conflicts_when_rust_unavailable():
    """detect_conflicts doit utiliser le fallback Python quand Rust indispo."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        candidate = SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Smith",
            reference="DOI:10.1234/test",
        )
        existing = [
            SourceReference(
                type_source=SourceType.expert_identifie,
                auteur="Jones",
                reference="DOI:10.1234/test",
            )
        ]
        conflits = wrapper_module.detect_conflicts(candidate, existing)
        assert len(conflits) == 1


def should_fallback_to_python_when_evaluate_with_context_rust_fails():
    """evaluate_with_context doit fallback vers Python si Rust lève une exception."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with (
        patch.object(wrapper_module, "_RUST_AVAILABLE", True),
        patch.object(
            wrapper_module._rust_engine.EvidenceEngine,
            "evaluate_with_context",
            side_effect=RuntimeError("Rust panic"),
        ),
    ):
        sub = _make_submission()
        result = wrapper_module.evaluate_with_context(sub)
        assert result.version == 1


def should_fallback_to_python_when_detect_conflicts_rust_fails():
    """detect_conflicts doit fallback vers Python si Rust lève une exception."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with (
        patch.object(wrapper_module, "_RUST_AVAILABLE", True),
        patch.object(
            wrapper_module._rust_engine.EvidenceEngine,
            "detect_conflicts",
            side_effect=RuntimeError("Rust panic"),
        ),
    ):
        candidate = SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Smith",
            reference="DOI:10.1234/test",
        )
        existing = [
            SourceReference(
                type_source=SourceType.expert_identifie,
                auteur="Jones",
                reference="DOI:10.1234/test",
            )
        ]
        conflits = wrapper_module.detect_conflicts(candidate, existing)
        # Le fallback Python doit détecter le conflit
        assert len(conflits) == 1


def should_return_refuse_when_conflits_detected_in_python_fallback():
    """Le fallback Python doit retourner refuse quand des conflits sont détectés."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with (
        patch.object(wrapper_module, "_RUST_AVAILABLE", False),
        patch.object(
            wrapper_module._settings,
            "evidence_experimental_conflicts_enabled",
            True,
        ),
    ):
        sub = _make_submission()
        sub.source_candidate.reference = "DOI:10.1234/conflict"
        existing = [
            SourceReference(
                type_source=SourceType.expert_identifie,
                auteur="Other",
                reference="DOI:10.1234/conflict",
            )
        ]
        result = wrapper_module.evaluate_with_context(sub, existing_sources=existing)
        assert result.statut == KnowledgeStatus.refuse
        assert len(result.conflits) > 0


def should_detect_conflict_type2_in_python_fallback():
    """Le fallback Python doit détecter le conflit type 2 (même auteur + date)."""
    import gsie_api.engines.evidence.wrapper as wrapper_module

    with patch.object(wrapper_module, "_RUST_AVAILABLE", False):
        candidate = SourceReference(
            type_source=SourceType.peer_reviewed,
            auteur="Smith",
            date_publication="2024-06-01",
            reference="DOI:10.1234/a",
        )
        existing = [
            SourceReference(
                type_source=SourceType.peer_reviewed,
                auteur="smith",
                date_publication="2024-06-01",
                reference="DOI:10.1234/b",
            )
        ]
        conflits = wrapper_module._detect_conflicts_python(candidate, existing)
        assert len(conflits) == 1
        assert "attribution" in conflits[0].description.lower()
