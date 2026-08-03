"""Contrats JSON stricts de la synchronisation GeoSylva."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeoSylvaParcelPayload(BaseModel):
    """Projection réseau d'une parcelle locale GeoSylva 2.4."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    forest_owner_id: str | None = Field(default=None, max_length=100)
    forest_id: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=300)
    surface_ha: float | None = Field(default=None, ge=0, le=10_000_000)
    shape: str | None = Field(default=None, max_length=100)
    slope_pct: float | None = Field(default=None, ge=0, le=1000)
    aspect: str | None = Field(default=None, max_length=100)
    access: str | None = Field(default=None, max_length=500)
    altitude_m: float | None = Field(default=None, ge=-500, le=10_000)
    objective_type: str | None = Field(default=None, max_length=100)
    objective_value: float | None = None
    tolerance_pct: float | None = Field(default=None, ge=0, le=100)
    sampling_mode: str | None = Field(default=None, max_length=100)
    sample_area_m2: float | None = Field(default=None, ge=0)
    target_species_csv: str | None = Field(default=None, max_length=20_000)
    srid: int | None = Field(default=None, ge=0, le=999_999)
    remarks: str | None = Field(default=None, max_length=20_000)
    municipality_code: str | None = Field(default=None, max_length=20)
    municipality_name: str | None = Field(default=None, max_length=300)
    cadastral_section: str | None = Field(default=None, max_length=50)
    cadastral_number: str | None = Field(default=None, max_length=100)
    cadastral_area_ha: float | None = Field(default=None, ge=0)
    ign_geometry_wkt: str | None = Field(default=None, max_length=500_000)
    cadastral_nature_code: str | None = Field(default=None, max_length=100)
    location_mode: str | None = Field(default=None, max_length=100)
    ser_code: str | None = Field(default=None, max_length=50)
    ser_name: str | None = Field(default=None, max_length=300)
    created_at_ms: int = Field(ge=0)
    updated_at_ms: int = Field(ge=0)


class GeoSylvaUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    base_version: int | None = Field(default=None, ge=1)
    client_updated_at: datetime
    parcel: GeoSylvaParcelPayload

    @field_validator("client_updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("client_updated_at doit inclure un fuseau horaire")
        return value


class GeoSylvaDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    base_version: int | None = Field(default=None, ge=1)
    client_updated_at: datetime

    @field_validator("client_updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("client_updated_at doit inclure un fuseau horaire")
        return value


class GeoSylvaParcelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str
    status: Literal["active", "deleted"]
    server_version: int
    client_updated_at: datetime
    server_updated_at: datetime
    parcel: GeoSylvaParcelPayload | None


class GeoSylvaParcelPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[GeoSylvaParcelResponse]
    page: int
    size: int
    total: int


GeoSylvaClientId = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$"),
]
