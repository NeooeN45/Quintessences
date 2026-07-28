"""Fiabilité des moteurs sur base réelle — trois défauts confirmés par exécution.

* **Diagnostic** : `date_diagnostic` entrait dans `contenu` mais pas dans la
  dérivation de `diagnostic_id`. Tout rejeu d'une requête identique — un simple
  retry après expiration réseau — échouait, avec un motif qui accusait à tort
  des « contradictions divergentes ».
* **Knowledge** : `evidence_assessment` est une relation 1-N append-only ; la
  jointure directe dupliquait la connaissance à chaque révision, gonflait
  `total` et présentait le niveau de preuve périmé comme une connaissance.
* **Botanical** : `_get_or_create_taxon` lisait puis insérait sans garde ; deux
  requêtes concurrentes sur la même essence violaient l'unicité de
  `resource.gsie_id` et remontaient en 500.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.engines.diagnostic.router import _EXEMPLE_REQUETE
from gsie_api.infrastructure.database import get_db
from tests.conftest import requires_docker

pytestmark = requires_docker

_ENTETES = {
    "Authorization": f"Bearer {create_access_token(subject='moteurs', claims={'roles': ['admin']})}"
}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestDiagnosticRejouable:
    """Deux appels strictement identiques doivent rendre la même réponse."""

    async def test_le_rejeu_rend_le_meme_diagnostic(self, client: AsyncClient) -> None:
        premier = await client.post(
            "/api/v1/diagnostic/diagnostiquer", json=_EXEMPLE_REQUETE, headers=_ENTETES
        )
        assert premier.status_code == 200, premier.text

        second = await client.post(
            "/api/v1/diagnostic/diagnostiquer", json=_EXEMPLE_REQUETE, headers=_ENTETES
        )

        assert second.status_code == 200, second.text
        assert second.json()["diagnostic_id"] == premier.json()["diagnostic_id"]
        # Horloge comprise : le rejeu rend le diagnostic déjà enregistré.
        assert second.json() == premier.json()


class TestKnowledgeSansDoublon:
    """Réviser le niveau de preuve ne doit pas dupliquer la connaissance."""

    @staticmethod
    def _connaissance(identifiant: str) -> dict[str, Any]:
        return {
            "connaissance_id": identifiant,
            "type": "regle",
            "titre": "Règle de test",
            "description": "Connaissance de test pour la déduplication.",
            "domaine_scientifique": "sylviculture",
            "contenu_normalise": {"enonce": "test"},
            "evidence_level": "B",
            "statut": "accepte",
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Auteur de test",
                "reference": "Référence de test 2026",
            },
        }

    @staticmethod
    def _requete(identifiant: str) -> dict[str, Any]:
        return {"requete_id": identifiant, "type": "par_domaine"}

    async def test_une_revision_ne_duplique_pas_la_connaissance(self, client: AsyncClient) -> None:
        identifiant = "22222222-2222-4222-8222-222222222222"
        ingest = await client.post(
            "/api/v1/knowledge/ingest",
            json=self._connaissance(identifiant),
            headers=_ENTETES,
        )
        assert ingest.status_code in (200, 201), ingest.text

        avant = await client.post(
            "/api/v1/knowledge/query",
            json=self._requete("33333333-3333-4333-8333-333333333331"),
            headers=_ENTETES,
        )
        assert avant.status_code == 200, avant.text
        total_avant = avant.json()["total"]

        revise = await client.post(
            "/api/v1/knowledge/revise",
            json={
                "connaissance_id": identifiant,
                "justification": "montée du niveau de preuve",
                "nouveau_evidence_level": "A",
            },
            headers=_ENTETES,
        )
        assert revise.status_code == 200, revise.text

        apres = await client.post(
            "/api/v1/knowledge/query",
            json=self._requete("33333333-3333-4333-8333-333333333332"),
            headers=_ENTETES,
        )

        assert apres.status_code == 200, apres.text
        # La révision ajoute une ligne evidence_assessment (append-only) mais
        # ne crée pas une seconde connaissance.
        assert apres.json()["total"] == total_avant
        identifiants = [o["connaissance_id"] for o in apres.json()["connaissances"]]
        assert len(identifiants) == len(set(identifiants))
        courante = next(
            o for o in apres.json()["connaissances"] if o["connaissance_id"] == identifiant
        )
        # C'est le niveau courant qui est exposé, pas le périmé.
        assert courante["evidence_level"] == "A"


class TestReferencePendante:
    """Pointer une resource inexistante est une faute d'appelant, pas une panne."""

    async def test_une_fk_inexistante_rend_422_et_nomme_le_champ(self, client: AsyncClient) -> None:
        reponse = await client.post(
            "/api/v1/resources",
            json={
                "type": "citation",
                "data": {
                    "source_id": "44444444-4444-4444-8444-444444444444",
                    "target_id": "55555555-5555-4555-8555-555555555555",
                    "citation_role": "primary",
                },
            },
            headers=_ENTETES,
        )

        assert reponse.status_code == 422, reponse.text
        detail = reponse.json()["detail"]
        assert any("source_id" in erreur or "target_id" in erreur for erreur in detail["errors"])


