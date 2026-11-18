"""Contrat PostgreSQL de l'identité Resource/Agent (ticket #76)."""

import asyncio
from time import perf_counter
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from gsie_api.engines.recommendation.engine import RecommendationEngine, RecommendationEngineError
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enums import AgentType
from gsie_api.infrastructure.models.prov import AgentModel
from tests.conftest import requires_docker

pytestmark = requires_docker


async def should_refuse_agent_when_gsie_id_belongs_to_another_uuid(
    db_session: AsyncSession,
) -> None:
    attendu, occupant = uuid4(), uuid4()
    gsie_id = f"agent:{attendu}"
    db_session.add(ResourceModel(id=occupant, type="agent", gsie_id=gsie_id))
    await db_session.flush()

    with pytest.raises(RecommendationEngineError, match="Identité racine Agent incohérente"):
        await RecommendationEngine(db_session)._agent(
            attendu, nom="Moteur", type_agent=AgentType.software
        )

    assert await db_session.get(ResourceModel, attendu) is None
    assert await db_session.get(AgentModel, attendu) is None
    assert (
        await db_session.scalar(select(ResourceModel.id).where(ResourceModel.gsie_id == gsie_id))
        == occupant
    )


@pytest.mark.parametrize(
    ("type_racine", "gsie_id_canonique"), [("concept", True), ("agent", False)]
)
async def should_refuse_agent_when_root_tuple_differs(
    db_session: AsyncSession, type_racine: str, gsie_id_canonique: bool
) -> None:
    identifiant = uuid4()
    gsie_id = f"agent:{identifiant if gsie_id_canonique else uuid4()}"
    db_session.add(ResourceModel(id=identifiant, type=type_racine, gsie_id=gsie_id))
    await db_session.flush()

    with pytest.raises(RecommendationEngineError, match="Identité racine Agent incohérente"):
        await RecommendationEngine(db_session)._agent(
            identifiant, nom="Moteur", type_agent=AgentType.software
        )

    assert await db_session.get(AgentModel, identifiant) is None
    assert (
        await db_session.execute(
            select(ResourceModel.type, ResourceModel.gsie_id).where(ResourceModel.id == identifiant)
        )
    ).one() == (type_racine, gsie_id)


async def should_refuse_agent_when_existing_child_type_differs(db_session: AsyncSession) -> None:
    identifiant = uuid4()
    db_session.add(ResourceModel(id=identifiant, type="agent", gsie_id=f"agent:{identifiant}"))
    await db_session.flush()
    db_session.add(AgentModel(id=identifiant, name="Personne", type=AgentType.person))
    await db_session.flush()

    with pytest.raises(RecommendationEngineError, match="Type du sous-type Agent incohérent"):
        await RecommendationEngine(db_session)._agent(
            identifiant, nom="Moteur", type_agent=AgentType.software
        )

    assert (
        await db_session.execute(
            select(AgentModel.type, AgentModel.name).where(AgentModel.id == identifiant)
        )
    ).one() == (AgentType.person, "Personne")


async def should_rollback_root_when_agent_insert_is_interrupted(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert db_session.bind is not None
    fabrique = async_sessionmaker(db_session.bind)
    identifiant = uuid4()
    async with fabrique() as session:
        executer = session.execute

        async def interrompre_enfant(requete):
            if requete.is_insert and requete.table.name == "agent":
                # La racine a été écrite dans la transaction interrompue.
                assert await session.get(ResourceModel, identifiant) is not None
                raise RuntimeError("Interruption du test entre racine et enfant")
            return await executer(requete)

        monkeypatch.setattr(session, "execute", interrompre_enfant)
        with pytest.raises(RuntimeError, match="Interruption du test entre racine et enfant"):
            async with session.begin():
                await RecommendationEngine(session)._agent(
                    identifiant, nom="Moteur", type_agent=AgentType.software
                )

    assert await db_session.get(ResourceModel, identifiant) is None
    assert await db_session.get(AgentModel, identifiant) is None


@pytest.mark.parametrize("ligne", ["racine", "enfant"])
async def should_protect_validated_types_until_commit(db_session: AsyncSession, ligne: str) -> None:
    # Partir d'un Agent déjà commité : aucun verrou d'une création en cours ne
    # doit pouvoir faire passer cette sonde à la place du verrou de relecture.
    assert db_session.bind is not None
    fabrique = async_sessionmaker(db_session.bind, expire_on_commit=False)
    identifiant = uuid4()
    db_session.add(ResourceModel(id=identifiant, type="agent", gsie_id=f"agent:{identifiant}"))
    await db_session.flush()
    db_session.add(AgentModel(id=identifiant, name="Nom conservé", type=AgentType.software))
    await db_session.commit()

    async def relire() -> None:
        async with fabrique.begin() as session:
            assert (
                await RecommendationEngine(session)._agent(
                    identifiant, nom="Autre nom", type_agent=AgentType.software
                )
                == identifiant
            )

    modification = (
        update(ResourceModel).where(ResourceModel.id == identifiant).values(type="concept")
        if ligne == "racine"
        else update(AgentModel).where(AgentModel.id == identifiant).values(type=AgentType.person)
    )
    async with fabrique.begin() as lectrice:
        assert await lectrice.scalar(text("SHOW transaction_isolation")) == "read committed"
        await RecommendationEngine(lectrice)._agent(
            identifiant, nom="Moteur", type_agent=AgentType.software
        )
        # Une autre analyse doit pouvoir utiliser le même Agent avant notre commit.
        await asyncio.wait_for(relire(), timeout=5)
        async with fabrique() as modificatrice:
            await modificatrice.execute(text("SET LOCAL lock_timeout = '250ms'"))
            debut = perf_counter()
            with pytest.raises(DBAPIError) as erreur:
                await modificatrice.execute(modification)
            attente = perf_counter() - debut
            assert erreur.value.orig.sqlstate == "55P03"
            print(f"{ligne} : modification bloquée après {attente * 1000:.1f} ms (55P03)")

    async with fabrique() as modificatrice:
        await modificatrice.execute(text("SET LOCAL lock_timeout = '250ms'"))
        debut = perf_counter()
        assert (await modificatrice.execute(modification)).rowcount == 1
        attente = perf_counter() - debut
        print(f"{ligne} : modification possible après commit ({attente * 1000:.1f} ms)")
        await modificatrice.rollback()
    assert (
        await db_session.scalar(select(AgentModel.name).where(AgentModel.id == identifiant))
        == "Nom conservé"
    )
