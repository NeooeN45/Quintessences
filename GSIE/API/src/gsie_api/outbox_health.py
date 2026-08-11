"""Healthcheck léger du worker outbox, sans charger l'application GSIE."""

import math
import os
import time
from pathlib import Path

DEFAULT_HEARTBEAT_PATH = "/tmp/gsie-outbox-worker.heartbeat"
DEFAULT_MAX_AGE_SECONDS = 30.0


def _heartbeat_path(path: str | None) -> Path:
    configured = path or os.getenv("GSIE_OUTBOX_HEALTHCHECK_PATH")
    return Path(configured or DEFAULT_HEARTBEAT_PATH)


def _maximum_age(max_age_seconds: float | None) -> float:
    try:
        maximum = (
            max_age_seconds
            if max_age_seconds is not None
            else float(
                os.getenv(
                    "GSIE_OUTBOX_HEALTHCHECK_MAX_AGE_SECONDS",
                    str(DEFAULT_MAX_AGE_SECONDS),
                )
            )
        )
    except ValueError:
        return -1.0
    return maximum if math.isfinite(maximum) and 2.0 <= maximum <= 300.0 else -1.0


def write_worker_heartbeat(path: str | None = None) -> None:
    """Écrit atomiquement le battement d'un cycle outbox réussi."""
    heartbeat = _heartbeat_path(path)
    temporary = heartbeat.with_suffix(f"{heartbeat.suffix}.tmp")
    temporary.touch(exist_ok=True)
    temporary.replace(heartbeat)


def worker_heartbeat_is_fresh(
    path: str | None = None,
    *,
    max_age_seconds: float | None = None,
    now_epoch: float | None = None,
) -> bool:
    """Indique si le worker a achevé récemment un cycle sans erreur."""
    maximum = _maximum_age(max_age_seconds)
    if maximum <= 0:
        return False
    now = time.time() if now_epoch is None else now_epoch
    try:
        age = max(now - _heartbeat_path(path).stat().st_mtime, 0.0)
    except OSError:
        return False
    return age <= maximum


def main() -> None:
    """Retourne un code exploitable directement par Docker."""
    raise SystemExit(0 if worker_heartbeat_is_fresh() else 1)


if __name__ == "__main__":
    main()
