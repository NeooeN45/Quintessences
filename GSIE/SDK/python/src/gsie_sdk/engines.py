"""Wrappers ergonomiques pour les endpoints des moteurs GSIE.

Chaque moteur expose une interface uniforme :
- `status()`  — GET /<engine>/status
- `version()`  — GET /<engine>/version
- `<action>(payload)` — endpoint principal POST du moteur

Aucune logique métier : les payloads sont passés tels quels à l'API,
qui valide via ses propres schémas Pydantic.
"""

from __future__ import annotations

from typing import Any, cast

from gsie_sdk.client import GSIEClient


class Engines:
    """Wrapper générique pour un moteur GSIE.

    Les endpoints principaux sont exposés dynamiquement via `action()`.
    Les wrappers nommés (diagnostiquer, recommander, ...) délèuent à `action()`.
    """

    def __init__(self, client: GSIEClient, name: str) -> None:
        self._client = client
        self._name = name

    async def status(self) -> dict[str, Any]:
        """Statut du moteur (GET /<name>/status)."""
        return cast("dict[str, Any]", await self._client.request("GET", f"/{self._name}/status"))

    async def version(self) -> dict[str, Any]:
        """Version et backend du moteur (GET /<name>/version)."""
        return cast("dict[str, Any]", await self._client.request("GET", f"/{self._name}/version"))

    async def action(self, endpoint: str, payload: dict[str, Any]) -> Any:
        """Appelle l'endpoint principal POST d'un moteur.

        Args:
            endpoint: nom de l'endpoint (ex. "diagnostiquer", "recommander").
            payload: corps de la requête (validé côté API).
        """
        return await self._client.request("POST", f"/{self._name}/{endpoint}", json=payload)

    # Wrappers nommés pour les endpoints principaux connus.
    async def diagnostiquer(self, payload: dict[str, Any]) -> Any:
        return await self.action("diagnostiquer", payload)

    async def recommander(self, payload: dict[str, Any]) -> Any:
        return await self.action("recommander", payload)

    async def valider(self, payload: dict[str, Any]) -> Any:
        return await self.action("valider", payload)

    async def simuler(self, payload: dict[str, Any]) -> Any:
        return await self.action("simuler", payload)
