"""Contrat statique du smoke PostgreSQL + MinIO Data Registry."""

from pathlib import Path


def test_smoke_is_bounded_and_cleans_object_storage() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "smoke_data_registry_infrastructure.py"
    ).read_text(encoding="utf-8")

    assert "storage.put" in script
    assert "storage.get" in script
    assert "hashlib.sha256" in script
    assert "storage.delete" in script
    assert '"fetch_performed": False' in script
