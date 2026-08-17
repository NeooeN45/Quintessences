"""Client HTTP vers l'API de téléchargement de la Géoplateforme IGN.

L'API de téléchargement permet de découvrir et télécharger des fichiers
de produits IGN (BD Forêt, BD TOPO Express, ADMIN-EXPRESS-COG, LiDAR HD,
etc.) conformément au format Atom RFC 4287.

Documentation :
    https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/telechargement/

Quatre méthodes :
- **GetCapabilities** : lister les ressources (produits) disponibles
- **GetResource** : lister les dossiers d'une ressource (jeux de données)
- **GetSubResource** : lister les fichiers d'un dossier
- **Download** : télécharger un fichier (binaire)

Aucune authentification requise (open data, licence Etalab 2.0).
Limite : 10 requêtes/s/IP. Résultats paginés (`page`, `limit` max 50).

Les réponses sont au format Atom XML — pas JSON. Le parsing utilise
`defusedxml.ElementTree` avec gestion des namespaces Atom
et Géoplateforme (`gpf_dl`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from defusedxml import ElementTree

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

from gsie_api.shared.http_client import ResilientHttpClient

_TELECHARGEMENT_BASE_URL = "https://data.geopf.fr/telechargement"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_LIMIT = 50

# Namespaces Atom XML de la Géoplateforme.
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "gpf_dl": "https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd",
    "georss": "http://www.georss.org/georss",
}


class TelechargementClientError(Exception):
    """Erreur lors d'un appel à l'API de téléchargement Géoplateforme."""


@dataclass(frozen=True)
class RessourceTelechargement:
    """Une ressource (produit IGN) listée par GetCapabilities."""

    nom: str
    url_resource: str
    description: str
    date_maj: str
    zones: list[str]
    formats: list[str]


@dataclass(frozen=True)
class DossierTelechargement:
    """Un dossier (jeu de données) listé par GetResource."""

    nom: str
    url_subresource: str
    date_maj: str
    zone: str
    format: str
    date_edition: str


@dataclass(frozen=True)
class FichierTelechargement:
    """Un fichier téléchargeable listé par GetSubResource."""

    url_download: str
    taille_octets: int
    checksum_md5: str
    mime_types: list[str]


@dataclass(frozen=True)
class PageTelechargement:
    """Une page de résultats paginés avec métadonnées de pagination."""

    total_entries: int
    page: int
    page_size: int
    page_count: int


def _parse_feed_metadata(root: Element) -> PageTelechargement:
    """Extrait les métadonnées de pagination du feed Atom."""
    return PageTelechargement(
        total_entries=int(root.get(f"{{{_NS['gpf_dl']}}}totalentries", "0")),
        page=int(root.get(f"{{{_NS['gpf_dl']}}}page", "1")),
        page_size=int(root.get(f"{{{_NS['gpf_dl']}}}pagesize", "0")),
        page_count=int(root.get(f"{{{_NS['gpf_dl']}}}pagecount", "0")),
    )


def _parse_ressource(entry: Element) -> RessourceTelechargement:
    """Parse une <entry> de GetCapabilities en RessourceTelechargement."""
    nom = entry.findtext("atom:title", "", _NS) or ""
    link_elem = entry.find("atom:link", _NS)
    url_resource = link_elem.get("href", "") if link_elem is not None else ""
    description = entry.findtext("atom:content", "", _NS) or ""
    date_maj = entry.findtext("atom:updated", "", _NS) or ""
    zones = [z.get("term", "") for z in entry.findall("gpf_dl:zone", _NS)]
    formats = [f.get("term", "") for f in entry.findall("gpf_dl:format", _NS)]
    return RessourceTelechargement(
        nom=nom,
        url_resource=url_resource,
        description=description,
        date_maj=date_maj,
        zones=zones,
        formats=formats,
    )


def _parse_dossier(entry: Element) -> DossierTelechargement:
    """Parse une <entry> de GetResource en DossierTelechargement."""
    nom = entry.findtext("atom:title", "", _NS) or ""
    link_elem = entry.find("atom:link", _NS)
    url_subresource = link_elem.get("href", "") if link_elem is not None else ""
    date_maj = entry.findtext("atom:updated", "", _NS) or ""
    zone_elem = entry.find("gpf_dl:zone", _NS)
    zone = zone_elem.get("term", "") if zone_elem is not None else ""
    format_elem = entry.find("gpf_dl:format", _NS)
    fmt = format_elem.get("term", "") if format_elem is not None else ""
    date_edition = entry.findtext("gpf_dl:editionDate", "", _NS) or ""
    return DossierTelechargement(
        nom=nom,
        url_subresource=url_subresource,
        date_maj=date_maj,
        zone=zone,
        format=fmt,
        date_edition=date_edition,
    )


def _parse_fichier(entry: Element) -> FichierTelechargement:
    """Parse une <entry> de GetSubResource en FichierTelechargement."""
    link_elem = entry.find("atom:link", _NS)
    url_download = link_elem.get("href", "") if link_elem is not None else ""
    taille_str = link_elem.get(f"{{{_NS['gpf_dl']}}}length", "0") if link_elem is not None else "0"
    try:
        taille_octets = int(taille_str)
    except (TypeError, ValueError):
        taille_octets = 0
    checksum = entry.findtext("atom:content", "", _NS) or ""
    mime_types = [mt.text or "" for mt in entry.findall("gpf_dl:mime_type", _NS)]
    return FichierTelechargement(
        url_download=url_download,
        taille_octets=taille_octets,
        checksum_md5=checksum,
        mime_types=mime_types,
    )


class TelechargementClient(ResilientHttpClient):
    """Client HTTP pour l'API de téléchargement Géoplateforme IGN — sans auth."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return TelechargementClientError

    @property
    def base_url(self) -> str:
        return _TELECHARGEMENT_BASE_URL

    async def get_capabilities(
        self,
        *,
        page: int = 1,
        limit: int = _DEFAULT_LIMIT,
        zone: str | None = None,
        format: str | None = None,
    ) -> tuple[list[RessourceTelechargement], PageTelechargement]:
        """Liste les ressources disponibles (GetCapabilities).

        Returns:
            Un tuple (liste des ressources, métadonnées de pagination).

        Raises:
            TelechargementClientError: en cas d'erreur réseau, HTTP, ou XML malformé.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if zone is not None:
            params["zone"] = zone
        if format is not None:
            params["format"] = format
        body = await self._get_text(
            "/capabilities",
            params=params,
            error_label="de l'appel GetCapabilities Géoplateforme",
        )
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as exc:
            raise TelechargementClientError(
                f"Échec du parsing XML GetCapabilities : {exc}"
            ) from exc
        entries = root.findall("atom:entry", _NS)
        ressources = [_parse_ressource(e) for e in entries]
        return ressources, _parse_feed_metadata(root)

    async def get_resource(
        self,
        resource_name: str,
        *,
        page: int = 1,
        limit: int = _DEFAULT_LIMIT,
        zone: str | None = None,
        format: str | None = None,
    ) -> tuple[list[DossierTelechargement], PageTelechargement]:
        """Liste les dossiers d'une ressource (GetResource).

        Raises:
            TelechargementClientError: en cas d'erreur réseau, HTTP, ou XML malformé.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if zone is not None:
            params["zone"] = zone
        if format is not None:
            params["format"] = format
        body = await self._get_text(
            f"/resource/{resource_name}",
            params=params,
            error_label=f"de l'appel GetResource {resource_name}",
        )
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as exc:
            raise TelechargementClientError(
                f"Échec du parsing XML GetResource {resource_name} : {exc}"
            ) from exc
        entries = root.findall("atom:entry", _NS)
        dossiers = [_parse_dossier(e) for e in entries]
        return dossiers, _parse_feed_metadata(root)

    async def get_subresource(
        self,
        resource_name: str,
        subresource_name: str,
        *,
        page: int = 1,
        limit: int = _DEFAULT_LIMIT,
    ) -> tuple[list[FichierTelechargement], PageTelechargement]:
        """Liste les fichiers d'un dossier (GetSubResource).

        Raises:
            TelechargementClientError: en cas d'erreur réseau, HTTP, ou XML malformé.
        """
        body = await self._get_text(
            f"/resource/{resource_name}/{subresource_name}",
            params={"page": page, "limit": limit},
            error_label=f"de l'appel GetSubResource {resource_name}/{subresource_name}",
        )
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as exc:
            raise TelechargementClientError(
                f"Échec du parsing XML GetSubResource {resource_name}/{subresource_name} : {exc}"
            ) from exc
        entries = root.findall("atom:entry", _NS)
        fichiers = [_parse_fichier(e) for e in entries]
        return fichiers, _parse_feed_metadata(root)

    async def download_file(
        self,
        resource_name: str,
        subresource_name: str,
        file_name: str,
    ) -> bytes:
        """Télécharge un fichier binaire (Download).

        Raises:
            TelechargementClientError: en cas d'erreur réseau ou HTTP.
        """
        return await self._get_bytes(
            f"/download/{resource_name}/{subresource_name}/{file_name}",
            error_label=f"du téléchargement {resource_name}/{subresource_name}/{file_name}",
        )
