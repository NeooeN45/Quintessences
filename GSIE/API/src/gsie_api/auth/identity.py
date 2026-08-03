"""Service d'identité canonique Quintessences (RFC-0032, DEC-000044).

Ce module ne dépend ni de FastAPI ni de SQLAlchemy. Il porte les invariants
d'identité et reste testable avec un dépôt mémoire : le compte canonique est
distinct des moyens de connexion et une adresse e-mail ne déclenche jamais
une fusion implicite avec Google.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from email_validator import EmailNotValidError, validate_email

if TYPE_CHECKING:
    from uuid import UUID


class IdentityError(Exception):
    """Erreur métier racine du module d'identité."""


class InvalidEmailError(IdentityError):
    """L'adresse ne peut pas servir d'identifiant local."""


class AccountAlreadyExistsError(IdentityError):
    """Un moyen de connexion local utilise déjà cette adresse."""


class InvalidCredentialsError(IdentityError):
    """Les informations de connexion ne prouvent pas l'identité."""


class AccountLinkRequiredError(IdentityError):
    """Un compte existant doit être authentifié avant rattachement."""


class ProviderAlreadyLinkedError(IdentityError):
    """L'identité externe appartient déjà à un autre compte."""


class ProviderNotConfiguredError(IdentityError):
    """Le fournisseur demandé n'est pas configuré côté serveur."""


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    """Compte canonique prêt à recevoir une session GSIE."""

    account_id: UUID
    roles: tuple[str, ...]
    provider: str
    is_active: bool = True
    session_version: int = 1


@dataclass(frozen=True, slots=True)
class LocalCredentialRecord:
    """Résultat minimal requis pour vérifier un moyen local."""

    account: AuthenticatedAccount
    identity_link_id: UUID
    password_hash: str


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    """Identité Google validée cryptographiquement côté serveur."""

    issuer: str
    subject: str
    email: str
    display_name: str | None


class IdentityRepositoryProtocol(Protocol):
    """Contrat de persistance requis par le service d'identité."""

    async def create_local_account(
        self,
        email: str,
        password_hash: str,
        display_name: str | None,
    ) -> AuthenticatedAccount: ...

    async def find_local_credentials(self, email: str) -> LocalCredentialRecord | None: ...

    async def update_password_hash(self, identity_link_id: UUID, password_hash: str) -> None: ...

    async def mark_authenticated(self, identity_link_id: UUID) -> None: ...

    async def find_provider_account(
        self,
        provider: str,
        issuer: str,
        subject: str,
    ) -> AuthenticatedAccount | None: ...

    async def has_account_with_verified_email(self, email: str) -> bool: ...

    async def create_google_account(self, identity: GoogleIdentity) -> AuthenticatedAccount: ...

    async def link_google_identity(
        self,
        account_id: UUID,
        identity: GoogleIdentity,
    ) -> AuthenticatedAccount: ...


class GoogleVerifierProtocol(Protocol):
    """Contrat de vérification d'un jeton d'identité Google."""

    @property
    def is_configured(self) -> bool: ...

    async def verify(self, token: str, expected_nonce: str) -> GoogleIdentity: ...


def normalize_email(value: str) -> str:
    """Valide puis normalise une adresse sans requête DNS.

    Le résultat est replié en casse pour garantir une clé locale stable.
    Google reste identifié par ``issuer + sub`` et non par cette valeur.
    """
    try:
        normalized = validate_email(value.strip(), check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise InvalidEmailError("Adresse e-mail invalide") from exc
    return normalized.casefold()


class PasswordService:
    """Hachage et vérification des mots de passe avec Argon2id."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(type=Type.ID)
        # Ce hash factice égalise le chemin d'un compte absent. Il ne protège
        # aucun secret et n'est jamais persisté.
        self._dummy_hash = self._hasher.hash("quintessences-dummy-password-not-an-account")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    def verify_dummy(self, password: str) -> None:
        """Exécute volontairement un calcul Argon2 pour un compte absent."""
        self.verify(self._dummy_hash, password)

    def needs_rehash(self, password_hash: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except InvalidHashError:
            return False


class IdentityService:
    """Orchestre les moyens de connexion autour du compte canonique."""

    def __init__(
        self,
        repository: IdentityRepositoryProtocol,
        password_service: PasswordService,
        google_verifier: GoogleVerifierProtocol | None = None,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._google_verifier = google_verifier

    async def register_local(
        self,
        email: str,
        password: str,
        display_name: str | None,
    ) -> AuthenticatedAccount:
        normalized_email = normalize_email(email)
        password_hash = self._password_service.hash(password)
        return await self._repository.create_local_account(
            normalized_email,
            password_hash,
            display_name,
        )

    async def authenticate_local(self, email: str, password: str) -> AuthenticatedAccount:
        normalized_email = normalize_email(email)
        record = await self._repository.find_local_credentials(normalized_email)
        if record is None:
            self._password_service.verify_dummy(password)
            raise InvalidCredentialsError
        if not record.account.is_active or not self._password_service.verify(
            record.password_hash,
            password,
        ):
            raise InvalidCredentialsError
        if self._password_service.needs_rehash(record.password_hash):
            await self._repository.update_password_hash(
                record.identity_link_id,
                self._password_service.hash(password),
            )
        await self._repository.mark_authenticated(record.identity_link_id)
        return record.account

    async def authenticate_google(self, token: str, nonce: str) -> AuthenticatedAccount:
        verifier = self._require_google_verifier()
        identity = await verifier.verify(token, nonce)
        account = await self._repository.find_provider_account(
            "google",
            identity.issuer,
            identity.subject,
        )
        if account is not None:
            if not account.is_active:
                raise InvalidCredentialsError
            return account
        if await self._repository.has_account_with_verified_email(identity.email):
            raise AccountLinkRequiredError
        return await self._repository.create_google_account(identity)

    async def link_google(
        self,
        account_id: UUID,
        token: str,
        nonce: str,
    ) -> AuthenticatedAccount:
        verifier = self._require_google_verifier()
        identity = await verifier.verify(token, nonce)
        existing = await self._repository.find_provider_account(
            "google",
            identity.issuer,
            identity.subject,
        )
        if existing is not None:
            if existing.account_id != account_id:
                raise ProviderAlreadyLinkedError
            return existing
        return await self._repository.link_google_identity(account_id, identity)

    def _require_google_verifier(self) -> GoogleVerifierProtocol:
        if self._google_verifier is None or not self._google_verifier.is_configured:
            raise ProviderNotConfiguredError
        return self._google_verifier
