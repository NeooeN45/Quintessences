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
import ipaddress
import json
import socket
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable

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


# ─────────────────────────────────────────────────────────────────────────
# Protection SSRF (RFC-0021 §4.3 — egress réseau applicatif)
# ─────────────────────────────────────────────────────────────────────────


def _default_dns_resolver(hostname: str) -> list[str]:
    """Résout un hostname en liste d'IPs (string).

    Retourne une liste vide si la résolution échoue (fail-open DNS) :
    si le hostname ne résout pas, la requête HTTP échouera aussi —
    pas de risque SSRF. Le risque DNS rebinding (résolution différente
    entre le check et la requête) exige une protection infrastructure
    (résolveur/proxy contrôlé), reconnu par RFC-0021 §4.3.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
        return [info[4][0] for info in infos]
    except (socket.gaierror, socket.herror):
        return []


# Résolveur DNS injectable pour les tests. Par défaut, utilise socket.getaddrinfo.
# Les tests monkeypatchent cette variable pour éviter la résolution réelle.
_dns_resolver: Callable[[str], list[str]] = _default_dns_resolver


def valider_url_egress(url: str) -> None:
    """Valide qu'une URL ne pointe pas vers une IP interne.

    Prévention SSRF (RFC-0021 §4.3) : bloque les requêtes vers
    - Loopback : 127.0.0.0/8, ::1
    - Link-local : 169.254.0.0/16 (metadata AWS/GCP), fe80::/10
    - Privé : 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7
    - Unspecified : 0.0.0.0, ::
    - Multicast/broadcast

    Lève ``ValueError`` si l'URL pointe vers une IP bloquée.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return  # URL relative ou sans hostname — pas de risque SSRF

    # Collecter toutes les IPs à vérifier : littéral IP + résolution DNS
    ips: list[str] = []
    try:
        ipaddress.ip_address(hostname)
        ips.append(hostname)  # littéral IP direct
    except ValueError:
        pass  # hostname, pas un littéral IP — résoudre ci-dessous

    ips.extend(_dns_resolver(hostname))

    for ip_str in ips:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_unspecified
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise ValueError(
                f"URL bloquée par la protection SSRF (egress) : "
                f"{hostname} résout vers {ip_str} ({ip.__class__.__name__})"
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
        data: dict[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
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

        ``data`` et ``files`` permettent d'envoyer du multipart/form-data
        (ex. upload d'images). Mutuellement exclusifs avec ``json_body``.
        """
        label = error_label or f"de l'appel API {method} {path}"
        merged_headers = {**self.auth_headers(), **(headers or {})}
        url = path if path.startswith("http") else f"{self.base_url}{path}"

        # Protection SSRF (RFC-0021 §4.3) : bloquer les URLs pointant
        # vers une IP interne avant toute requête. Le check est hors
        # boucle de retry — une URL bloquée ne mérite pas de retry.
        try:
            valider_url_egress(url)
        except ValueError as exc:
            raise self.exception_class(f"Échec {label} : {exc}") from exc

        last_exc: Exception | None = None
        for tentative in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        json=json_body,
                        data=data,
                        files=files,
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

    async def _post_multipart_json(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]],
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        error_label: str | None = None,
    ) -> Any:
        """POST multipart/form-data + parse JSON + capture erreurs.

        Pour les APIs qui acceptent des fichiers (ex. PlantNet identify).
        ``files`` est une liste de tuples httpx :
        ``[(nom_champ, (nom_fichier, contenu_bytes, content_type))]``.
        """
        label = error_label or f"de l'appel API POST {path}"
        try:
            response = await self._request(
                "POST",
                path,
                params=params,
                data=data,
                files=files,
                headers=headers,
                error_label=label,
            )
            return response.json()
        except json.JSONDecodeError as exc:
            raise self.exception_class(f"Échec {label} : {exc}") from exc


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
