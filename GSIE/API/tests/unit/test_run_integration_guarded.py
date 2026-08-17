"""Tests du garde-fou Docker de la campagne d'intégration."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from scripts import run_integration_guarded


def should_load_env_without_overriding_callers_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        "# commentaire\nGSIE_ENVIRONMENT=development\nGSIE_SECRET=depuis-fichier\n",
        encoding="utf-8",
    )
    environnement = {"GSIE_SECRET": "depuis-appelant"}

    run_integration_guarded._charger_env(env_file, environnement)

    assert environnement == {
        "GSIE_SECRET": "depuis-appelant",
        "GSIE_ENVIRONMENT": "development",
    }


def should_keep_test_runner_self_contained_without_env_file(monkeypatch) -> None:
    monkeypatch.setattr(run_integration_guarded, "_docker_est_disponible", lambda: False)
    monkeypatch.setattr(sys, "argv", ["run_integration_guarded"])

    assert run_integration_guarded.main() == 2


def should_reject_when_docker_process_cannot_start(monkeypatch) -> None:
    def _raise_permission(*args, **kwargs):
        raise PermissionError("docker inaccessible")

    monkeypatch.setattr(subprocess, "Popen", _raise_permission)

    assert run_integration_guarded._docker_est_disponible() is False


def should_reject_when_docker_process_expires(monkeypatch) -> None:
    class _Processus:
        returncode = None

        def communicate(self, *, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("docker", timeout)
            return ("", "")

        def kill(self):
            return None

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: _Processus())

    assert run_integration_guarded._docker_est_disponible() is False


def should_return_docker_blocked_code(monkeypatch) -> None:
    monkeypatch.setattr(run_integration_guarded, "_docker_est_disponible", lambda: False)
    monkeypatch.setattr(sys, "argv", ["run_integration_guarded"])

    assert run_integration_guarded.main() == 2
