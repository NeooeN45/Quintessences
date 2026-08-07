"""Tests unitaires pour le hardening auth — MFA, lockout, sessions, force mot de passe.

Ces tests valident les services isolément avec des fakes/doubles, sans base de
données ni Redis. Les tests d'intégration (router + DB) sont dans test_auth.py.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
import pyotp
import pytest
from pydantic import SecretStr

import gsie_api.auth.mfa as mfa_module
from gsie_api.auth.lockout import (
    AccountLockedError,
    AccountLockoutService,
    MemoryLockoutStore,
)
from gsie_api.auth.mfa import (
    InvalidRecoveryCodeError,
    MfaAlreadyEnabledError,
    MfaError,
    MfaNotEnabledError,
    MfaSecretRecord,
    MfaService,
)
from gsie_api.auth.password_strength import (
    CompromisedPasswordError,
    PasswordStrengthService,
    WeakPasswordError,
)
from gsie_api.auth.sessions import SessionInfo, SessionService

# ---------------------------------------------------------------------------
# MFA TOTP
# ---------------------------------------------------------------------------


class FakeMfaRepository:
    """Fake du dépôt MFA pour tests isolés."""

    def __init__(self) -> None:
        self._secrets: dict[UUID, str] = {}
        self._recovery_codes: dict[UUID, list[str]] = {}

    async def get_active_secret(self, account_id: UUID) -> MfaSecretRecord | None:
        if account_id not in self._secrets:
            return None
        return MfaSecretRecord(account_id=account_id, secret_cipher=self._secrets[account_id])

    async def save_secret(self, account_id: UUID, secret_cipher: str) -> None:
        if account_id in self._secrets:
            raise MfaAlreadyEnabledError
        self._secrets[account_id] = secret_cipher

    async def disable_secret(self, account_id: UUID) -> None:
        if account_id not in self._secrets:
            raise MfaNotEnabledError
        del self._secrets[account_id]

    async def save_recovery_codes(self, account_id: UUID, code_hashes: list[str]) -> None:
        self._recovery_codes[account_id] = list(code_hashes)

    async def consume_recovery_code(self, account_id: UUID, code: str) -> bool:
        codes = self._recovery_codes.get(account_id, [])
        stored_hash = f"hash:{code}"
        if stored_hash in codes:
            codes.remove(stored_hash)
            return True
        return False

    async def has_recovery_codes(self, account_id: UUID) -> bool:
        return bool(self._recovery_codes.get(account_id))


class FakePasswordService:
    """Fake de PasswordService — hash trivial pour tests."""

    def hash(self, password: str) -> str:
        return f"hash:{password}"

    def verify(self, stored_hash: str, plain: str) -> bool:
        return stored_hash == f"hash:{plain}"


@pytest.fixture()
def mfa_service() -> MfaService:
    repo = FakeMfaRepository()
    return MfaService(repository=repo, password_service=FakePasswordService())  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def _reset_fernet_instance() -> None:
    """Isole l'instance Fernet globale entre chaque test MFA."""
    mfa_module._fernet_instance = None
    yield
    mfa_module._fernet_instance = None


