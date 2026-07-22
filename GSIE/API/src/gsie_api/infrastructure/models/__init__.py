"""Infrastructure models — registry des types du métamodèle v6.2.

Importe tous les modèles pour qu'ils soient enregistrés dans RESOURCE_TYPES
via le décorateur @register_type. L'import de ce module suffit à peupler
le registry pour le CRUD générique.

Le registre RESOURCE_TYPES est la source exécutable du nombre de types.
Cette documentation ne recopie volontairement pas ce total, qui évolue avec
les RFC métier.
"""

# Import de tous les domaines — chaque import enregistre les types dans RESOURCE_TYPES
from gsie_api.infrastructure.models import (
    assertion,  # noqa: F401
    business,  # noqa: F401 — 7 types métier (audit ONF/CNPF)
    dynamics,  # noqa: F401
    ecology,  # noqa: F401
    fair_rgpd,  # noqa: F401
    forestry,  # noqa: F401 — types RFC-0016 (schéma forestier spécialisé)
    governance,  # noqa: F401
    identification,  # noqa: F401 — 3 types RFC-0018 (identification botanique Pl@ntNet)
    junctions,  # noqa: F401 — 17 tables de jonction n:m
    models_ai,  # noqa: F401
    observation,  # noqa: F401
    outbox,  # noqa: F401 — Outbox/Inbox (ADR-005)
    prov,  # noqa: F401
    provenance,  # noqa: F401
    reasoning,  # noqa: F401
    spatial_temporal,  # noqa: F401
    temporal_engine,  # noqa: F401
)
from gsie_api.infrastructure.models.base import (  # noqa: F401
    RESOURCE_TYPES,
    Base,
    ResourceModel,
    TimestampMixin,
    register_type,
)

__all__ = [
    "Base",
    "ResourceModel",
    "RESOURCE_TYPES",
    "TimestampMixin",
    "register_type",
]
