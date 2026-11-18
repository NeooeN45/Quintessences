"""Campagne PostgreSQL reconstituée à partir du bilan PR74, §7.2.

Le script historique était archivé hors dépôt. Exécuter la campagne avec
`pytest tests/integration/test_orchestration.py -k campagne_agent_moteur -s`.
Le banc migre puis clone une base jetable du conteneur de test. Il conserve
le résultat de chaque transaction, y compris ses erreurs, sans réessayer.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from gsie_api.engines.orchestration.schemas import AnalyseRequest
from gsie_api.engines.orchestration.service import OrchestrationEngine
from gsie_api.engines.recommendation.engine import _NAMESPACE_AGENTS, RecommendationEngine
from gsie_api.infrastructure.models.base import ResourceModel
from gsie_api.infrastructure.models.enrichment import AnalysisRunModel
from gsie_api.infrastructure.models.enums import AgentType
from gsie_api.infrastructure.models.prov import AgentModel
from gsie_api.infrastructure.models.reasoning import RecommendationModel

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest import MonkeyPatch
    from sqlalchemy.engine import URL
    from sqlalchemy.ext.asyncio import AsyncEngine

_PLAN = json.loads(Path(__file__).with_name("harnais_f_plan.json").read_text(encoding="utf-8"))
_AGENT_ID = uuid5(_NAMESPACE_AGENTS, "recommendation-engine")
_GSIE_ID = f"agent:{_AGENT_ID}"


@dataclass(frozen=True)
class AnalyseValidee:
    identifiant: UUID
    recommandations: frozenset[UUID]


def _decrire_erreur(erreur: BaseException) -> dict[str, str | None]:
    cause: BaseException | None = getattr(erreur, "orig", erreur)
    sqlstate = None
    contrainte = None
    while cause is not None:
        sqlstate = sqlstate or getattr(cause, "sqlstate", None)
        contrainte = contrainte or getattr(cause, "constraint_name", None)
        cause = cause.__cause__
    return {
        "erreur": type(erreur).__name__,
        "sqlstate": sqlstate,
        "contrainte": contrainte,
    }


async def _migrer(url: URL) -> None:
    url_interne = url.render_as_string(hide_password=False)
    racine_api = Path(__file__).resolve().parents[2]
    migration = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "upgrade",
        "head",
        cwd=racine_api,
        env={
            **os.environ,
            "GSIE_ENVIRONMENT": "development",
            "GSIE_DATABASE_URL": url_interne,
            "GSIE_MIGRATION_DATABASE_URL": url_interne,
            "GSIE_DATABASE_ROLE": "test",
            "GSIE_DATA_NAMESPACE": "gsie-agent-concurrence-test",
        },
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    sortie, _ = await migration.communicate()
    assert migration.returncode == 0, sortie.decode(errors="replace").replace(
        url_interne, url.render_as_string()
    )


async def _salve(
    moteur: AsyncEngine, monkeypatch: MonkeyPatch, corps: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    fabrique = async_sessionmaker(moteur, expire_on_commit=False)
    taille = _PLAN["analyses_par_salve"]
    barriere = asyncio.Barrier(taille)
    arrivees: list[tuple[int, str]] = []
    sorties: list[tuple[int, str]] = []
    agent_original = RecommendationEngine._agent

    async def attendre_avant_insert(
        instance: RecommendationEngine, agent_id: UUID, *, nom: str, type_agent: AgentType
    ) -> UUID:
        assert (agent_id, type_agent) == (_AGENT_ID, AgentType.software)
        assert instance._session.in_transaction()
        pid, xid = (
            await instance._session.execute(
                text("SELECT pg_backend_pid(), pg_current_xact_id()::text")
            )
        ).one()
        arrivees.append((pid, xid))
        async with asyncio.timeout(_PLAN["delai_barriere_secondes"]):
            await barriere.wait()
        sorties.append((pid, xid))
        return await agent_original(instance, agent_id, nom=nom, type_agent=type_agent)

    async def executer(requete: AnalyseRequest) -> AnalyseValidee:
        async with fabrique.begin() as session:
            resultat = await OrchestrationEngine(session).analyser(requete, datetime.now(UTC))
            recommandations = frozenset(
                candidate.recommandation_id
                for recommandation in resultat.recommandations.recommandations
                for candidate in (recommandation, *recommandation.alternatives)
            )
        # `begin()` a commité avant que le succès soit compté.
        return AnalyseValidee(resultat.analyse_id, recommandations)

    requetes = [AnalyseRequest.model_validate(corps()) for _ in range(taille)]
    with monkeypatch.context() as patch:
        patch.setattr(RecommendationEngine, "_agent", attendre_avant_insert)
        async with asyncio.timeout(_PLAN["delai_salve_secondes"]):
            resultats = await asyncio.gather(
                *(executer(requete) for requete in requetes), return_exceptions=True
            )

    analyses_attendues: dict[UUID, UUID] = {}
    recommandations_attendues: set[UUID] = set()
    erreurs = []
    for numero, (requete, resultat) in enumerate(zip(requetes, resultats, strict=True), 1):
        if isinstance(resultat, BaseException):
            erreurs.append({"session": numero, **_decrire_erreur(resultat)})
        else:
            assert resultat.identifiant not in analyses_attendues
            assert resultat.recommandations
            analyses_attendues[resultat.identifiant] = requete.requete_id
            recommandations_attendues.update(resultat.recommandations)

    async with fabrique() as session:
        analyses = (
            await session.execute(select(AnalysisRunModel.id, AnalysisRunModel.requete_origine))
        ).all()
        recommandations = (
            await session.execute(
                select(RecommendationModel.id, RecommendationModel.recommended_by)
            )
        ).all()
        agents = (
            await session.execute(
                select(ResourceModel.id, ResourceModel.type, ResourceModel.gsie_id, AgentModel.type)
                .outerjoin(AgentModel, AgentModel.id == ResourceModel.id)
                .where((ResourceModel.id == _AGENT_ID) | (ResourceModel.gsie_id == _GSIE_ID))
            )
        ).all()

    assert len(arrivees) == len(sorties) == taille
    assert len({pid for pid, _ in arrivees}) == len({xid for _, xid in arrivees}) == taille
    assert set(arrivees) == set(sorties)
    assert dict(analyses) == analyses_attendues
    assert dict(recommandations) == dict.fromkeys(recommandations_attendues, _AGENT_ID)
    assert agents == ([(_AGENT_ID, "agent", _GSIE_ID, AgentType.software)] if analyses else [])

    return {
        "analyses": taille,
        "persistances": len(analyses),
        "arrivees": arrivees,
        "sorties": sorties,
        "erreurs": erreurs,
    }


async def lancer_campagne_agent(
    postgres_url: str, monkeypatch: MonkeyPatch, corps: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    """Exécute le budget fixé sur des clones de la même base sans Agent."""
    url = make_url(postgres_url)
    admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
    # Noms générés, jamais issus d'une entrée SQL ni d'un élément de l'URL.
    template = f"course_agent_{uuid4().hex}"
    salves = []
    try:
        async with admin.connect() as connexion:
            await connexion.execute(text(f"CREATE DATABASE {template} TEMPLATE template0"))
            try:
                await _migrer(url.set(database=template))
                for numero in range(1, _PLAN["salves"] + 1):
                    clone = f"{template}_{numero}"
                    await connexion.execute(text(f"CREATE DATABASE {clone} TEMPLATE {template}"))
                    moteur = create_async_engine(
                        url.set(database=clone),
                        pool_size=_PLAN["analyses_par_salve"],
                        max_overflow=0,
                        isolation_level=_PLAN["isolation"],
                    )
                    try:
                        salves.append(
                            {"numero": numero, **await _salve(moteur, monkeypatch, corps)}
                        )
                    finally:
                        await moteur.dispose()
                        await connexion.execute(text(f"DROP DATABASE {clone}"))
            finally:
                await connexion.execute(text(f"DROP DATABASE {template}"))
    finally:
        await admin.dispose()

    return {
        "analyses": sum(salve["analyses"] for salve in salves),
        "reussites": sum(salve["persistances"] for salve in salves),
        "echecs": sum(len(salve["erreurs"]) for salve in salves),
        "salves": salves,
    }
