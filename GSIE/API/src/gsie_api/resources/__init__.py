"""Resources package — CRUD générique pour les 73 types du métamodèle v6.2."""

from gsie_api.resources.router import router as resources_router
from gsie_api.resources.schemas import (
    ResourceCreate,
    ResourceListResponse,
    ResourceRead,
    ResourceTypesResponse,
    ResourceUpdate,
)
from gsie_api.resources.service import ResourceService

__all__ = [
    "resources_router",
    "ResourceService",
    "ResourceCreate",
    "ResourceRead",
    "ResourceUpdate",
    "ResourceListResponse",
    "ResourceTypesResponse",
]
