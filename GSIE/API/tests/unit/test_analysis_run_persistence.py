from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from gsie_api.engines.orchestration.service import OrchestrationEngine
from gsie_api.engines.validation.schemas import ValidationStatut
from gsie_api.infrastructure.models.enrichment import AnalysisRunModel


@pytest.mark.asyncio
async def test_persiste_la_preuve_complete_sur_la_session_partagee() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    resultat = MagicMock()
    resultat.analyse_id = uuid4()
    resultat.requete_origine = uuid4()
    resultat.validation.statut = ValidationStatut.bloque
    resultat.model_dump.return_value = {
        "analyse_id": str(resultat.analyse_id),
        "inference": {"conclusions": []},
        "diagnostic": {},
        "recommandations": {},
        "validation": {"statut": "bloque"},
    }

    await OrchestrationEngine(session)._persister_analyse(
        resultat, uuid4(), datetime(2026, 8, 13, tzinfo=UTC)
    )

    ligne = session.add.call_args.args[0]
    assert isinstance(ligne, AnalysisRunModel)
    assert ligne.id == resultat.analyse_id
    assert ligne.statut_validation == "bloque"
    assert ligne.contenu["validation"]["statut"] == "bloque"
    session.flush.assert_awaited_once()
