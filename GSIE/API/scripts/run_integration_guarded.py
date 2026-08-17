#!/usr/bin/env python3
"""Lance la suite d'intégration avec une porte Docker et un délai borné.

Le script ne démarre, n'arrête et ne supprime aucun conteneur. Il vérifie
seulement que le démon Docker répond, puis délègue la création de
l'infrastructure à la suite pytest/fixtures existante.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _charger_env(path: Path, environnement: dict[str, str]) -> None:
    """Charge un fichier ``KEY=VALUE`` sans écraser l'environnement appelant."""
    for ligne in path.read_text(encoding="utf-8").splitlines():
        contenu = ligne.strip()
        if not contenu or contenu.startswith("#") or "=" not in contenu:
            continue
        cle, valeur = contenu.split("=", 1)
        cle = cle.strip()
        valeur = valeur.strip()
        if cle and cle not in environnement:
            environnement[cle] = valeur


def _docker_est_disponible() -> bool:
    try:
        processus = subprocess.Popen(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except (FileNotFoundError, PermissionError, OSError):
        return False
    try:
        stdout, _ = processus.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        processus.kill()
        processus.communicate()
        return False
    return processus.returncode == 0 and bool(stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=2_400,
        help="durée maximale pytest (défaut : 40 minutes)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="nombre de workers pytest (défaut : 2, pour limiter la mémoire)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="fichier d'environnement optionnel relatif à GSIE/API",
    )
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds doit être positif")
    if args.workers <= 0:
        parser.error("--workers doit être positif")

    if not _docker_est_disponible():
        print("DOCKER_BLOCKED: le démon Docker ne répond pas en 30 secondes", file=sys.stderr)
        return 2

    api_root = Path(__file__).resolve().parents[1]
    environnement = os.environ.copy()
    if args.env_file is not None:
        env_file = args.env_file
        if not env_file.is_absolute():
            env_file = api_root / env_file
        if not env_file.is_file():
            print(f"ENV_FILE_MISSING: fichier introuvable: {env_file}", file=sys.stderr)
            return 2
        _charger_env(env_file, environnement)
    for cle, valeur in {
        "GSIE_ENVIRONMENT": "development",
        "GSIE_DATABASE_ROLE": "test",
        "GSIE_DATA_NAMESPACE": "gsie-test",
        "GSIE_AUTH_DEV_LOGIN_ENABLED": "false",
        "GSIE_AUTH_DEV_PASSWORD": "gsie-test-dev-password-change-me",
    }.items():
        environnement.setdefault(cle, valeur)
    # Un test qui saute silencieusement faute de Docker ne constitue pas une
    # preuve. La valeur appelante reste prioritaire pour les environnements CI.
    environnement.setdefault("GSIE_REQUIRE_DOCKER", "1")
    commande = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration",
        "-q",
        "--no-cov",
        "--tb=short",
        "--durations=30",
        "-n",
        str(args.workers),
    ]
    try:
        résultat = subprocess.run(
            commande,
            cwd=api_root,
            env=environnement,
            check=False,
            timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        print(
            f"INTEGRATION_TIMEOUT après {args.timeout_seconds} secondes",
            file=sys.stderr,
        )
        return 124
    return résultat.returncode


if __name__ == "__main__":
    raise SystemExit(main())
