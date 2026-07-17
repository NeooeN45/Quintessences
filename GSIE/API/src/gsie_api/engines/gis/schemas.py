"""Schémas Pydantic pour le GIS Engine.

Conforme à GIS_ENGINE.md §5 (contrat d'interface), avec un périmètre
v1 restreint à deux couches réelles et vérifiables sans clé API :
- `cadastre` — API Carto module Cadastre (IGN, apicarto.ign.fr)
- `altitude` — API de calcul altimétrique (IGN, data.geopf.fr)

Les autres couches du contrat (mnt, pente, exposition, hydrographie,
orthophoto, sol) restent hors périmètre v1 — pas de données simulées
pour les couches non implémentées (ADR-007).
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gsie_api.engines.evidence.schemas import SourceReference


class CoucheGeo(StrEnum):
    """Couches géospatiales du contrat GIS_ENGINE.md §5 — v1 implémente cadastre et altitude."""

    cadastre = "cadastre"
    altitude = "altitude"
    mnt = "mnt"
    pente = "pente"
    exposition = "exposition"
    hydrographie = "hydrographie"
    orthophoto = "orthophoto"
    sol = "sol"


class ParcelleCadastraleRequest(BaseModel):
    """Requête d'une parcelle cadastrale unique (API Carto Cadastre IGN)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    code_insee: str = Field(min_length=5, max_length=5, description="Code INSEE de la commune")
    section: str = Field(min_length=1, max_length=10, description="Section cadastrale (ex. AH)")
    numero: str = Field(min_length=1, max_length=10, description="Numéro de parcelle (ex. 0040)")


class AltitudeRequest(BaseModel):
    """Requête d'altitude pour un point (API de calcul altimétrique IGN)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID = Field(default_factory=uuid4)
    latitude: float = Field(ge=-90.0, le=90.0, description="WGS 84")
    longitude: float = Field(ge=-180.0, le=180.0, description="WGS 84")


class GeoLayer(BaseModel):
    """Une couche géospatiale (GIS_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    nom: CoucheGeo
    type: str = Field(description="raster | vecteur | mesure")
    valeurs: dict[str, Any] = Field(
        description="Structure selon type (GeoJSON, grille, ou valeur ponctuelle)"
    )
    unite: str | None = None
    resolution: str | None = None
    source: SourceReference
    date_maj: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GeoData(BaseModel):
    """Résultat d'une requête géospatiale (GIS_ENGINE.md §5)."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    place_id: UUID | None = Field(default=None, description="UUID de la resource `place` persistée")
    couches: list[GeoLayer]
    source: SourceReference
    date_donnees: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mode: str = Field(default="en_ligne", description="en_ligne | hors_ligne | degrade")


class StationCharacteristics(BaseModel):
    """Caractéristiques stationnelles calculées (GIS_ENGINE.md §5) — v1 : altitude uniquement."""

    model_config = ConfigDict(extra="forbid")

    requete_id: UUID
    altitude_m: float
    latitude: float
    longitude: float
    source: SourceReference
