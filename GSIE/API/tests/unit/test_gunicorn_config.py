"""Tests de la configuration de recyclage Gunicorn."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

CONFIG_PATH = Path(__file__).parents[2] / "gunicorn.conf.py"


def _load_config() -> dict[str, object]:
    return runpy.run_path(str(CONFIG_PATH))


def test_recycling_defaults_are_strongly_desynchronized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GSIE_GUNICORN_MAX_REQUESTS", raising=False)
    monkeypatch.delenv("GSIE_GUNICORN_MAX_REQUESTS_JITTER", raising=False)

    config = _load_config()

    assert config["max_requests"] == 5000
    assert config["max_requests_jitter"] == 5000


def test_recycling_thresholds_can_be_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GSIE_GUNICORN_MAX_REQUESTS", "7000")
    monkeypatch.setenv("GSIE_GUNICORN_MAX_REQUESTS_JITTER", "3000")

    config = _load_config()

    assert config["max_requests"] == 7000
    assert config["max_requests_jitter"] == 3000


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("GSIE_GUNICORN_MAX_REQUESTS", "0"),
        ("GSIE_GUNICORN_MAX_REQUESTS_JITTER", "-1"),
    ],
)
def test_recycling_rejects_non_positive_values(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="doit être strictement positif"):
        _load_config()
