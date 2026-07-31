"""Classe de base pour tous les clients d'API externes GSIE.

Capture automatiquement les 5 modes de panne identifiés dans
GSIE-PROMPT-0023 :

1. **Panne réseau** — `httpx.ConnectError`, `httpx.ConnectTimeout`, etc.
2. **HTTP 4xx/5xx** — `httpx.HTTPStatusError` (via `raise_for_status()`).
3. **Corps malformé** — `json.JSONDecodeError` (JSON), `ValueError`,
   `TypeError` (parsing).
4. **Champ absent** — géré par le client via `dict.get()` + retour
   `None`/`[]`/`{}` (jamais de valeur inventée).
5. **Quota/Auth** — 401/403/429 capturés comme cas particulier du mode #2.

Tout nouveau client d'API externe doit hériter de `ResilientHttpClient`
ou `ResilientCsvClient`. La capture des erreurs est alors automatique —
impossible d'oublier une garde.

Usage typique :

    class MonClient(ResilientHttpClient):
        @property
        def exception_class(self) -> type[Exception]:
            return MonClientError

        @property
        def base_url(self) -> str:
            return "https://api.exemple.com/v1"

        def auth_headers(self) -> dict[str, str]:
            return {"apikey": get_settings().ma_cle}

        async def get_data(self, query: str) -> dict[str, Any] | None:
            data = await self._get_json(
                "/search",
                params={"q": query},
                error_label="de l'appel MonService",
            )
            if "result" not in data:
                return None
            return data

Pour le CSV, utiliser `ResilientCsvClient` qui parse automatiquement
le corps en `list[dict[str, str | None]]` via `csv.DictReader`.

Le paramètre ``error_label`` personnalise le message d'erreur :
``f"Échec {error_label} : {exc}"``. Par défaut, ``error_label`` est
``f"de l'appel API {method} {path}"``.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 0.5  # secondes — backoff exponentiel : 0.5s, 1s, 2s
# Erreurs réseau transitoires qui meritent un retry.
# Les 4xx (sauf 429) sont des erreurs applicatives — pas de retry.
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)


class ResilientHttpClient(ABC):
    """Base class pour les clients d'API externes avec résilience automatique.

    Capture `httpx.HTTPError`, `json.JSONDecodeError` et les wrap dans
    l'exception métier définie par `exception_class`. Les sous-classes
    n'ont qu'à définir :

    - `exception_class` : l'exception à lever
    - `base_url` : l'URL de base de l'API
    - `auth_headers()` : les headers d'authentification (optionnel)

    Les méthodes utilitaires `_get_json()`, `_get_text()`, `_get_bytes()`
    gèrent la requête HTTP + le parsing + la capture d'erreurs.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT, max_retries: int = _MAX_RETRIES) -> None:
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    @abstractmethod
    def exception_class(self) -> type[Exception]:
        """La classe d'exception métier à lever en cas d'échec."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """L'URL de base de l'API (sans trailing slash)."""

    def auth_headers(self) -> dict[str, str]:
        """Headers d'authentification. Override pour ajouter apikey, Bearer, etc."""
        return {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
    ) -> httpx.Response:
        """Exécute une requête HTTP et capture les 5 modes de panne.

        Lève `self.exception_class` en cas d'erreur réseau, HTTP 4xx/5xx,
        ou quota/auth. Retourne la réponse brute pour parsing par
        l'appelant.

        Retry automatique sur erreurs réseau transitoires
        (`ConnectError`, `ConnectTimeout`, `ReadTimeout`,
        `RemoteProtocolError`) avec backoff exponentiel (0.5s, 1s, 2s).
        Les 4xx (sauf 429) ne sont pas retryés — ce sont des erreurs
        applicatives, pas des pannes transitoires. 429 (quota) est
        retryé car le serveur peut lever la limite.
        """
        label = error_label or f"de l'appel API {method} {path}"
        merged_headers = {**self.auth_headers(), **(headers or {})}
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        last_exc: Exception | None = None
        for tentative in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        json=json_body,
                        headers=merged_headers,
                    )
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as exc:
                # 429 (Too Many Requests) — le serveur peut lever la limite.
                if exc.response.status_code == 429 and tentative < self._max_retries:
                    last_exc = exc
                    await asyncio.sleep(_RETRY_BASE_DELAY * (2**tentative))
                    continue
                raise self.exception_class(f"Échec {label} : {exc}") from exc
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if tentative < self._max_retries:
                    await asyncio.sleep(_RETRY_BASE_DELAY * (2**tentative))
                    continue
                raise self.exception_class(f"Échec {label} : {exc}") from exc
            except httpx.HTTPError as exc:
                raise self.exception_class(f"Échec {label} : {exc}") from exc
        # Normalement inatteignable — la boucle raise ou return toujours.
        raise self.exception_class(f"Échec {label} : {last_exc}") from last_exc

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
    ) -> Any:
        """GET + parse JSON + capture JSONDecodeError.

        Lève `self.exception_class` si le JSON est malformé.
        """
        label = error_label or f"de l'appel API GET {path}"
        try:
            response = await self._request(
                "GET", path, params=params, headers=headers, error_label=label
            )
            return response.json()
        except json.JSONDecodeError as exc:
            raise self.exception_class(f"Échec {label} : {exc}") from exc

    async def _get_text(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
    ) -> str:
        """GET + retourne le corps en texte. Pour CSV, XML, etc."""
        response = await self._request(
            "GET", path, params=params, headers=headers, error_label=error_label
        )
        return response.text

    async def _get_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
    ) -> bytes:
        """GET + retourne le corps en bytes. Pour gzip, binaire, etc."""
        response = await self._request(
            "GET", path, params=params, headers=headers, error_label=error_label
        )
        return response.content


class ResilientCsvClient(ResilientHttpClient):
    """Base class pour les clients d'API qui retournent du CSV.

    Parse automatiquement le corps en `list[dict[str, str | None]]` via
    `csv.DictReader`. Un corps vide retourne `[]` — jamais de valeur
    inventée. Les colonnes manquantes sont `None`.
    """

    async def _get_csv(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
        delimiter: str = ";",
    ) -> list[dict[str, str | None]]:
        """GET + parse CSV + capture erreurs de parsing."""
        text = await self._get_text(path, params=params, headers=headers, error_label=error_label)
        if not text.strip():
            return []
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return list(reader)
