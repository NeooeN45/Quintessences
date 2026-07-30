"""Tests du stockage objet — confinement local et fail-fast hors développement."""

from io import BytesIO

import pytest

from gsie_api.infrastructure import object_storage
from gsie_api.infrastructure.object_storage import LocalStorage


def should_refuse_local_fallback_in_production(monkeypatch) -> None:
    """La production ne doit jamais stocker silencieusement sur le disque local."""
    monkeypatch.setattr(object_storage._settings, "environment", "production")

    with pytest.raises(RuntimeError, match="S3"):
        object_storage.get_object_storage()


def should_refuse_local_fallback_in_staging(monkeypatch) -> None:
    """Le staging doit reproduire la topologie de stockage de production."""
    monkeypatch.setattr(object_storage._settings, "environment", "staging")

    with pytest.raises(RuntimeError, match="S3"):
        object_storage.get_object_storage()


@pytest.mark.asyncio
async def should_reject_path_traversal(tmp_path) -> None:
    """Une clé objet ne doit pas pouvoir sortir du répertoire configuré."""
    storage = LocalStorage(str(tmp_path / "objects"))

    with pytest.raises(ValueError, match="outside"):
        await storage.put("../outside.txt", BytesIO(b"secret"))


# --- Le confinement vaut sur *chaque* point d'entree ---

_CLES_HORS_RACINE = (
    "../outside.txt",
    "../../etc/passwd",
    "sous/dossier/../../../outside.txt",
)


def _operations(storage: LocalStorage, cle: str) -> dict[str, object]:
    """Toutes les méthodes publiques qui acceptent une clé, prêtes à appeler.

    Le dictionnaire est comparé à la surface réelle de la classe par
    `should_cover_every_key_accepting_method` : une méthode ajoutée sans
    contrôle de confinement fait tomber ce test-là.
    """
    return {
        "put": lambda: storage.put(cle, BytesIO(b"secret")),
        "get": lambda: storage.get(cle),
        "delete": lambda: storage.delete(cle),
        "exists": lambda: storage.exists(cle),
        "get_presigned_url": lambda: storage.get_presigned_url(cle),
    }


@pytest.mark.parametrize("cle", _CLES_HORS_RACINE)
@pytest.mark.parametrize(
    "operation",
    ["put", "get", "delete", "exists", "get_presigned_url"],
)
@pytest.mark.asyncio
async def should_reject_path_traversal_on_every_method(tmp_path, operation, cle) -> None:
    """Chaque méthode refuse une clé qui sort du répertoire configuré.

    Seul `put` était couvert. Les cinq méthodes passent aujourd'hui par le même
    `_resolve_key`, donc toutes sont protégées — mais un refactoring qui en
    contournerait une, en composant `self._base / key` sur place, n'aurait fait
    tomber aucun test hors de `put`. Or `get` fuit, et `delete` détruit.

    Trois formes de clé, dont une qui remonte depuis un sous-dossier : la
    résolution doit intervenir après normalisation, pas sur le préfixe.
    """
    storage = LocalStorage(str(tmp_path / "objects"))

    with pytest.raises(ValueError, match="outside"):
        await _operations(storage, cle)[operation]()  # type: ignore[operator]


def should_cover_every_key_accepting_method(tmp_path) -> None:
    """Le test précédent couvre toute la surface publique acceptant une clé.

    Sans ce contrôle, une méthode ajoutée à `LocalStorage` échapperait
    silencieusement au contrôle de confinement : la liste paramétrée ci-dessus
    resterait verte tout en ne couvrant plus tout. C'est la leçon du trou RBAC
    de `admin` — une liste écrite à la main reste aveugle à ce qu'elle oublie.
    """
    import inspect

    storage = LocalStorage(str(tmp_path / "objects"))
    publiques = {
        nom
        for nom, membre in inspect.getmembers(LocalStorage, inspect.isfunction)
        if not nom.startswith("_") and "key" in inspect.signature(membre).parameters
    }

    couvertes = set(_operations(storage, "k").keys())
    assert publiques == couvertes, (
        f"méthodes acceptant une clé mais non couvertes : {sorted(publiques - couvertes)} ; "
        f"couvertes mais disparues : {sorted(couvertes - publiques)}"
    )
