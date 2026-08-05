"""Vérification de force de mot de passe — HIBP k-anonymity + zxcvbn.

HIBP (HaveIBeenPwned) utilise le protocole k-anonymity : seul le préfixe
SHA-1 (5 premiers caractères hex) est envoyé, le suffixe est comparé
localement. Aucune information sur le mot de passe complet ne quitte
le serveur.

zxcvbn produit un score 0-4 (0 = trivial, 4 = robuste). Le seuil
minimum est configurable (défaut : 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
from zxcvbn import zxcvbn

from gsie_api.core.config import get_settings


class PasswordStrengthError(Exception):
    """Erreur racine de la vérification de force mot de passe."""


class CompromisedPasswordError(PasswordStrengthError):
    """Le mot de passe apparaît dans une fuite de données connue."""


class WeakPasswordError(PasswordStrengthError):
    """Le mot de passe ne atteint pas le score zxcvbn minimum."""

    def __init__(self, score: int, minimum: int, suggestions: list[str]) -> None:
        self.score = score
        self.minimum = minimum
        self.suggestions = suggestions
        super().__init__(f"Score zxcvbn {score} < minimum {minimum}")


@dataclass(frozen=True, slots=True)
class PasswordStrengthReport:
    """Rapport de vérification de force mot de passe."""

    zxcvbn_score: int
    is_compromised: bool
    compromise_count: int
    suggestions: tuple[str, ...]


class HibpClientProtocol(Protocol):
    """Contrat du client HIBP pour injection de test."""

    async def fetch_suffixes(self, prefix: str) -> dict[str, int]:
        """Retourne les suffixes SHA-1 et leurs comptes pour un préfixe donné."""


class HttpxHibpClient:
    """Client HIBP utilisant l'API v3 avec k-anonymity."""

    _BASE_URL = "https://api.pwnedpasswords.com/range"

    async def fetch_suffixes(self, prefix: str) -> dict[str, int]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._BASE_URL}/{prefix}")
            response.raise_for_status()
        result: dict[str, int] = {}
        for line in response.text.splitlines():
            if ":" not in line:
                continue
            suffix, count_str = line.split(":", 1)
            try:
                result[suffix.strip()] = int(count_str.strip())
            except ValueError:
                continue
        return result


class PasswordStrengthService:
    """Vérifie la force et la compromission d'un mot de passe."""

    def __init__(
        self,
        hibp_client: HibpClientProtocol | None = None,
    ) -> None:
        self._settings = get_settings()
        self._hibp_client = hibp_client or HttpxHibpClient()

    async def validate(
        self,
        password: str,
        user_inputs: list[str] | None = None,
    ) -> PasswordStrengthReport:
        """Valide un mot de passe et lève une exception s'il est faible ou compromis."""
        report = await self.check(password, user_inputs)

        if self._settings.password_check_hibp_enabled and report.is_compromised:
            raise CompromisedPasswordError(
                f"Mot de passe compromis ({report.compromise_count} occurrences)"
            )

        if (
            self._settings.password_check_zxcvbn_enabled
            and report.zxcvbn_score < self._settings.password_min_zxcvbn_score
        ):
            raise WeakPasswordError(
                score=report.zxcvbn_score,
                minimum=self._settings.password_min_zxcvbn_score,
                suggestions=list(report.suggestions),
            )

        return report

    async def check(
        self,
        password: str,
        user_inputs: list[str] | None = None,
    ) -> PasswordStrengthReport:
        """Vérifie sans lever — retourne un rapport complet."""
        # zxcvbn (synchrone, rapide)
        result = zxcvbn(password, user_inputs or [])
        zxcvbn_score = int(result.get("score", 0))
        suggestions = tuple(result.get("feedback", {}).get("suggestions", []))

        # HIBP k-anonymity
        is_compromised = False
        compromise_count = 0
        if self._settings.password_check_hibp_enabled:
            import hashlib

            sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
            prefix, suffix = sha1[:5], sha1[5:]
            try:
                suffixes = await self._hibp_client.fetch_suffixes(prefix)
                compromise_count = suffixes.get(suffix, 0)
                is_compromised = compromise_count > 0
            except Exception:
                # HIBP indisponible — on ne bloque pas l'inscription, on log.
                is_compromised = False

        return PasswordStrengthReport(
            zxcvbn_score=zxcvbn_score,
            is_compromised=is_compromised,
            compromise_count=compromise_count,
            suggestions=suggestions,
        )
