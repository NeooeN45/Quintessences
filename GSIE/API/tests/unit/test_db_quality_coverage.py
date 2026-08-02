"""Tests unitaires — métriques DB quality (couverture 46% → 100%).

Mocke async_session_factory pour tester _collect_metrics et
collect_db_metrics sans Docker.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gsie_api.metrics import db_quality


class TestPublierSeries:
    """Couverture de _publier_series (lignes 102-127)."""

    def should_publish_series_with_labels(self) -> None:
        gauge = MagicMock()
        lignes = [("GBIF", 10), ("TAXREF", 5)]
        db_quality._publier_series(gauge, "test_metric", "namespace", lignes)
        gauge.clear.assert_called_once()
        assert gauge.labels.call_count == 2

    def should_use_default_when_label_is_none(self) -> None:
        gauge = MagicMock()
        lignes = [(None, 3)]
        db_quality._publier_series(gauge, "test_metric", "namespace", lignes, defaut="inconnu")
        gauge.labels.assert_called_with(namespace="inconnu")

    def should_cap_series_when_over_max(self) -> None:
        gauge = MagicMock()
        lignes = [(f"ns{i}", i) for i in range(60)]
        db_quality._publier_series(gauge, "test_metric", "namespace", lignes)
        # Plafond à 50 séries
        assert gauge.labels.call_count == 50


class TestCollectMetrics:
    """Couverture de _collect_metrics et collect_db_metrics."""

    async def should_collect_all_metrics_when_db_available(self) -> None:
        # Mock de la session — chaque scalar retourne un compteur
        mock_session = AsyncMock()
        # Les scalars sont appelés dans l'ordre :
        # n_ent, n_images, n_descs, n_validated, n_unvalidated
        mock_session.scalar = AsyncMock(side_effect=[10, 5, 3, 2, 1])
        # Les executes retournent des Result avec fetchone() et scalars()
        mock_result_aliases = MagicMock()
        mock_result_aliases.__iter__ = MagicMock(return_value=iter([("GBIF", 5), ("TAXREF", 3)]))
        mock_result_completeness = MagicMock()
        mock_result_completeness.fetchone.return_value = (10, 5, 3, 2, 1)
        mock_result_lang = MagicMock()
        mock_result_lang.__iter__ = MagicMock(return_value=iter([("fr", 5)]))
        mock_result_quality = MagicMock()
        mock_result_quality.__iter__ = MagicMock(return_value=iter([("good", 3)]))
        mock_result_progress = MagicMock()
        mock_result_progress.scalars = MagicMock(return_value=iter([]))
        mock_session.execute = AsyncMock(
            side_effect=[
                mock_result_aliases,
                mock_result_completeness,
                mock_result_lang,
                mock_result_quality,
                mock_result_progress,
            ]
        )

        @asynccontextmanager
        async def _fake_factory():
            yield mock_session

        with patch.object(db_quality, "async_session_factory", _fake_factory):
            await db_quality._collect_metrics()

    async def should_handle_empty_db_gracefully(self) -> None:
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(side_effect=[0, 0, 0, 0, 0])
        mock_result_empty = MagicMock()
        mock_result_empty.fetchone.return_value = None
        mock_result_empty.__iter__ = MagicMock(return_value=iter([]))
        mock_result_empty.scalars = MagicMock(return_value=iter([]))
        mock_session.execute = AsyncMock(
            side_effect=[
                mock_result_empty,
                mock_result_empty,
                mock_result_empty,
                mock_result_empty,
                mock_result_empty,
            ]
        )

        @asynccontextmanager
        async def _fake_factory():
            yield mock_session

        with patch.object(db_quality, "async_session_factory", _fake_factory):
            await db_quality._collect_metrics()

    async def should_relay_error_from_collect(self) -> None:
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("DB injoignable")
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch.object(db_quality, "async_session_factory", mock_session_factory),
            pytest.raises(Exception, match="DB injoignable"),
        ):
            await db_quality.collect_db_metrics()
