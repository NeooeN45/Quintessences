"""Tests unitaires — collecte des métriques de qualité DB.

Ces tests gardent deux régressions constatées à l'audit du 2026-08-01 :

1. `collect_db_metrics` faisait `asyncio.run()` depuis un endpoint `async def`.
   L'appel levait `RuntimeError` à tous les coups, un `suppress(Exception)`
   l'avalait, et `/metrics/db-quality` répondait `collected` sans avoir rien
   collecté. Des Gauges restées à zéro se lisent comme « base vide ».
2. La progression des pipelines itérait le `Result` au lieu de `.scalars()`,
   donc des `Row` au lieu de modèles — `AttributeError`, avalée par le même
   `suppress`.

Le premier point se garde par le type de la fonction et par la réponse de
l'endpoint en cas d'échec ; le second par l'absence de `suppress` global,
qui rendait les deux invisibles.
"""

import inspect
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, Gauge

from gsie_api.app import create_app
from gsie_api.core.limiter import limiter
from gsie_api.metrics import collect_db_metrics
from gsie_api.metrics.db_quality import _MAX_SERIES_PAR_METRIQUE, _publier_series


def should_expose_collect_db_metrics_as_a_coroutine():
    """La collecte doit être awaitable — pas de boucle asyncio créée à part.

    `asyncio.run()` echouerait sous un endpoint async, et ouvrirait de toute
    facon une seconde boucle a laquelle les connexions asyncpg de
    `async_session_factory` ne sont pas rattachees.
    """
    assert inspect.iscoroutinefunction(collect_db_metrics)


async def should_propagate_collection_failure():
    """Un echec de collecte remonte : il n'est plus avale silencieusement."""
    with (
        patch(
            "gsie_api.metrics.db_quality._collect_metrics",
            new=AsyncMock(side_effect=RuntimeError("connexion refusee")),
        ),
        pytest.raises(RuntimeError),
    ):
        await collect_db_metrics()


def should_return_503_when_collection_fails(mock_lifespan: object):
    """L'ack ne doit jamais annoncer une collecte qui n'a pas eu lieu."""
    with (
        patch.object(limiter, "enabled", False),
        patch(
            "gsie_api.metrics.collect_db_metrics",
            new=AsyncMock(side_effect=RuntimeError("connexion refusee")),
        ),
        TestClient(create_app()) as client,
    ):
        reponse = client.post("/metrics/db-quality")

    assert reponse.status_code == 503
    # Le texte du pilote reste au journal, pas dans la reponse.
    assert "connexion refusee" not in reponse.text


def should_acknowledge_when_collection_succeeds(mock_lifespan: object):
    """La collecte reussie est attendue, puis acquittee."""
    collecte = AsyncMock()
    # `create_app` importe la collecte localement : la cible du patch est le
    # module d'origine, et l'app doit etre construite sous le patch.
    with (
        patch.object(limiter, "enabled", False),
        patch("gsie_api.metrics.collect_db_metrics", new=collecte),
        TestClient(create_app()) as client,
    ):
        reponse = client.post("/metrics/db-quality")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "collected"}
    collecte.assert_awaited_once()


def should_refuse_get_on_the_collection_endpoint(mock_lifespan: object):
    """La collecte n'est pas une lecture : elle ne doit pas repondre a un GET.

    Cinq agregats sur toute la table `resource` derriere un GET, c'est un
    prechargement de navigateur ou un retry de proxy qui les rejoue.
    """
    collecte = AsyncMock()
    with (
        patch.object(limiter, "enabled", False),
        patch("gsie_api.metrics.collect_db_metrics", new=collecte),
        TestClient(create_app()) as client,
    ):
        reponse = client.get("/metrics/db-quality")

    assert reponse.status_code == 405
    collecte.assert_not_awaited()


def should_cap_label_cardinality_and_purge_stale_series():
    """Les series etiquetees sont plafonnees, et purgees entre deux collectes."""
    gauge = Gauge(
        "gsie_test_cardinalite",
        "Gauge de test — cardinalite",
        labelnames=("namespace",),
        registry=CollectorRegistry(),
    )

    _publier_series(gauge, "gsie_test_cardinalite", "namespace", [("gbif", 10), ("trkp", 5)])
    assert {s.labels["namespace"] for s in gauge.collect()[0].samples} == {"gbif", "trkp"}

    # `trkp` disparait de la base : sa serie ne doit pas survivre.
    _publier_series(gauge, "gsie_test_cardinalite", "namespace", [("gbif", 12)])
    assert {s.labels["namespace"] for s in gauge.collect()[0].samples} == {"gbif"}

    # Au-dela du plafond, seules les premieres series sont publiees.
    trop = [(f"ns{i}", 1) for i in range(_MAX_SERIES_PAR_METRIQUE + 10)]
    _publier_series(gauge, "gsie_test_cardinalite", "namespace", trop)
    assert len(gauge.collect()[0].samples) == _MAX_SERIES_PAR_METRIQUE


def should_replace_none_label_by_a_default():
    """Une valeur d'etiquette nulle devient `unknown` plutot que `None`."""
    gauge = Gauge(
        "gsie_test_defaut",
        "Gauge de test — valeur nulle",
        labelnames=("quality",),
        registry=CollectorRegistry(),
    )

    _publier_series(gauge, "gsie_test_defaut", "quality", [(None, 3)])

    assert gauge.collect()[0].samples[0].labels == {"quality": "unknown"}
