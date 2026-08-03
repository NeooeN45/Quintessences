"""Tests unitaires — Pedology Engine (couverture 70% → 100%).

Couvre la méthode `query` qui appelle SoilGridsClient et construit
les caractéristiques du sol. Le client est mocké.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from gsie_api.engines.evidence.schemas import EvidenceLevel
from gsie_api.engines.pedology.engine import PedologyEngine, PedologyEngineError
from gsie_api.engines.pedology.schemas import PedologyQuery
from gsie_api.engines.pedology.soilgrids_client import SoilGridsClientError


def _make_query() -> PedologyQuery:
    return PedologyQuery(
        latitude=45.0,
        longitude=0.5,
        profondeur="15",
    )


class TestPedologyEngineQuery:
    """Couverture de la méthode query (lignes 76-103)."""

    async def should_return_caracteristiques_when_soilgrids_succeeds(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(
            return_value={"phh2o": 5.5, "clay": 30.0, "sand": 40.0, "silt": 30.0}
        )
        mock_client.unit_for = MagicMock(
            side_effect=lambda prop: {
                "phh2o": "pH",
                "clay": "%",
                "sand": "%",
                "silt": "%",
            }.get(prop, "")
        )

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        assert result.latitude == 45.0
        assert result.longitude == 0.5
        assert len(result.caracteristiques) == 4
        noms = {c.nom for c in result.caracteristiques}
        assert noms == {"ph", "argile_pct", "sable_pct", "limon_pct"}
        assert all(c.evidence_level == EvidenceLevel.B for c in result.caracteristiques)

    async def should_filter_unknown_properties(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={"phh2o": 5.5, "unknown_prop": 42.0})
        mock_client.unit_for = MagicMock(return_value="unit")

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        # unknown_prop n'est pas dans _PROPERTY_LABELS → filtré
        assert len(result.caracteristiques) == 1
        assert result.caracteristiques[0].nom == "ph"

    async def should_return_empty_caracteristiques_when_no_data(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={})
        mock_client.unit_for = MagicMock(return_value="unit")

        engine = PedologyEngine(soilgrids_client=mock_client)
        result = await engine.query(_make_query())

        assert len(result.caracteristiques) == 0

    async def should_raise_pedology_error_when_soilgrids_fails(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(side_effect=SoilGridsClientError("API indisponible"))

        engine = PedologyEngine(soilgrids_client=mock_client)
        with pytest.raises(PedologyEngineError, match="API indisponible"):
            await engine.query(_make_query())

    def should_return_version_0_1_0(self) -> None:
        assert PedologyEngine.version() == "0.1.0"
