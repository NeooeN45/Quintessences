"""Client pour les API Wikimedia (Commons + Wikipédia).

Deux endpoints documentés et vérifiés manuellement le 2026-08-01 :

- Wikimedia Commons API : recherche d'images par nom d'espèce
  GET https://commons.wikimedia.org/w/api.php?action=query&generator=search
      &gsrsearch={species}&gsrnamespace=6&prop=imageinfo
      &iiprop=url|extmetadata&iiurlwidth=400&format=json&formatversion=2
  → URL image, thumbnail, licence CC-BY-SA, photographe, description

- Wikipédia API (EN) : extrait d'article par nom d'espèce
  GET https://en.wikipedia.org/w/api.php?action=query&prop=extracts
      &exintro=1&explaintext=1&titles={species}&format=json&redirects=1
  → extrait en plain text (premier paragraphe)

L'API EN est utilisée car plus exhaustive pour les espèces que la FR
(vérifié sur Abies alba : extrait EN ~300 chars, extrait FR vide).

ADR-009 : aucune valeur inventée. Si l'API retourne un extrait vide ou
aucune image, le client retourne None — pas de description fallback.
"""

from __future__ import annotations

from typing import Any

from gsie_api.shared.http_client import ResilientHttpClient

_COMMONS_BASE_URL = "https://commons.wikimedia.org"
_WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"
_WIKIPEDIA_FR_BASE_URL = "https://fr.wikipedia.org"
_DEFAULT_TIMEOUT = 30.0
_THUMBNAIL_WIDTH = 400
_MAX_IMAGES = 3
# Seuil de qualité d'une description (en caractères). En dessous, la
# description est considérée comme un stub et non stockée (audit P2-1).
_MIN_DESCRIPTION_LENGTH = 100


class WikimediaClientError(Exception):
    """Erreur lors d'un appel aux API Wikimedia (réseau, réponse inattendue)."""


class WikimediaClient(ResilientHttpClient):
    """Client pour les API Wikimedia Commons + Wikipédia.

    Aucune authentification requise (API publique, rate limit 200 req/s
    avec User-Agent obligatoire — voir https://meta.wikimedia.org/wiki/User-Agent_policy).
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return WikimediaClientError

    @property
    def base_url(self) -> str:
        return _COMMONS_BASE_URL

    def auth_headers(self) -> dict[str, str]:
        """User-Agent obligatoire selon la politique Wikimedia."""
        return {
            "User-Agent": "GSIE/1.0 (https://github.com/NeooeN45/Quintessences; contact@gsie.fr)",
        }

    async def search_species_images(
        self,
        scientific_name: str,
        *,
        limit: int = _MAX_IMAGES,
    ) -> list[dict[str, str]]:
        """Recherche des images d'une espèce sur Wikimedia Commons.

        Args:
            scientific_name: nom scientifique (ex. "Abies alba")
            limit: nombre maximum d'images à retourner

        Returns:
            Liste de dictionnaires avec : url, thumb_url, title, license,
            photographer, description_url. Vide si aucune image trouvée.

        Raises:
            WikimediaClientError: en cas d'erreur réseau ou de réponse inattendue.
        """
        data: dict[str, Any] = await self._get_json(
            "/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": scientific_name,
                "gsrnamespace": "6",  # namespace File:
                "gsrlimit": str(limit),
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": str(_THUMBNAIL_WIDTH),
                "format": "json",
                "formatversion": "2",
            },
            error_label=f"de la recherche Commons pour '{scientific_name}'",
        )

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return []

        images: list[dict[str, str]] = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            image_info_list = page.get("imageinfo", [])
            if not image_info_list:
                continue
            info = image_info_list[0]
            extmeta = info.get("extmetadata", {})

            images.append(
                {
                    "url": str(info.get("url", "")),
                    "thumb_url": str(info.get("thumburl", "")),
                    "title": str(page.get("title", "")),
                    "license": str(extmeta.get("LicenseShortName", {}).get("value", "")),
                    "photographer": _strip_html(str(extmeta.get("Artist", {}).get("value", ""))),
                    "description_url": str(info.get("descriptionurl", "")),
                }
            )

        return images

    async def get_species_description(
        self,
        scientific_name: str,
        *,
        language: str = "en",
    ) -> str | None:
        """Récupère l'extrait introductif de l'article Wikipédia.

        Args:
            scientific_name: nom scientifique (ex. "Abies alba")
            language: code langue ISO 639-1 ("en" par défaut, "fr" pour FR)

        Returns:
            L'extrait en plain text, ou None si aucun article n'existe.

        Raises:
            WikimediaClientError: en cas d'erreur réseau ou de réponse inattendue.
        """
        base_url = _WIKIPEDIA_FR_BASE_URL if language == "fr" else _WIKIPEDIA_BASE_URL
        data: dict[str, Any] = await self._get_json(
            f"{base_url}/w/api.php",
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": "1",
                "explaintext": "1",
                "titles": scientific_name,
                "format": "json",
                "redirects": "1",
            },
            error_label=f"de l'extrait Wikipédia ({language}) pour '{scientific_name}'",
        )

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        # pages est un dict {pageid: {...}} — prendre la première page
        first_page: dict[str, Any] = next(iter(pages.values()), {})
        extract = first_page.get("extract", "")
        if not extract:
            return None
        return str(extract).strip()

    async def get_species_description_with_fallback(
        self,
        scientific_name: str,
    ) -> tuple[str | None, str]:
        """Récupère la description EN, puis fallback FR si EN absent/trop court.

        Args:
            scientific_name: nom scientifique (ex. "Abies alba")

        Returns:
            Tuple (description, langue) — description peut être None,
            langue est "en", "fr" ou "" si aucune trouvée.
        """
        # 1. Tentative EN
        desc_en = await self.get_species_description(scientific_name, language="en")
        if desc_en and len(desc_en) >= _MIN_DESCRIPTION_LENGTH:
            return desc_en, "en"

        # 2. Fallback FR si EN absent ou trop court
        desc_fr = await self.get_species_description(scientific_name, language="fr")
        if desc_fr and len(desc_fr) >= _MIN_DESCRIPTION_LENGTH:
            return desc_fr, "fr"

        # 3. Retourner EN même si court (mieux que rien)
        if desc_en:
            return desc_en, "en"
        return None, ""


def _strip_html(html: str) -> str:
    """Retire les balises HTML d'une chaîne (photographe Commons contient des <a>)."""
    import re

    if not html:
        return ""
    # Retire les balises <a>...</a> et autres tags HTML
    clean = re.sub(r"<[^>]+>", "", html)
    return clean.strip()
