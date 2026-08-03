"""Client HTTP vers l'API PlantNet — identification de plantes par image.

API PlantNet (https://my.plantnet.org/) — 78 810 espèces identifiables
(veille techno 2026-08-02, RFC-0031 action 8).

Endpoint principal :
    POST /v2/identify/{project}?api-key=KEY
    multipart/form-data : images + organs

L'authentification se fait via la clé API passée en paramètre de requête
(convention PlantNet, pas dans le header).
"""

from __future__ import annotations

from typing import Any

from gsie_api.core.config import get_settings
from gsie_api.shared.http_client import ResilientHttpClient

_BASE_URL = "https://my-api.plantnet.org"
_IDENTIFY_URL = f"{_BASE_URL}/v2/identify/all"
_DEFAULT_TIMEOUT = 60.0  # identification d'image = plus lent qu'un GET simple


class PlantNetClientError(Exception):
    """Erreur lors d'un appel à l'API PlantNet (réseau, réponse inattendue)."""


class PlantNetClient(ResilientHttpClient):
    """Client HTTP pour l'API PlantNet — identification d'espèces par image.

    Nécessite une clé API PlantNet (PLANTNET_API_KEY dans l'environnement).
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        super().__init__(timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return PlantNetClientError

    @property
    def base_url(self) -> str:
        return _BASE_URL

    def auth_headers(self) -> dict[str, str]:
        # PlantNet utilise la clé en query param, pas en header.
        # La clé est ajoutée dans les params de chaque appel.
        return {}

    def _api_key(self) -> str:
        key = get_settings().plantnet_api_key
        if not key:
            raise PlantNetClientError(
                "Échec de l'identification PlantNet : PLANTNET_API_KEY non configurée"
            )
        return key

    async def identify(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        organ: str = "auto",
        project: str = "all",
        lang: str = "fr",
        nb_results: int = 5,
    ) -> dict[str, Any] | None:
        """Identifie une plante à partir d'une image.

        Args:
            image_bytes: contenu binaire de l'image (JPG ou PNG).
            filename: nom du fichier pour l'upload.
            organ: organe de la plante — auto, flower, leaf, fruit, bark, habit.
            project: projet PlantNet (all, weurope, canada, etc.).
            lang: langue des noms communs (fr, en, etc.).
            nb_results: nombre de résultats à retourner.

        Returns:
            La réponse PlantNet avec bestMatch et results, ou None si
            aucune identification n'a pu être faite.

        Raises:
            PlantNetClientError: en cas d'erreur réseau, HTTP, ou clé manquante.
        """
        data: dict[str, Any] = await self._post_multipart_json(
            f"/v2/identify/{project}",
            data={"organs": organ, "nb-results": nb_results},
            files=[("images", (filename, image_bytes, "image/jpeg"))],
            params={"api-key": self._api_key(), "lang": lang},
            error_label="de l'identification PlantNet",
        )
        if not data.get("results"):
            return None
        return data
