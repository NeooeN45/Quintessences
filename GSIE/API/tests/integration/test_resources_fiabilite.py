"""Fiabilité du CRUD générique sur base réelle — chemins jamais couverts.

Trois défauts se cachaient derrière les tests existants :

* `revision.author_id` et `resource_diff.id` référencent `resource(id)` ; le
  service citait des identifiants sans ligne parente, donc toute écriture
  authentifiée échouait en `ForeignKeyViolationError` sur PostgreSQL. Les tests
  unitaires tournent sur SQLite, qui n'applique pas les clés étrangères, et la
  suite d'intégration créait l'Agent à la main dans sa fixture — le chemin de
  production, lui, n'était garanti par rien.
* la relecture qui suit l'écriture touchait des colonnes `onupdate=func.now()`
  expirées par le commit, déclenchant un chargement paresseux hors greenlet.
* `GET /resources?type=` (vide) était traité comme un filtre : l'exclusion RGPD
  était désactivée alors qu'aucun filtre n'était réellement appliqué.

Ces tests exercent donc le chemin nominal **sans** rien préparer à la main.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gsie_api.app import create_app
from gsie_api.core.auth import create_access_token
from gsie_api.core.rbac import RGPD_RESOURCE_TYPES
from gsie_api.infrastructure.database import get_db
from gsie_api.infrastructure.models import ResourceModel
from gsie_api.infrastructure.models.temporal_engine import ResourceDiffModel, RevisionModel
from tests.conftest import requires_docker

pytestmark = requires_docker

_SUJET = "forestier-fiabilite"


@pytest.fixture
def entetes_ecriture() -> dict[str, str]:
    """Jeton forge a l'execution — un jeton forge a l'import perime apres 15 min
    (TTL jwt_access_token_expire_minutes), et la suite complete dure plus longtemps.
    """
    return {
        "Authorization": f"Bearer {create_access_token(subject=_SUJET, claims={'roles': ['writer']})}",  # noqa: E501
    }


@pytest.fixture
def entetes_lecture() -> dict[str, str]:
    """Jeton de lecture forge a l'execution — meme raison que `entetes_ecriture`."""
    return {
        "Authorization": f"Bearer {create_access_token(subject='liseur', claims={'roles': ['reader']})}",  # noqa: E501
    }


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP sans aucune préparation : l'Agent auteur n'existe pas."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestEcritureAuthentifiee:
    """L'auteur cité doit exister : le service le matérialise lui-même."""

    async def test_creation_reussit_sans_agent_pre_cree(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": "entity", "data": {"entity_subtype": "parcelle"}},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text

    async def test_mise_a_jour_ecrit_un_diff_rattache(
        self, client: AsyncClient, db_session: AsyncSession, entetes_ecriture: dict[str, str]
    ) -> None:
        cree = await client.post(
            "/api/v1/resources",
            json={"type": "entity", "data": {"entity_subtype": "avant"}},
            headers=entetes_ecriture,
        )
        assert cree.status_code == 201, cree.text
        identifiant = cree.json()["id"]

        maj = await client.put(
            f"/api/v1/resources/{identifiant}",
            json={"data": {"entity_subtype": "apres"}, "justification": "affinage station"},
            headers=entetes_ecriture,
        )

        assert maj.status_code == 200, maj.text
        # La valeur relue après commit prouve l'absence de chargement paresseux.
        assert maj.json()["data"]["entity_subtype"] == "apres"

        diff = (await db_session.execute(select(ResourceDiffModel))).scalars().one()
        revision = (
            (await db_session.execute(select(RevisionModel).where(RevisionModel.version == 2)))
            .scalars()
            .one()
        )
        assert revision.diff_id == diff.id
        # Le diff est bien une resource du métamodèle (type 61, ADR-002),
        # pas un identifiant orphelin.
        parent = await db_session.get(ResourceModel, diff.id)
        assert parent is not None
        assert parent.type == "resource_diff"


class TestCoercitionDesTypes:
    """`data` est un dict libre : le service doit convertir, pas faire confiance."""

    @pytest.mark.parametrize(
        ("type_name", "data"),
        [
            ("activity", {"type": "extraction", "started_at": "2026-01-15T10:00:00Z"}),
            (
                "temporal_context",
                {
                    "valid_time_start": "2026-01-15T10:00:00Z",
                    "transaction_time_start": "2026-01-15T10:00:00Z",
                    "granularity": "day",
                },
            ),
            (
                "question",
                {"text": "q", "question_type": "scientific", "asked_at": "2026-01-15T10:00:00Z"},
            ),
        ],
    )
    async def test_une_date_iso_est_convertie(
        self,
        client: AsyncClient,
        type_name: str,
        data: dict[str, object],
        entetes_ecriture: dict[str, str],
    ) -> None:
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": type_name, "data": data},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text

    async def test_une_geometrie_reste_lisible_apres_ecriture(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """La ligne était écrite puis la resource devenait illisible (500 permanent)."""
        cree = await client.post(
            "/api/v1/resources",
            json={
                "type": "place",
                "data": {"geometry": "SRID=2154;POINT(650000 6860000)", "srid": 2154},
            },
            headers=entetes_ecriture,
        )
        assert cree.status_code == 201, cree.text

        relecture = await client.get(
            f"/api/v1/resources/{cree.json()['id']}", headers=entetes_ecriture
        )

        assert relecture.status_code == 200, relecture.text
        assert "650000" in str(relecture.json()["data"]["geometry"])

    @pytest.mark.parametrize(
        ("type_name", "data"),
        [
            ("observation", {"subject_id": "pas-un-uuid"}),
            ("place", {"geometry": "PAS DU WKT", "srid": 2154}),
            # Un instant sans fuseau serait réinterprété dans celui du serveur.
            ("activity", {"type": "extraction", "started_at": "2026-01-15T10:00:00"}),
        ],
    )
    async def test_une_valeur_mal_typee_donne_422_et_non_500(
        self,
        client: AsyncClient,
        type_name: str,
        data: dict[str, object],
        entetes_ecriture: dict[str, str],
    ) -> None:
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": type_name, "data": data},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 422, reponse.text


class TestChampsMetierHomonymes:
    """`version` est un champ métier ici, pas le compteur système d'`assertion`."""

    @pytest.mark.parametrize(
        ("parent_type", "parent_data", "type_name", "cle_parent"),
        [
            (
                "vocabulary",
                {"name": "v", "namespace": "n", "description": "d"},
                "vocabulary_release",
                "vocabulary_id",
            ),
            (
                "model",
                {"name": "m", "type": "growth", "description": "d"},
                "model_version",
                "model_id",
            ),
        ],
    )
    async def test_un_type_versionne_est_creable(
        self,
        client: AsyncClient,
        parent_type: str,
        parent_data: dict[str, object],
        type_name: str,
        cle_parent: str,
        entetes_ecriture: dict[str, str],
    ) -> None:
        parent = await client.post(
            "/api/v1/resources",
            json={"type": parent_type, "data": parent_data},
            headers=entetes_ecriture,
        )
        assert parent.status_code == 201, parent.text

        reponse = await client.post(
            "/api/v1/resources",
            json={
                "type": type_name,
                "data": {cle_parent: parent.json()["id"], "version": "1.0.0"},
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text


class TestExclusionRGPD:
    """Un `?type=` vide n'est pas un filtre et ne lève aucune protection."""

    @pytest.mark.parametrize("requete", ["/api/v1/resources", "/api/v1/resources?type="])
    async def test_lecteur_ne_voit_jamais_les_types_rgpd(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        requete: str,
        entetes_lecture: dict[str, str],
    ) -> None:
        db_session.add(ResourceModel(type="consent", gsie_id="consent:2026:fiabilite"))
        db_session.add(ResourceModel(type="entity", gsie_id="entity:2026:fiabilite"))
        await db_session.commit()

        reponse = await client.get(requete, headers=entetes_lecture)

        assert reponse.status_code == 200, reponse.text
        types_vus = {item["type"] for item in reponse.json()["items"]}
        assert types_vus.isdisjoint(RGPD_RESOURCE_TYPES)
        assert "entity" in types_vus


class TestResolutionNativeDeclaree:
    """Une distribution qui déclare une échelle doit en déclarer le grain.

    `NOMENCLATURE_SOURCES.md` §4 : la résolution native d'une source doit être
    un nombre. Tant qu'elle reste en prose — « 50 cm rasters », « Placettes
    20 m rayon » — deux sources ne sont pas comparables, et aucun moteur ne
    peut refuser de croiser des données d'échelles incompatibles.
    """

    @staticmethod
    async def _creer_echelle(
        client: AsyncClient, grain: float | None, entetes: dict[str, str]
    ) -> str:
        data: dict[str, Any] = {"level": "landscape"}
        if grain is not None:
            data["grain_m2"] = grain
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": "scale_context", "data": data},
            headers=entetes,
        )
        assert reponse.status_code == 201, reponse.text
        identifiant: str = reponse.json()["id"]
        return identifiant

    @staticmethod
    async def _creer_version(client: AsyncClient, entetes: dict[str, str]) -> str:
        jeu = await client.post(
            "/api/v1/resources",
            json={"type": "dataset", "data": {"title": "LiDAR HD", "description": "IGN"}},
            headers=entetes,
        )
        assert jeu.status_code == 201, jeu.text
        version = await client.post(
            "/api/v1/resources",
            json={
                "type": "dataset_version",
                "data": {"dataset_id": jeu.json()["id"], "version": "2024"},
            },
            headers=entetes,
        )
        assert version.status_code == 201, version.text
        identifiant: str = version.json()["id"]
        return identifiant

    async def _distribution(
        self, client: AsyncClient, echelle: str, entetes: dict[str, str]
    ) -> Any:
        version = await self._creer_version(client, entetes)
        return await client.post(
            "/api/v1/resources",
            json={
                "type": "distribution",
                "data": {
                    "dataset_version_id": version,
                    "access_method": "file_download",
                    "licence": "Licence Ouverte 2.0",
                    "scale_context_id": echelle,
                },
            },
            headers=entetes,
        )

    async def test_une_echelle_sans_grain_est_refusee(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        sans_grain = await self._creer_echelle(client, None, entetes_ecriture)

        reponse = await self._distribution(client, sans_grain, entetes_ecriture)

        assert reponse.status_code == 422, reponse.text
        assert any("grain_m2" in e for e in reponse.json()["detail"]["errors"])

    async def test_une_echelle_avec_grain_est_acceptee(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Témoin : c'est bien l'absence de grain qui est refusée, pas le lien."""
        avec_grain = await self._creer_echelle(client, 0.25, entetes_ecriture)

        reponse = await self._distribution(client, avec_grain, entetes_ecriture)

        assert reponse.status_code == 201, reponse.text

    async def test_data_asset_accepte_un_fichier_superieur_a_2_gio(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """La taille BIGINT est conservée par le CRUD générique."""
        version = await self._creer_version(client, entetes_ecriture)
        reponse = await client.post(
            "/api/v1/resources",
            json={
                "type": "data_asset",
                "data": {
                    "dataset_version_id": version,
                    "format": "copc",
                    "size_bytes": 5_000_000_000,
                    "checksum": "a" * 64,
                    "checksum_algorithm": "sha256",
                    "storage_uri": "s3://gsie-assets/forest/copc.laz",
                    "archived_at": "2026-08-10T08:00:00Z",
                },
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
        assert reponse.json()["data"]["size_bytes"] == 5_000_000_000

    async def test_data_asset_refuse_un_chemin_local_expose(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        version = await self._creer_version(client, entetes_ecriture)
        reponse = await client.post(
            "/api/v1/resources",
            json={
                "type": "data_asset",
                "data": {
                    "dataset_version_id": version,
                    "format": "geotiff",
                    "size_bytes": 12,
                    "checksum": "a" * 64,
                    "storage_uri": "file:///srv/gsie/secret.tif",
                    "archived_at": "2026-08-10T08:00:00Z",
                },
            },
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 422, reponse.text
        assert any("storage_uri" in error for error in reponse.json()["detail"]["errors"])


class TestSourceCitable:
    """Une source qui ne peut pas être citée n'est pas une source (CON-005).

    `SourceReference` — le format qu'attend toute conclusion pour citer —
    exige un auteur. Sans lui, une conclusion invoquerait un document sans
    pouvoir dire qui l'a écrit : citable en apparence, invérifiable en fait.

    C'est ce qui bloquait la récupération des règles : aucune `SourceReference`
    du dépôt n'était construite depuis la base, faute de pouvoir l'être.
    """

    @staticmethod
    def _source(**champs: str) -> dict[str, Any]:
        base = {
            "title": "Catalogue des stations forestières",
            "subtype": "publication",
            "source_nature": "reference",
            "auteur": "CRPF Normandie",
            "date_publication": "2019",
        }
        base.update(champs)
        return base

    @pytest.mark.parametrize("manquant", ["auteur", "date_publication"])
    async def test_une_source_incitable_est_refusee(
        self, client: AsyncClient, manquant: str, entetes_ecriture: dict[str, str]
    ) -> None:
        data = {k: v for k, v in self._source().items() if k != manquant}

        reponse = await client.post(
            "/api/v1/resources",
            json={"type": "source", "data": data},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 422, reponse.text
        assert any(manquant in e for e in reponse.json()["detail"]["errors"])

    async def test_une_source_complete_est_acceptee(
        self, client: AsyncClient, entetes_ecriture: dict[str, str]
    ) -> None:
        """Témoin : c'est bien le manque qui refuse, pas le type `source`."""
        reponse = await client.post(
            "/api/v1/resources",
            json={"type": "source", "data": self._source()},
            headers=entetes_ecriture,
        )

        assert reponse.status_code == 201, reponse.text
