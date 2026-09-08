"""Tests unitaires — couverture des routers engine manquants.

Complète test_routers_coverage.py pour les routers :
- learning/router.py       — /status, /version, /process
- recommendation/router.py — /status, /version, /recommend, /decision
- simulation/router.py     — /status, /version, /run
- validation/router.py     — /status, /version, /validate
- correlation/router.py    — /status, /version, /compute, /stats
- orchestration/router.py  — /status, /version, /analyse

Tests sans Docker — la DB est mockée via dependency_overrides.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.middleware import SlowAPIASGIMiddleware
from slowapi.util import get_remote_address

from gsie_api.core.auth import create_access_token
from gsie_api.engines.correlation.router import router as correlation_router
from gsie_api.engines.learning.router import router as learning_router
from gsie_api.engines.orchestration.router import router as orchestration_router
from gsie_api.engines.reasoning.router import router as reasoning_router
from gsie_api.engines.recommendation.router import router as recommendation_router
from gsie_api.engines.simulation.router import router as simulation_router
from gsie_api.engines.validation.router import router as validation_router
from gsie_api.infrastructure.database import get_db

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

_API_PREFIX = "/api/v1"


def _auth_headers(roles: list[str] | None = None) -> dict[str, str]:
    if roles is None:
        roles = ["reader"]
    token = create_access_token(subject="test-user", claims={"roles": roles})
    return {"Authorization": f"Bearer {token}"}


def _writer_headers() -> dict[str, str]:
    return _auth_headers(roles=["writer"])


def _analyse_payload() -> dict[str, Any]:
    """Requête complète minimale pour tester les gardes HTTP d'orchestration."""
    source = {
        "type_source": "peer_reviewed",
        "auteur": "Test",
        "reference": "DOI",
    }
    return {
        "requete_id": str(uuid4()),
        "station_id": str(uuid4()),
        "contexte": {
            "pedologie": {
                "source_moteur": "PEDOLOGY",
                "source": source,
                "evidence_level": "B",
                "valeurs": {"pH": 5.2},
            }
        },
        "regles": [
            {
                "identifiant": "regle-01",
                "condition": "pedologie_pH < 5.5",
                "enonce_conclusion": "Le sol est acide.",
                "source": source,
                "evidence_level": "B",
                "niveau_confiance": 0.85,
            }
        ],
        "qualifications": [
            {
                "identifiant_regle": "regle-01",
                "role": "contrainte",
                "domaine_element": "pedologique",
            }
        ],
        "etat_global": {
            "etat": "vigueur_reduite",
            "justification": "Acidité",
            "source": source,
            "evidence_level": "B",
        },
        "type_diagnostic": "stationnel",
        "question": "Quelles essences ?",
        "objectif_forestier": "production",
        "alternatives_demandees": True,
    }


def _build_engine_app(router: Any, mock_db: Any = None) -> FastAPI:
    app = FastAPI()
    app.state.limiter = Limiter(key_func=get_remote_address)
    app.add_middleware(SlowAPIASGIMiddleware)
    if mock_db is not None:

        async def _override_get_db() -> AsyncGenerator[Any, None]:
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db
    app.include_router(router, prefix=_API_PREFIX)
    return app


# ===========================================================================
# Learning Router
# ===========================================================================


