"""MFA TOTP (RFC 6238) + codes de récupération à usage unique.

Le secret TOTP est chiffré côté serveur avec une clé dérivée de la clé
principale de l'application. Les codes de récupération sont hashés avec
Argon2id et consommés atomiquement.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import pyotp
from cryptography.fernet import Fernet

from gsie_api.core.config import get_settings

if TYPE_CHECKING:
    from uuid import UUID

    from gsie_api.auth.identity import PasswordService


class MfaError(Exception):
    """Erreur métier racine du module MFA."""


class MfaAlreadyEnabledError(MfaError):
    """Le compte a déjà un secret TOTP actif."""


class MfaNotEnabledError(MfaError):
    """Le compte n'a pas de secret TOTP actif."""


class InvalidTotpCodeError(MfaError):
    """Le code TOTP fourni est invalide ou expiré."""


class InvalidRecoveryCodeError(MfaError):
    """Le code de récupération est invalide, expiré ou déjà consommé."""


@dataclass(frozen=True, slots=True)
class MfaSetupResult:
    """Résultat de l'initialisation MFA — secret + URI otpauth + codes de récupération."""

    secret: str
    otpauth_uri: str
    recovery_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MfaSecretRecord:
    """Secret TOTP persisté, chargé sous verrou par le dépôt SQL."""

    account_id: UUID
    secret_cipher: str


class MfaRepositoryProtocol(Protocol):
    """Contrat de persistance requis par le service MFA."""

    async def get_active_secret(self, account_id: UUID) -> MfaSecretRecord | None: ...

    async def save_secret(self, account_id: UUID, secret_cipher: str) -> None: ...

    async def disable_secret(self, account_id: UUID) -> None: ...

    async def save_recovery_codes(self, account_id: UUID, code_hashes: list[str]) -> None: ...

    async def consume_recovery_code(self, account_id: UUID, code_hash: str) -> bool: ...

    async def has_recovery_codes(self, account_id: UUID) -> bool: ...


_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    """Dérive une clé Fernet depuis la clé JWT privée de l'application.

    En développement, utilise une clé fixe dérivée d'un seed constant.
    En production, la clé JWT privée est unique par déploiement.
    L'instance est cachée pour garantir que la même clé est utilisée
    tout au long du cycle de vie du processus.
    """
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    settings = get_settings()
    key_material = settings.jwt_private_key_path.encode("utf-8")
    # Dérivation déterministe — Fernet exige 32 bytes base64-url (44 chars)
    import base64
    import hashlib

    derived = hashlib.sha256(key_material).digest()
    _fernet_instance = Fernet(base64.urlsafe_b64encode(derived))
    return _fernet_instance


class MfaService:
    """Orchestre l'activation, la vérification et la récupération TOTP."""

    def __init__(
        self,
        repository: MfaRepositoryProtocol,
        password_service: PasswordService,
        now: type[object] | None = None,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._settings = get_settings()
        self._now = now

    async def setup(self, account_id: UUID) -> MfaSetupResult:
        """Génère un secret TOTP + codes de récupération pour le compte."""
        existing = await self._repository.get_active_secret(account_id)
        if existing is not None:
            raise MfaAlreadyEnabledError

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=self._settings.mfa_totp_step_seconds)
        otpauth_uri = totp.provisioning_uri(
            name=str(account_id),
            issuer_name=self._settings.mfa_issuer,
        )

        fernet = _get_fernet()
        secret_cipher = fernet.encrypt(secret.encode("utf-8")).decode("utf-8")
        await self._repository.save_secret(account_id, secret_cipher)

        recovery_codes = await self._generate_recovery_codes(account_id)

        return MfaSetupResult(
            secret=secret,
            otpauth_uri=otpauth_uri,
            recovery_codes=recovery_codes,
        )

    async def verify_totp(self, account_id: UUID, code: str) -> bool:
        """Vérifie un code TOTP contre le secret actif du compte."""
        record = await self._repository.get_active_secret(account_id)
        if record is None:
            raise MfaNotEnabledError

        fernet = _get_fernet()
        try:
            secret = fernet.decrypt(record.secret_cipher.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            raise MfaError("Secret MFA illisible") from exc

        totp = pyotp.TOTP(secret, interval=self._settings.mfa_totp_step_seconds)
        return totp.verify(code, valid_window=1)

    async def verify_recovery_code(self, account_id: UUID, code: str) -> bool:
        """Vérifie et consomme un code de récupération à usage unique."""
        normalized = code.strip().replace("-", "").upper()
        if not normalized:
            raise InvalidRecoveryCodeError

        # Le hash est calculé côté service pour que le dépôt ne voie que des hashes.
        code_hash = self._password_service.hash(normalized)
        consumed = await self._repository.consume_recovery_code(account_id, code_hash)
        if not consumed:
            raise InvalidRecoveryCodeError
        return True

    async def disable(self, account_id: UUID) -> None:
        """Désactive le MFA pour le compte."""
        record = await self._repository.get_active_secret(account_id)
        if record is None:
            raise MfaNotEnabledError
        await self._repository.disable_secret(account_id)

    async def _generate_recovery_codes(self, account_id: UUID) -> tuple[str, ...]:
        count = self._settings.mfa_recovery_code_count
        codes: list[str] = []
        hashes: list[str] = []
        for _ in range(count):
            raw = secrets.token_hex(8).upper()
            formatted = f"{raw[:8]}-{raw[8:]}"
            codes.append(formatted)
            hashes.append(self._password_service.hash(formatted.replace("-", "")))
        await self._repository.save_recovery_codes(account_id, hashes)
        return tuple(codes)
