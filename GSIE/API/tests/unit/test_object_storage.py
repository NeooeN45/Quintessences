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
