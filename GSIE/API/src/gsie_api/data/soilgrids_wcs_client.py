"""Client WCS SoilGrids borné et compatible avec le contrat FETCH GSIE."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from gsie_api.data.adapters import AdapterFetchResult, AdapterSecurityError
from gsie_api.data.soilgrids_wcs_policy import (
    SOILGRIDS_WCS_ENDPOINT,
    SoilGridsWcsRequest,
)
from gsie_api.shared.http_client import ResilientHttpClient, valider_url_egress

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SoilGridsWcsClientError(Exception):
    """Erreur réseau ou réponse invalide du service WCS SoilGrids."""


class SoilGridsWcsClient(ResilientHttpClient):
    """Client ISRIC WCS sans dépendance au REST bêta suspendu.

    Les métadonnées de santé passent par le client HTTP résilient commun.
    Les couvertures sont ouvertes en streaming pour que le worker FETCH puisse
    appliquer ses bornes de taille, MIME et checksum sans charger le GeoTIFF
    en mémoire.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)

    @property
    def exception_class(self) -> type[Exception]:
        return SoilGridsWcsClientError

    @property
    def base_url(self) -> str:
        return SOILGRIDS_WCS_ENDPOINT

    async def probe(self) -> None:
        """Vérifie le service WCS sans exécuter de GetCoverage."""

        payload = await self._get_bytes(
            "",
            params={"SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCapabilities"},
            error_label="de la sonde WCS SoilGrids",
        )
        if not payload:
            raise SoilGridsWcsClientError("La réponse GetCapabilities SoilGrids est vide")

    @staticmethod
    def _parameters(
        request: SoilGridsWcsRequest,
    ) -> list[tuple[str, str | int | float | bool | None]]:
        parameters: list[tuple[str, str | int | float | bool | None]] = []
        for key, value in request.parameters.items():
            if isinstance(value, tuple):
                parameters.extend((key, item) for item in value)
            else:
                parameters.append((key, value))
        return parameters

    async def fetch_coverage(
        self,
        request: SoilGridsWcsRequest,
        *,
        timeout_seconds: float,
        max_bytes: int,
    ) -> AdapterFetchResult:
        """Ouvre un GetCoverage WCS et retourne un flux à fermeture garantie."""

        url = SOILGRIDS_WCS_ENDPOINT
        try:
            valider_url_egress(url)
        except ValueError as exc:
            raise SoilGridsWcsClientError(f"Échec du fetch WCS SoilGrids : {exc}") from exc

        client = httpx.AsyncClient(
            timeout=min(self._timeout, timeout_seconds),
            follow_redirects=False,
            verify=True,
        )
        try:
            response = await client.send(
                client.build_request("GET", url, params=self._parameters(request)),
                stream=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            await client.aclose()
            raise SoilGridsWcsClientError(f"Échec du fetch WCS SoilGrids : {exc}") from exc

        length_header = response.headers.get("content-length")
        try:
            content_length = int(length_header) if length_header is not None else None
        except ValueError:
            await response.aclose()
            await client.aclose()
            raise SoilGridsWcsClientError("Content-Length WCS SoilGrids invalide") from None
        if content_length is not None and content_length > max_bytes:
            await response.aclose()
            await client.aclose()
            raise AdapterSecurityError("SOILGRIDS_WCS_SIZE_LIMIT_EXCEEDED")

        async def body() -> AsyncIterator[bytes]:
            size = 0
            try:
                async for chunk in response.aiter_bytes(64 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise AdapterSecurityError("SOILGRIDS_WCS_SIZE_LIMIT_EXCEEDED")
                    yield chunk
            except httpx.HTTPError as exc:
                raise SoilGridsWcsClientError(
                    f"Échec pendant le streaming WCS SoilGrids : {exc}"
                ) from exc
            finally:
                await response.aclose()
                await client.aclose()

        return AdapterFetchResult(
            body=body(),
            content_type=response.headers.get("content-type"),
            content_length=content_length,
        )


__all__ = ["SoilGridsWcsClient", "SoilGridsWcsClientError"]
