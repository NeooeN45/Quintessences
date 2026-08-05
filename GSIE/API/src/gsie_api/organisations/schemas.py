"""Contrats JSON des organisations et workspaces GSIE."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SlugPattern = r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$"

OrganisationSlug = Annotated[str, Field(min_length=3, max_length=100, pattern=SlugPattern)]
WorkspaceSlug = Annotated[str, Field(min_length=3, max_length=100, pattern=SlugPattern)]
DisplayName = Annotated[str, Field(min_length=1, max_length=200)]
MemberRole = Literal["owner", "admin", "member"]


class OrganisationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: OrganisationSlug
    display_name: DisplayName


class OrganisationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    slug: str
    display_name: str
    status: Literal["active", "disabled"]
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class OrganisationPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OrganisationResponse]
    page: int
    size: int
    total: int


class WorkspaceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: WorkspaceSlug
    display_name: DisplayName


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    organisation_id: UUID
    slug: str
    display_name: str
    created_at: datetime
    updated_at: datetime


class WorkspacePage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WorkspaceResponse]
    page: int
    size: int
    total: int


class MemberInviteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    role: MemberRole = "member"


class MemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organisation_id: UUID
    account_id: UUID
    role: MemberRole
    invited_by: UUID
    joined_at: datetime
    revoked_at: datetime | None = None


class MemberPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MemberResponse]
    page: int
    size: int
    total: int
