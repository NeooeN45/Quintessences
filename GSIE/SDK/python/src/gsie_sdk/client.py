"""Client principal du SDK GSIE — gestion auth + transport httpx asynchrone.

Le client gère le cycle de vie du JWT RS256 :
- `login` récupère access + refresh tokens
- toute requête porte le header `Authorization: Bearer <access>`
- sur 401, refresh automatique puis retry unique
- `verify` contrôle la validité du token courant

Aucune logique métier : le SDK ne fait que transporter. Les wrappers moteurs
(`engines.py`) exposent les endpoints de l'API de façon ergonomique.
"""

from __future__ import annotations

from typing import Any, cast

import httpx

from gsie_sdk.exceptions import APIError, AuthenticationError, TokenRefreshError

API_PREFIX = "/api/v1"
TOKEN_REFRESH_PATH = "/auth/refresh"
DEFAULT_TIMEOUT = 30.0


class GSIEClient:
    """Client asynchrone de l'API GSIE.

    Usage :
        async with GSIEClient("http://localhost:8000") as client:
            await client.login("admin", "secret")
            diag = await client.diagnostic.diagnostiquer({...})
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=headers or {},
        )
        # Wrappers moteurs — instanciés paresseusement pour partager le transport
        from gsie_sdk.engines import Engines

        self.diagnostic = Engines(self, "diagnostic")
        self.recommendation = Engines(self, "recommendation")
        self.validation = Engines(self, "validation")
        self.simulation = Engines(self, "simulation")

    async def __aenter__(self) -> GSIEClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Ferme le transport httpx sous-jacent."""
        await self._http.aclose()

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    async def login(self, username: str, password: str) -> None:
        """Authentifie et stocke access + refresh tokens."""
        resp = await self._http.post(
            f"{API_PREFIX}/auth/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 401:
            raise AuthenticationError("Identifiants invalides")
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.text)
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]

    async def verify(self) -> dict[str, Any]:
        """Vérifie la validité du token courant."""
        return cast("dict[str, Any]", await self._request("GET", "/auth/verify"))

    async def health(self) -> dict[str, Any]:
        """Liveness probe (instantané)."""
        resp = await self._http.get("/health")
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.text)
        return cast("dict[str, Any]", resp.json())

    async def ready(self) -> dict[str, Any]:
        """Readiness probe (DB + Redis)."""
        resp = await self._http.get("/ready")
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.text)
        return cast("dict[str, Any]", resp.json())

    async def _refresh(self) -> None:
        """Rafraîchit le token via le refresh token (rotation)."""
        if not self._refresh_token:
            raise TokenRefreshError("Aucun refresh token disponible")
        resp = await self._http.post(
            f"{API_PREFIX}{TOKEN_REFRESH_PATH}",
            json={"refresh_token": self._refresh_token},
        )
        if resp.status_code != 200:
            raise TokenRefreshError(f"Refresh refusé: {resp.status_code}")
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        retry_on_401: bool = True,
    ) -> Any:
        """Requête authentifiée avec refresh automatique sur 401.

        Args:
            method: verbe HTTP (GET, POST, ...).
            path: chemin relatif au prefix API (ex. "/diagnostic/diagnostiquer").
            json: corps de requête.
            params: paramètres de query string.
            retry_on_401: si False, ne pas tenter de refresh sur 401 (évite boucle).
        """
        try:
            return await self._request(method, path, json=json, params=params)
        except APIError as exc:
            if exc.status_code == 401 and retry_on_401 and self._refresh_token:
                await self._refresh()
                return await self._request(method, path, json=json, params=params, _authed=True)
            raise

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        _authed: bool = False,
    ) -> Any:
        url = f"{API_PREFIX}{path}"
        headers = self._auth_headers()
        resp = await self._http.request(method, url, json=json, params=params, headers=headers)
        if resp.status_code == 401 and not _authed:
            raise APIError(401, resp.text)
        if resp.status_code >= 400:
            raise APIError(resp.status_code, resp.text)
        if resp.status_code == 204:
            return None
        return resp.json()

    def _auth_headers(self) -> dict[str, str]:
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}
