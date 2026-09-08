"""INV-005 — cohérence entre la racine ``resource`` et son sous-type ``agent``."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.engines.recommendation.engine import (
    RecommendationEngine,
    RecommendationEngineError,
)
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enums import AgentType
from gsie_api.infrastructure.models.prov import AgentModel
from tests.conftest import requires_docker

pytestmark = requires_docker


@pytest.mark.asyncio
async def test_agent_refuse_un_uuid_deja_utilise_par_un_autre_type(
    db_session: AsyncSession,
) -> None:
    """Un UUID ``diagnostic`` ne peut jamais devenir implicitement un Agent."""
    identifiant = uuid4()
    db_session.add(
        ResourceModel(
            id=identifiant,
            type="diagnostic",
            gsie_id=f"diagnostic:{identifiant}",
        )
    )
    await db_session.flush()

    with pytest.raises(RecommendationEngineError, match="type racine"):
        await RecommendationEngine(db_session)._agent(
            identifiant,
            nom="Collision volontaire",
            type_agent=AgentType.person,
        )

    assert await db_session.get(AgentModel, identifiant) is None
    racine = await db_session.get(ResourceModel, identifiant)
    assert racine is not None
    assert racine.type == "diagnostic"


@pytest.mark.asyncio
async def test_agent_existant_incompatible_est_refuse_sans_ecrasement(
    db_session: AsyncSession,
) -> None:
    """L'idempotence ne doit pas masquer une collision sémantique d'Agent."""
    identifiant = uuid4()
    db_session.add(
        ResourceModel(
            id=identifiant,
            type="agent",
            gsie_id=f"agent:{identifiant}",
        )
    )
    await db_session.flush()
    db_session.add(
        AgentModel(
            id=identifiant,
            name="Agent logiciel existant",
            type=AgentType.software,
        )
    )
    await db_session.flush()

    with pytest.raises(RecommendationEngineError, match="incompatible"):
        await RecommendationEngine(db_session)._agent(
            identifiant,
            nom="Personne différente",
            type_agent=AgentType.person,
        )

    agent = await db_session.get(AgentModel, identifiant)
    assert agent is not None
    assert agent.name == "Agent logiciel existant"
    assert agent.type is AgentType.software
