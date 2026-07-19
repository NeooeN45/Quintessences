"""Utilitaires JSON stricts et déterministes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StrictJsonError(ValueError):
    """Signale un JSON ambigu, invalide ou non canonisable."""


def _reject_constant(value: str) -> None:
    raise StrictJsonError(f"Constante JSON non finie interdite : {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJsonError(f"Clé JSON dupliquée : {key}")
        result[key] = value
    return result


def loads_strict(data: bytes | str) -> Any:
    """Charge du JSON en refusant doublons de clés, NaN et infinis."""

    try:
        return json.loads(
            data,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise StrictJsonError(f"JSON invalide : {exc}") from exc


def canonical_json(data: Any) -> bytes:
    """Produit la représentation JSON canonique utilisée pour la signature."""

    try:
        encoded = json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise StrictJsonError(f"Valeur non canonisable en JSON : {exc}") from exc
    return encoded.encode("utf-8")


def write_json_atomic(path: Path, data: Any, *, mode: int = 0o644) -> None:
    """Écrit un rapport JSON lisible, puis le publie par renommage atomique."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.chmod(mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