class TestCorrelationVarianceNulle:
    """Une variable constante est une entrée dégénérée, pas une erreur serveur."""

    @staticmethod
    def _serie(nom: str, valeurs: list[float]) -> dict[str, Any]:
        return {
            "source_moteur": "PEDOLOGY",
            "variable": nom,
            "unite": "m",
            "valeurs": valeurs,
        }

    @classmethod
    def _requete(cls, identifiant: str, methode: str, valeurs_a: list[float]) -> dict[str, Any]:
        return {
            "requete_id": identifiant,
            "domaine": "stationnel",
            "variable_a": cls._serie("altitude", valeurs_a),
            "variable_b": cls._serie("hauteur", [1.0, 2.0, 3.0, 4.0, 5.0]),
            "methode": methode,
            "source": {
                "type_source": "peer_reviewed",
                "auteur": "Auteur de test",
                "reference": "Référence de test 2026",
            },
            "evidence_level": "B",
        }

    async def test_le_cas_nominal_aboutit(self, client: AsyncClient) -> None:
        """Témoin : sans lui, un refus dû à la charge utile passerait pour un succès.

        C'est précisément le piège dans lequel la première version de ce test
        était tombée — elle recevait 422 sans jamais atteindre le moteur.
        """
        reponse = await client.post(
            "/api/v1/correlation/compute",
            json=self._requete(
                "66666666-6666-4666-8666-666666666660",
                "pearson",
                [1.0, 2.1, 2.9, 4.2, 5.1],
            ),
            headers=_ENTETES,
        )

        assert reponse.status_code in (200, 201), reponse.text

    @pytest.mark.parametrize(
        ("methode", "identifiant"),
        [
            ("pearson", "66666666-6666-4666-8666-666666666661"),
            ("spearman", "66666666-6666-4666-8666-666666666662"),
            ("kendall", "66666666-6666-4666-8666-666666666663"),
        ],
    )
    async def test_une_serie_constante_est_refusee_proprement(
        self, client: AsyncClient, methode: str, identifiant: str
    ) -> None:
        reponse = await client.post(
            "/api/v1/correlation/compute",
            json=self._requete(identifiant, methode, [1.0, 1.0, 1.0, 1.0, 1.0]),
            headers=_ENTETES,
        )

        # 400 : erreur métier nommée. Surtout pas 500, et surtout pas 422 —
        # un 422 signalerait que la requête n'a jamais atteint le moteur.
        assert reponse.status_code == 400, reponse.text
        assert "constante" in reponse.text


class TestBotanicalConcurrence:
    """Deux requêtes simultanées sur le même taxon ne doivent pas se percuter."""

    async def test_deux_sessions_creent_un_seul_taxon(
        self, postgres_url: str, db_session: AsyncSession
    ) -> None:
        """`db_session` est demandée pour son effet de bord : elle crée le schéma."""
        import asyncio

        from sqlalchemy.ext.asyncio import create_async_engine

        from gsie_api.engines.botanical.engine import BotanicalEngine

        moteur = create_async_engine(postgres_url, pool_pre_ping=True)
        fabrique = async_sessionmaker(moteur, class_=AsyncSession, expire_on_commit=False)

        async def creer() -> Any:
            async with fabrique() as session:
                identifiant = await BotanicalEngine(session)._get_or_create_taxon(2878688)
                await session.commit()
                return identifiant

        resultats = await asyncio.gather(creer(), creer(), return_exceptions=True)
        await moteur.dispose()

        echecs = [r for r in resultats if isinstance(r, BaseException)]
        assert echecs == [], f"la course n'est pas rattrapée : {echecs}"
        assert resultats[0] == resultats[1], "deux entités créées pour le même taxon"