@pytest.fixture
async def learning_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(learning_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestLearningRouter:
    async def should_return_status_when_called(self, learning_client: AsyncClient) -> None:
        resp = await learning_client.get(f"{_API_PREFIX}/learning/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["engine"] == "learning"
        assert data["status"] == "active"

    async def should_return_version_when_called(self, learning_client: AsyncClient) -> None:
        resp = await learning_client.get(f"{_API_PREFIX}/learning/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert data["backend"] == "python"

    async def should_return_401_when_no_auth_on_process(self, learning_client: AsyncClient) -> None:
        resp = await learning_client.post(
            f"{_API_PREFIX}/learning/process",
            json={
                "signal_id": str(uuid4()),
                "type": "retour_forestier",
                "contenu": {"recommandation_id": str(uuid4()), "decision": "refuse"},
                "date_signal": "2026-08-02T10:00:00Z",
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, learning_client: AsyncClient) -> None:
        from gsie_api.engines.learning.engine import LearningEngineError

        with patch("gsie_api.engines.learning.router.LearningEngine") as mock_engine_cls:
            mock_engine = mock_engine_cls.return_value
            mock_engine.process = AsyncMock(side_effect=LearningEngineError("type inconnu"))
            resp = await learning_client.post(
                f"{_API_PREFIX}/learning/process",
                json={
                    "signal_id": str(uuid4()),
                    "type": "retour_forestier",
                    "contenu": {
                        "recommandation_id": str(uuid4()),
                        "decision": "refuse",
                        "contexte_station": str(uuid4()),
                    },
                    "date_signal": "2026-08-02T10:00:00Z",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "type inconnu" in resp.json()["detail"]

    async def should_return_204_when_signal_accumulated(self, learning_client: AsyncClient) -> None:
        with patch("gsie_api.engines.learning.router.LearningEngine") as mock_engine_cls:
            mock_engine = mock_engine_cls.return_value
            mock_engine.process = AsyncMock(return_value=None)
            resp = await learning_client.post(
                f"{_API_PREFIX}/learning/process",
                json={
                    "signal_id": str(uuid4()),
                    "type": "retour_forestier",
                    "contenu": {
                        "recommandation_id": str(uuid4()),
                        "decision": "accepte",
                        "contexte_station": str(uuid4()),
                    },
                    "date_signal": "2026-08-02T10:00:00Z",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 204


# ===========================================================================
# Recommendation Router
# ===========================================================================


@pytest.fixture
async def recommendation_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(recommendation_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestRecommendationRouter:
    async def should_return_status(self, recommendation_client: AsyncClient) -> None:
        resp = await recommendation_client.get(f"{_API_PREFIX}/recommendation/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "recommendation"

    async def should_return_version(self, recommendation_client: AsyncClient) -> None:
        resp = await recommendation_client.get(f"{_API_PREFIX}/recommendation/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "python"

    async def should_return_401_when_no_auth_on_recommend(
        self, recommendation_client: AsyncClient
    ) -> None:
        resp = await recommendation_client.post(
            f"{_API_PREFIX}/recommendation/recommend",
            json={"requete_id": str(uuid4()), "diagnostic_id": str(uuid4())},
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, recommendation_client: AsyncClient) -> None:
        from gsie_api.engines.recommendation.engine import RecommendationEngineError

        with patch("gsie_api.engines.recommendation.router.RecommendationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.recommend = AsyncMock(
                side_effect=RecommendationEngineError("diagnostic introuvable")
            )
            resp = await recommendation_client.post(
                f"{_API_PREFIX}/recommendation/recommend",
                json={
                    "requete_id": str(uuid4()),
                    "diagnostic_id": str(uuid4()),
                    "objectif_forestier": "production",
                    "alternatives_demandees": True,
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "diagnostic introuvable" in resp.json()["detail"]

    async def should_return_401_when_no_auth_on_decision(
        self, recommendation_client: AsyncClient
    ) -> None:
        resp = await recommendation_client.post(
            f"{_API_PREFIX}/recommendation/decision",
            json={
                "recommandation_id": str(uuid4()),
                "decision": "accepte",
                "motif": "test",
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_decision_error(
        self, recommendation_client: AsyncClient
    ) -> None:
        from gsie_api.engines.recommendation.engine import RecommendationEngineError

        with patch("gsie_api.engines.recommendation.router.RecommendationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.record_decision = AsyncMock(
                side_effect=RecommendationEngineError("recommandation introuvable")
            )
            resp = await recommendation_client.post(
                f"{_API_PREFIX}/recommendation/decision",
                json={
                    "recommandation_id": str(uuid4()),
                    "decision": "accepte",
                    "date_decision": "2026-08-02T10:00:00Z",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "recommandation introuvable" in resp.json()["detail"]


# ===========================================================================
# Simulation Router
# ===========================================================================


@pytest.fixture
async def simulation_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(simulation_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestSimulationRouter:
    async def should_return_status(self, simulation_client: AsyncClient) -> None:
        resp = await simulation_client.get(f"{_API_PREFIX}/simulation/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "simulation"

    async def should_return_version(self, simulation_client: AsyncClient) -> None:
        resp = await simulation_client.get(f"{_API_PREFIX}/simulation/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "python"

    async def should_return_401_when_no_auth_on_run(self, simulation_client: AsyncClient) -> None:
        resp = await simulation_client.post(
            f"{_API_PREFIX}/simulation/run",
            json={
                "scenario_id": str(uuid4()),
                "type_scenario": "intervention",
                "etat_initial": {},
                "intervention": {},
                "horizon_annees": 10,
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, simulation_client: AsyncClient) -> None:
        from gsie_api.engines.simulation.engine import SimulationEngineError

        with patch("gsie_api.engines.simulation.router.SimulationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.simulate = AsyncMock(side_effect=SimulationEngineError("horizon invalide"))
            resp = await simulation_client.post(
                f"{_API_PREFIX}/simulation/run",
                json={
                    "scenario_id": str(uuid4()),
                    "source_diagnostic": str(uuid4()),
                    "intervention": {
                        "type_intervention": "eclaircie",
                        "parametres": {"intensite": 0.3},
                    },
                    "horizon": "10y",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "horizon invalide" in resp.json()["detail"]


# ===========================================================================
# Validation Router
# ===========================================================================


@pytest.fixture
async def validation_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(validation_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestValidationRouter:
    async def should_return_status(self, validation_client: AsyncClient) -> None:
        resp = await validation_client.get(f"{_API_PREFIX}/validation/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "validation"

    async def should_return_version(self, validation_client: AsyncClient) -> None:
        resp = await validation_client.get(f"{_API_PREFIX}/validation/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "python"

    async def should_return_401_when_no_auth_on_validate(
        self, validation_client: AsyncClient
    ) -> None:
        resp = await validation_client.post(
            f"{_API_PREFIX}/validation/validate",
            json={
                "requete_id": str(uuid4()),
                "type_sortie": "diagnostic",
                "contenu": {},
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, validation_client: AsyncClient) -> None:
        from gsie_api.engines.validation.engine import ValidationEngineError

        with patch("gsie_api.engines.validation.router.ValidationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.validate = AsyncMock(side_effect=ValidationEngineError("requête malformée"))
            resp = await validation_client.post(
                f"{_API_PREFIX}/validation/validate",
                json={
                    "requete_id": str(uuid4()),
                    "type_sortie": "diagnostic",
                    "contenu": {
                        "source": {
                            "type_source": "peer_reviewed",
                            "auteur": "Test",
                            "reference": "DOI",
                        },
                        "justification": "Test",
                    },
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "requête malformée" in resp.json()["detail"]


# ===========================================================================
# Correlation Router
# ===========================================================================


@pytest.fixture
async def correlation_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(correlation_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestCorrelationRouter:
    async def should_return_status(self, correlation_client: AsyncClient) -> None:
        resp = await correlation_client.get(f"{_API_PREFIX}/correlation/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "correlation"

    async def should_return_version(self, correlation_client: AsyncClient) -> None:
        resp = await correlation_client.get(f"{_API_PREFIX}/correlation/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "postgresql"

    async def should_return_401_when_no_auth_on_compute(
        self, correlation_client: AsyncClient
    ) -> None:
        resp = await correlation_client.post(
            f"{_API_PREFIX}/correlation/compute",
            json={
                "requete_id": str(uuid4()),
                "domaine": "stationnel",
                "variable_a": {
                    "source_moteur": "CLIMATE",
                    "variable": "temp",
                    "valeurs": [1.0, 2.0, 3.0],
                },
                "variable_b": {
                    "source_moteur": "PEDOLOGY",
                    "variable": "ph",
                    "valeurs": [4.0, 5.0, 6.0],
                },
                "methode": "pearson",
                "source": {"type_source": "peer_reviewed", "auteur": "Test", "reference": "DOI"},
                "evidence_level": "B",
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, correlation_client: AsyncClient) -> None:
        from gsie_api.engines.correlation.engine import CorrelationEngineError

        with patch("gsie_api.engines.correlation.router.CorrelationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.compute = AsyncMock(
                side_effect=CorrelationEngineError("méthode non supportée")
            )
            resp = await correlation_client.post(
                f"{_API_PREFIX}/correlation/compute",
                json={
                    "requete_id": str(uuid4()),
                    "domaine": "stationnel",
                    "variable_a": {
                        "source_moteur": "CLIMATE",
                        "variable": "temp",
                        "valeurs": [1.0, 2.0, 3.0],
                    },
                    "variable_b": {
                        "source_moteur": "PEDOLOGY",
                        "variable": "ph",
                        "valeurs": [4.0, 5.0, 6.0],
                    },
                    "methode": "pearson",
                    "source": {
                        "type_source": "peer_reviewed",
                        "auteur": "Test",
                        "reference": "DOI",
                    },
                    "evidence_level": "B",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "méthode non supportée" in resp.json()["detail"]

    async def should_return_401_when_no_auth_on_stats(
        self, correlation_client: AsyncClient
    ) -> None:
        resp = await correlation_client.get(f"{_API_PREFIX}/correlation/stats")
        assert resp.status_code == 401

    async def should_return_stats_when_authorized(self, correlation_client: AsyncClient) -> None:
        with patch("gsie_api.engines.correlation.router.CorrelationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.stats = AsyncMock(return_value={"pearson": 5, "spearman": 3})
            resp = await correlation_client.get(
                f"{_API_PREFIX}/correlation/stats",
                headers=_auth_headers(roles=["reader"]),
            )
        assert resp.status_code == 200

    async def should_return_400_when_matrix_engine_error(
        self, correlation_client: AsyncClient
    ) -> None:
        """POST /correlation/matrix — CorrelationEngineError retourne 400."""
        from gsie_api.engines.correlation.engine import CorrelationEngineError

        with patch("gsie_api.engines.correlation.router.CorrelationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.compute_matrix = AsyncMock(
                side_effect=CorrelationEngineError("variable constante")
            )
            resp = await correlation_client.post(
                f"{_API_PREFIX}/correlation/matrix",
                json={
                    "requete_id": str(uuid4()),
                    "domaine": "stationnel",
                    "variables": [
                        {
                            "source_moteur": "CLIMATE",
                            "variable": "temp",
                            "valeurs": [1.0, 2.0, 3.0],
                        },
                        {
                            "source_moteur": "PEDOLOGY",
                            "variable": "ph",
                            "valeurs": [4.0, 5.0, 6.0],
                        },
                    ],
                    "methode": "pearson",
                    "source": {
                        "type_source": "peer_reviewed",
                        "auteur": "Test",
                        "reference": "DOI",
                    },
                    "evidence_level": "B",
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "variable constante" in resp.json()["detail"]


# ===========================================================================
# Orchestration Router
# ===========================================================================


@pytest.fixture
async def orchestration_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(orchestration_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestOrchestrationRouter:
    async def should_return_status(self, orchestration_client: AsyncClient) -> None:
        resp = await orchestration_client.get(f"{_API_PREFIX}/orchestration/status")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "orchestration"

    async def should_return_version(self, orchestration_client: AsyncClient) -> None:
        resp = await orchestration_client.get(f"{_API_PREFIX}/orchestration/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "python"

    async def should_return_401_when_no_auth_on_analyse(
        self, orchestration_client: AsyncClient
    ) -> None:
        resp = await orchestration_client.post(
            f"{_API_PREFIX}/orchestration/analyse",
            json={"requete_id": str(uuid4())},
        )
        assert resp.status_code == 401

    async def should_return_400_when_analyse_impossible(
        self, orchestration_client: AsyncClient
    ) -> None:
        from gsie_api.engines.orchestration.service import AnalyseImpossibleError

        with patch("gsie_api.engines.orchestration.router.OrchestrationEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.analyser_idempotente = AsyncMock(
                side_effect=AnalyseImpossibleError("aucune règle applicable")
            )
            resp = await orchestration_client.post(
                f"{_API_PREFIX}/orchestration/analyse",
                json={
                    "requete_id": str(uuid4()),
                    "station_id": str(uuid4()),
                    "contexte": {
                        "pedologie": {
                            "source_moteur": "PEDOLOGY",
                            "source": {
                                "type_source": "peer_reviewed",
                                "auteur": "Test",
                                "reference": "DOI",
                            },
                            "evidence_level": "B",
                            "valeurs": {"pH": 5.2},
                        }
                    },
                    "regles": [
                        {
                            "identifiant": "regle-01",
                            "condition": "pedologie_pH < 5.5",
                            "enonce_conclusion": "Le sol est acide.",
                            "source": {
                                "type_source": "peer_reviewed",
                                "auteur": "Test",
                                "reference": "DOI",
                            },
                            "evidence_level": "B",
                            "niveau_confiance": 0.85,
                        }
                    ],
                    "qualifications": [
                        {
                            "identifiant_regle": "regle-01",
                            "role": "contrainte",
                            "domaine_element": "pedologique",
                        }
                    ],
                    "etat_global": {
                        "etat": "vigueur_reduite",
                        "justification": "Acidité",
                        "source": {
                            "type_source": "peer_reviewed",
                            "auteur": "Test",
                            "reference": "DOI",
                        },
                        "evidence_level": "B",
                    },
                    "type_diagnostic": "stationnel",
                    "question": "Quelles essences ?",
                    "objectif_forestier": "production",
                    "alternatives_demandees": True,
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "aucune règle applicable" in resp.json()["detail"]

    async def should_return_400_when_idempotency_key_does_not_match(
        self, orchestration_client: AsyncClient
    ) -> None:
        payload = _analyse_payload()
        resp = await orchestration_client.post(
            f"{_API_PREFIX}/orchestration/analyse",
            json=payload,
            headers={**_writer_headers(), "Idempotency-Key": str(uuid4())},
        )

        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    async def should_return_409_when_idempotency_conflict_is_detected(
        self, orchestration_client: AsyncClient
    ) -> None:
        from gsie_api.engines.orchestration.idempotency import (
            AnalyseIdempotencyConflictError,
        )

        with patch("gsie_api.engines.orchestration.router.OrchestrationEngine") as mock_cls:
            mock_cls.return_value.analyser_idempotente = AsyncMock(
                side_effect=AnalyseIdempotencyConflictError("contenu différent")
            )
            resp = await orchestration_client.post(
                f"{_API_PREFIX}/orchestration/analyse",
                json=_analyse_payload(),
                headers=_writer_headers(),
            )

        assert resp.status_code == 409
        assert "contenu différent" in resp.json()["detail"]

    @pytest.mark.parametrize(
        ("error_type", "expected_status"),
        [
            ("StationIntrouvableError", 404),
            ("HydratationVideError", 400),
        ],
    )
    async def should_map_analyse_hydration_errors(
        self,
        orchestration_client: AsyncClient,
        error_type: str,
        expected_status: int,
    ) -> None:
        from gsie_api.engines.orchestration.hydration import (
            HydratationVideError,
            StationIntrouvableError,
        )

        exception_type = {
            "StationIntrouvableError": StationIntrouvableError,
            "HydratationVideError": HydratationVideError,
        }[error_type]
        with patch("gsie_api.engines.orchestration.router.OrchestrationEngine") as mock_cls:
            mock_cls.return_value.analyser_idempotente = AsyncMock(
                side_effect=exception_type("contexte stationnel indisponible")
            )
            resp = await orchestration_client.post(
                f"{_API_PREFIX}/orchestration/analyse",
                json=_analyse_payload(),
                headers=_writer_headers(),
            )

        assert resp.status_code == expected_status
        assert "contexte stationnel indisponible" in resp.json()["detail"]

    @pytest.mark.parametrize(
        ("error_type", "expected_status"),
        [
            ("StationIntrouvableError", 404),
            ("HydratationVideError", 400),
        ],
    )
    async def should_map_context_preview_errors(
        self,
        orchestration_client: AsyncClient,
        error_type: str,
        expected_status: int,
    ) -> None:
        from gsie_api.engines.orchestration.hydration import (
            HydratationVideError,
            StationIntrouvableError,
        )

        exception_type = {
            "StationIntrouvableError": StationIntrouvableError,
            "HydratationVideError": HydratationVideError,
        }[error_type]
        with patch("gsie_api.engines.orchestration.router.StationContexteHydrator") as mock_cls:
            mock_cls.return_value.hydrate = AsyncMock(
                side_effect=exception_type("station indisponible")
            )
            resp = await orchestration_client.get(
                f"{_API_PREFIX}/orchestration/stations/{uuid4()}/contexte",
                headers=_auth_headers(),
                params={"niveau_pedologie": "B"},
            )

        assert resp.status_code == expected_status
        assert "station indisponible" in resp.json()["detail"]

    @pytest.mark.parametrize(
        ("error_type", "expected_status"),
        [
            ("StationIntrouvableError", 404),
            ("HydratationVideError", 400),
            ("ReglesQualifieesAbsentesError", 400),
            ("QualificationRegleManquanteError", 400),
            ("EtatGlobalNonSourceError", 400),
            ("VersionRegleManquanteError", 400),
        ],
    )
    async def should_map_station_preparation_errors(
        self,
        orchestration_client: AsyncClient,
        error_type: str,
        expected_status: int,
    ) -> None:
        from gsie_api.engines.orchestration.hydration import (
            HydratationVideError,
            StationIntrouvableError,
        )
        from gsie_api.engines.orchestration.preparation import (
            EtatGlobalNonSourceError,
            QualificationRegleManquanteError,
            ReglesQualifieesAbsentesError,
            VersionRegleManquanteError,
        )

        exception_type = {
            "StationIntrouvableError": StationIntrouvableError,
            "HydratationVideError": HydratationVideError,
            "ReglesQualifieesAbsentesError": ReglesQualifieesAbsentesError,
            "QualificationRegleManquanteError": QualificationRegleManquanteError,
            "EtatGlobalNonSourceError": EtatGlobalNonSourceError,
            "VersionRegleManquanteError": VersionRegleManquanteError,
        }[error_type]
        with patch("gsie_api.engines.orchestration.router.StationPreparationService") as mock_cls:
            mock_cls.return_value.prepare = AsyncMock(
                side_effect=exception_type("préparation refusée")
            )
            resp = await orchestration_client.get(
                f"{_API_PREFIX}/orchestration/stations/{uuid4()}/preparation",
                headers=_auth_headers(),
                params={"niveau_pedologie": "B"},
            )

        assert resp.status_code == expected_status
        assert "préparation refusée" in resp.json()["detail"]


# ===========================================================================
# Reasoning Router
# ===========================================================================


@pytest.fixture
async def reasoning_client() -> AsyncGenerator[AsyncClient, None]:
    mock_db = AsyncMock()
    app = _build_engine_app(reasoning_router, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


class TestReasoningRouter:
    async def should_return_version(self, reasoning_client: AsyncClient) -> None:
        resp = await reasoning_client.get(f"{_API_PREFIX}/reasoning/version")
        assert resp.status_code == 200
        assert resp.json()["backend"] == "postgresql"

    async def should_return_401_when_no_auth_on_infer(self, reasoning_client: AsyncClient) -> None:
        resp = await reasoning_client.post(
            f"{_API_PREFIX}/reasoning/infer",
            json={
                "requete_id": str(uuid4()),
                "station_id": str(uuid4()),
                "contexte": {},
                "question": "test",
                "profondeur_max": 5,
                "regles": [],
            },
        )
        assert resp.status_code == 401

    async def should_return_400_when_engine_error(self, reasoning_client: AsyncClient) -> None:
        from gsie_api.engines.reasoning.engine import ReasoningEngineError

        with patch("gsie_api.engines.reasoning.router.ReasoningEngine") as mock_cls:
            mock_engine = mock_cls.return_value
            mock_engine.infer = AsyncMock(side_effect=ReasoningEngineError("règle mal formée"))
            resp = await reasoning_client.post(
                f"{_API_PREFIX}/reasoning/infer",
                json={
                    "requete_id": str(uuid4()),
                    "station_id": str(uuid4()),
                    "contexte": {
                        "pedologie": {
                            "source_moteur": "PEDOLOGY",
                            "source": {
                                "type_source": "peer_reviewed",
                                "auteur": "Test",
                                "reference": "DOI",
                            },
                            "evidence_level": "B",
                            "valeurs": {"pH": 5.2},
                        }
                    },
                    "question": "Quelles essences ?",
                    "profondeur_max": 5,
                    "regles": [
                        {
                            "identifiant": "regle-01",
                            "condition": "pedologie_pH < 5.5",
                            "enonce_conclusion": "Le sol est acide.",
                            "source": {
                                "type_source": "peer_reviewed",
                                "auteur": "Test",
                                "reference": "DOI",
                            },
                            "evidence_level": "B",
                            "niveau_confiance": 0.85,
                        }
                    ],
                },
                headers=_writer_headers(),
            )
        assert resp.status_code == 400
        assert "règle mal formée" in resp.json()["detail"]