class TestMfaSetup:
    async def test_setup_generates_secret_and_recovery_codes(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        result = await mfa_service.setup(account_id)

        assert len(result.secret) >= 16
        assert result.otpauth_uri.startswith("otpauth://totp/")
        assert len(result.recovery_codes) == 10
        # Chaque code de récupération a le format XXXXXXXX-XXXXXXXX
        for code in result.recovery_codes:
            assert "-" in code
            assert len(code.replace("-", "")) == 16

    async def test_setup_twice_raises_already_enabled(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        with pytest.raises(MfaAlreadyEnabledError):
            await mfa_service.setup(account_id)


class TestMfaVerifyTotp:
    async def test_verify_valid_totp_code(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        result = await mfa_service.setup(account_id)
        totp = pyotp.TOTP(result.secret, interval=30)
        valid_code = totp.now()
        assert await mfa_service.verify_totp(account_id, valid_code) is True

    async def test_verify_invalid_totp_code(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        assert await mfa_service.verify_totp(account_id, "000000") is False

    async def test_verify_without_setup_raises_not_enabled(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        with pytest.raises(MfaNotEnabledError):
            await mfa_service.verify_totp(account_id, "123456")


class TestMfaRecoveryCode:
    async def test_verify_recovery_code_success(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        result = await mfa_service.setup(account_id)
        first_code = result.recovery_codes[0].replace("-", "")
        assert await mfa_service.verify_recovery_code(account_id, first_code) is True

    async def test_verify_recovery_code_twice_fails(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        result = await mfa_service.setup(account_id)
        first_code = result.recovery_codes[0].replace("-", "")
        await mfa_service.verify_recovery_code(account_id, first_code)
        with pytest.raises(InvalidRecoveryCodeError):
            await mfa_service.verify_recovery_code(account_id, first_code)

    async def test_verify_invalid_recovery_code(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        with pytest.raises(InvalidRecoveryCodeError):
            await mfa_service.verify_recovery_code(account_id, "INVALID")


class TestMfaDisable:
    async def test_disable_removes_secret(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        await mfa_service.disable(account_id)
        with pytest.raises(MfaNotEnabledError):
            await mfa_service.verify_totp(account_id, "123456")

    async def test_disable_without_setup_raises(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        with pytest.raises(MfaNotEnabledError):
            await mfa_service.disable(account_id)


class TestMfaStatus:
    async def test_is_enabled_returns_true_when_secret_exists(
        self, mfa_service: MfaService
    ) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        assert await mfa_service.is_enabled(account_id) is True

    async def test_is_enabled_returns_false_when_no_secret(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        assert await mfa_service.is_enabled(account_id) is False


class TestMfaFernetAndEdgeCases:
    def _fake_settings(
        self,
        *,
        environment: str = "development",
        mfa_encryption_key: str = "",
    ) -> object:
        return SimpleNamespace(
            mfa_encryption_key=SecretStr(mfa_encryption_key),
            environment=environment,
            mfa_issuer="Quintessences",
            mfa_totp_step_seconds=30,
        )

    def test_fernet_rejects_empty_key_in_production(self) -> None:
        fake = self._fake_settings(environment="production", mfa_encryption_key="")
        with (
            patch("gsie_api.auth.mfa.get_settings", return_value=fake),
            pytest.raises(MfaError, match="Clé de chiffrement MFA absente"),
        ):
            mfa_module._get_fernet()

    def test_fernet_rejects_invalid_key(self) -> None:
        fake = self._fake_settings(mfa_encryption_key="invalid-key")
        with (
            patch("gsie_api.auth.mfa.get_settings", return_value=fake),
            pytest.raises(MfaError, match="Clé de chiffrement MFA invalide"),
        ):
            mfa_module._get_fernet()

    async def test_verify_totp_raises_when_secret_cannot_be_decrypted(
        self, mfa_service: MfaService
    ) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        # Remplace le secret chiffré par une chaîne invalide pour Fernet.
        mfa_service._repository._secrets[account_id] = "not-a-fernet-token"

        with pytest.raises(MfaError, match="Secret MFA illisible"):
            await mfa_service.verify_totp(account_id, "123456")

    async def test_verify_recovery_code_empty_raises(self, mfa_service: MfaService) -> None:
        account_id = uuid4()
        await mfa_service.setup(account_id)
        with pytest.raises(InvalidRecoveryCodeError):
            await mfa_service.verify_recovery_code(account_id, "   ")


# ---------------------------------------------------------------------------
# Lockout progressif
# ---------------------------------------------------------------------------


class TestMemoryLockoutStore:
    async def test_lockout_after_max_attempts(self) -> None:
        store = MemoryLockoutStore(max_attempts=3, lock_duration_seconds=60)
        key = "user@example.com:127.0.0.1"
        for _ in range(2):
            count = await store.record_failure(key)
            assert count < 3
            assert not await store.is_locked(key)

        count = await store.record_failure(key)
        assert count == 3
        assert await store.is_locked(key)
        assert await store.remaining_lock_seconds(key) > 0

    async def test_record_success_resets_counter(self) -> None:
        store = MemoryLockoutStore(max_attempts=3, lock_duration_seconds=60)
        key = "user@example.com:127.0.0.1"
        await store.record_failure(key)
        await store.record_failure(key)
        await store.record_success(key)
        assert not await store.is_locked(key)
        count = await store.record_failure(key)
        assert count == 1

    async def test_lockout_expires(self) -> None:
        store = MemoryLockoutStore(max_attempts=2, lock_duration_seconds=1)
        key = "test:ip"
        await store.record_failure(key)
        await store.record_failure(key)
        assert await store.is_locked(key)
        # Le verrouillage expire après lock_duration seconds
        await asyncio.sleep(1.1)
        assert not await store.is_locked(key)


class TestAccountLockoutService:
    async def test_check_and_raise_when_not_locked(self) -> None:
        store = MemoryLockoutStore(max_attempts=5, lock_duration_seconds=60)
        service = AccountLockoutService(store)
        # Ne lève pas d'exception
        await service.check_and_raise("user@example.com", "127.0.0.1")

    async def test_check_and_raise_when_locked(self) -> None:
        store = MemoryLockoutStore(max_attempts=2, lock_duration_seconds=60)
        service = AccountLockoutService(store)
        await service.record_failure("user@example.com", "127.0.0.1")
        await service.record_failure("user@example.com", "127.0.0.1")
        with pytest.raises(AccountLockedError) as exc_info:
            await service.check_and_raise("user@example.com", "127.0.0.1")
        assert exc_info.value.remaining_seconds > 0


# ---------------------------------------------------------------------------
# Sessions actives
# ---------------------------------------------------------------------------


class FakeSessionRepository:
    """Fake du dépôt de sessions pour tests isolés."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionInfo] = {}
        self._revoked: set[UUID] = set()

    async def create_session(
        self,
        account_id: UUID,
        jti: str,
        refresh_jti: str | None,
        device_name: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> SessionInfo:
        session_id = uuid4()
        now = datetime.now(UTC)
        info = SessionInfo(
            id=session_id,
            jti=jti,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            issued_at=now,
            last_seen_at=now,
        )
        self._sessions[session_id] = info
        return info

    async def list_active_sessions(self, account_id: UUID) -> list[SessionInfo]:
        return list(self._sessions.values())

    async def revoke_session(self, account_id: UUID, session_id: UUID) -> bool:
        if session_id in self._sessions and session_id not in self._revoked:
            self._revoked.add(session_id)
            return True
        return False

    async def revoke_all_sessions(self, account_id: UUID, except_jti: str | None = None) -> int:
        count = 0
        for sid, info in list(self._sessions.items()):
            if except_jti and info.jti == except_jti:
                continue
            self._revoked.add(sid)
            count += 1
        return count

    async def revoke_by_jti(self, jti: str) -> bool:
        for sid, info in self._sessions.items():
            if info.jti == jti and sid not in self._revoked:
                self._revoked.add(sid)
                return True
        return False

    async def touch_session(self, jti: str) -> None:
        pass


class TestSessionService:
    async def test_register_and_list_session(self) -> None:
        service = SessionService(FakeSessionRepository())  # type: ignore[arg-type]
        account_id = uuid4()
        info = await service.register_session(
            account_id=account_id,
            jti="jti-1",
            refresh_jti="refresh-1",
            device_name="Chrome",
            user_agent="Mozilla/5.0",
            ip_address="127.0.0.1",
        )
        assert info.jti == "jti-1"
        sessions = await service.list_sessions(account_id)
        assert len(sessions) == 1

    async def test_revoke_session(self) -> None:
        service = SessionService(FakeSessionRepository())  # type: ignore[arg-type]
        account_id = uuid4()
        info = await service.register_session(account_id, "jti-1", "refresh-1", None, None, None)
        assert await service.revoke_session(account_id, info.id) is True
        assert await service.revoke_session(account_id, info.id) is False

    async def test_revoke_all_sessions_except_current(self) -> None:
        service = SessionService(FakeSessionRepository())  # type: ignore[arg-type]
        account_id = uuid4()
        await service.register_session(account_id, "jti-1", "r-1", None, None, None)
        await service.register_session(account_id, "jti-2", "r-2", None, None, None)
        count = await service.revoke_all_sessions(account_id, except_jti="jti-1")
        assert count == 1


# ---------------------------------------------------------------------------
# Force mot de passe
# ---------------------------------------------------------------------------


class FakeHibpClient:
    """Fake du client HIBP pour tests isolés."""

    def __init__(self, compromised_suffixes: dict[str, int] | None = None) -> None:
        self._suffixes = compromised_suffixes or {}

    async def fetch_suffixes(self, prefix: str) -> dict[str, int]:
        return dict(self._suffixes)


class TestPasswordStrengthService:
    def _service(self, hibp: FakeHibpClient | None = None) -> PasswordStrengthService:
        return PasswordStrengthService(hibp_client=hibp or FakeHibpClient())

    async def test_weak_password_low_score(self) -> None:
        service = self._service()
        report = await service.check("1234")
        assert report.zxcvbn_score < 3

    async def test_strong_password_high_score(self) -> None:
        service = self._service()
        report = await service.check("Tr0ub4dour&3$skY!waffles")
        assert report.zxcvbn_score >= 3

    async def test_compromised_password_detected(self) -> None:
        import hashlib

        password = "password"
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        suffix = sha1[5:]
        hibp = FakeHibpClient({suffix: 1000})
        service = self._service(hibp)
        report = await service.check(password)
        assert report.is_compromised is True
        assert report.compromise_count == 1000

    async def test_validate_raises_on_compromised(self) -> None:
        import hashlib

        password = "password"
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        suffix = sha1[5:]
        hibp = FakeHibpClient({suffix: 1000})
        service = self._service(hibp)
        with pytest.raises(CompromisedPasswordError):
            await service.validate(password)

    async def test_validate_raises_on_weak(self) -> None:
        service = self._service()
        with pytest.raises(WeakPasswordError) as exc_info:
            await service.validate("abc")
        assert exc_info.value.score < exc_info.value.minimum

    async def test_validate_passes_strong_password(self) -> None:
        service = self._service()
        report = await service.validate("Tr0ub4dour&3$skY!waffles")
        assert report.zxcvbn_score >= 3

    async def test_check_tolerates_hibp_unavailability(self) -> None:
        class FailingHibpClient:
            async def fetch_suffixes(self, prefix: str) -> dict[str, int]:
                del prefix
                raise httpx.ConnectError("HIBP indisponible")

        service = self._service(FailingHibpClient())  # type: ignore[arg-type]
        report = await service.check("un-mot-de-passe-quelconque")

        assert report.is_compromised is False
        assert report.compromise_count == 0
