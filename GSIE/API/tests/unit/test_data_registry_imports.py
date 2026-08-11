"""Non-régression des directions d'import du Data Registry."""

from __future__ import annotations

import subprocess
import sys


def test_should_import_resources_service_before_data_package() -> None:
    """Un processus froid doit pouvoir charger ResourceService en premier."""

    command = (
        "import gsie_api.resources.service; "
        "import gsie_api.data.lifecycle; "
        "import gsie_api.data.manifest_application"
    )
    result = subprocess.run(  # noqa: S603 - exécutable Python courant, sans shell
        [sys.executable, "-c", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
