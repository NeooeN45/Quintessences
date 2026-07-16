"""Infrastructure models — registry des 73 types du métamodèle v6.2.

Importe tous les modèles pour qu'ils soient enregistrés dans RESOURCE_TYPES
via le décorateur @register_type. L'import de ce module suffit à peupler
le registry pour le CRUD générique.
"""

from gsie_api.infrastructure.models.base import (  # noqa: F401
    Base,
    ResourceModel,
    RESOURCE_TYPES,
    TimestampMixin,
    register_type,
)

# Import de tous les domaines — chaque import enregistre les types dans RESOURCE_TYPES
from gsie_api.infrastructure.models import provenance  # noqa: F401
from gsie_api.infrastructure.models import assertion  # noqa: F401
from gsie_api.infrastructure.models import observation  # noqa: F401
from gsie_api.infrastructure.models import prov  # noqa: F401
from gsie_api.infrastructure.models import spatial_temporal  # noqa: F401
from gsie_api.infrastructure.models import temporal_engine  # noqa: F401
from gsie_api.infrastructure.models import models_ai  # noqa: F401
from gsie_api.infrastructure.models import ecology  # noqa: F401
from gsie_api.infrastructure.models import reasoning  # noqa: F401
from gsie_api.infrastructure.models import governance  # noqa: F401
from gsie_api.infrastructure.models import dynamics  # noqa: F401
from gsie_api.infrastructure.models import fair_rgpd  # noqa: F401
from gsie_api.infrastructure.models import junctions  # noqa: F401 — 17 tables de jonction n:m
from gsie_api.infrastructure.models import outbox  # noqa: F401 — Outbox/Inbox (ADR-005)

__all__ = [
    "Base",
    "ResourceModel",
    "RESOURCE_TYPES",
    "TimestampMixin",
    "register_type",
]
