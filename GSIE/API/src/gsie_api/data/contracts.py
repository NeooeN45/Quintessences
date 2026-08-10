"""Primitives déterministes du contrat Data Registry RFC-0038.

Ce module ne fait aucun accès réseau ou base de données. Il porte les règles
qui doivent rester identiques entre le service Registry, les workers et les
clients : vocabulaire de domaines, normalisation et curseurs de pagination.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

DOMAIN_VOCABULARY_VERSION = "2026-08-10"

# Vocabulaire initial versionné. Une extension doit changer la version afin de
# rendre les décisions historiques rejouables.
DOMAIN_VOCABULARY = MappingProxyType(
    {
        "biodiversity": "Biodiversité",
        "botany": "Botanique",
        "climate": "Climat",
        "elevation": "Élévation",
        "forest_inventory": "Inventaire forestier",
        "gis": "Information géographique",
        "hydrology": "Hydrologie",
        "land_cover": "Occupation du sol",
        "pedology": "Pédologie",
        "remote_sensing": "Télédétection",
        "soil_moisture": "Humidité des sols",
        "weather": "Météorologie",
        "water_quality": "Qualité de l'eau",
    }
)

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
_CURSOR_MAX_LENGTH = 512


@dataclass(frozen=True, slots=True)
class CursorPayload:
    """Position opaque d'une page triée par date puis identifiant."""

    created_at: datetime
    resource_id: UUID
    filters_hash: str


def normalize_slug(value: str) -> str:
    """Normalise et valide l'identité lisible d'un dataset."""
    if not isinstance(value, str):
        raise ValueError("Le slug doit être une chaîne")
    normalized = value.strip().lower()
    if len(normalized) > 200 or not _SLUG_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Le slug doit respecter ^[a-z0-9]+(?:[-_][a-z0-9]+)*$ et 200 caractères maximum"
        )
    return normalized


def normalize_keywords(values: list[str] | tuple[str, ...] | None) -> list[str]:
    """Nettoie une liste de tags sans réordonner ni dupliquer les valeurs."""
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError("Chaque tag doit être une chaîne")
        item = " ".join(value.strip().lower().split())
        if not item:
            continue
        if len(item) > 100:
            raise ValueError("Un tag ne peut pas dépasser 100 caractères")
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    if len(normalized) > 50:
        raise ValueError("Un dataset ne peut pas porter plus de 50 tags")
    return normalized


def validate_domain(value: str) -> str:
    """Valide une clé du vocabulaire contrôlé et versionné."""
    if not isinstance(value, str):
        raise ValueError("Le domaine doit être une chaîne")
    normalized = value.strip().lower()
    if normalized not in DOMAIN_VOCABULARY:
        raise ValueError(f"Domaine GSIE inconnu : {normalized or '(vide)'}")
    return normalized


def filters_hash(filters: object) -> str:
    """Construit une empreinte stable des filtres de pagination."""
    encoded = json.dumps(filters, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()[:32]


def encode_cursor(created_at: datetime, resource_id: UUID, *, filters_hash: str) -> str:
    """Encode une position en jeton URL-safe non interprétable par le client."""
    if created_at.tzinfo is None:
        raise ValueError("Un curseur exige une date avec fuseau horaire")
    payload = {
        "v": 1,
        "created_at": created_at.isoformat(),
        "resource_id": str(resource_id),
        "filters_hash": filters_hash,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(token: str) -> CursorPayload:
    """Décode et valide un curseur reçu d'un client."""
    if not isinstance(token, str) or not token or len(token) > _CURSOR_MAX_LENGTH:
        raise ValueError("Curseur invalide")
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.b64decode(padded.encode(), altchars=b"-_", validate=True)
        value = json.loads(raw.decode())
        if not isinstance(value, dict):
            raise ValueError("structure")
        if value.get("v") != 1:
            raise ValueError("version")
        created_at = datetime.fromisoformat(value["created_at"])
        resource_id = UUID(value["resource_id"])
        filters_value = value["filters_hash"]
        if not isinstance(filters_value, str) or not re.fullmatch(r"[0-9a-f]{32}", filters_value):
            raise ValueError("empreinte")
        if created_at.tzinfo is None:
            raise ValueError("fuseau")
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        binascii.Error,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError("Curseur invalide") from exc
    return CursorPayload(created_at, resource_id, filters_value)
