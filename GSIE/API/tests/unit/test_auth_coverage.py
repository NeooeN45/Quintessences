"""Tests unitaires — couverture résiduelle auth/router.py.

Couvre les lignes manquantes :
- 68, 70 : _get_dev_user quand dev_login désactivé ou credentials vides
- 114 : login quand dev_login désactivé (404)
- 152-159 : login success path
- 184-221 : refresh token (roles claim string/list/other)
- 242-249 : verify endpoint
- 277-286 : logout endpoint
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gsie_api.app import create_app
from gsie_api.auth import router as auth_router

if TYPE_CHECKING:
    from collections.abc import Generator

auth_router._settings.auth_dev_login_enabled = True
auth_router._settings.auth_dev_password = "changeme"


@pytest.fixture
def client(mock_lifespan: object) -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


async def should_validate_session_version_with_a_lazy_database_session() -> None:
    """Le validateur ouvre sa propre session uniquement quand il est sollicité."""
    session = MagicMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    repository = MagicMock()
    repository.is_session_version_current = AsyncMock(return_value=True)
    account_id = uuid4()

    with (
        patch.object(
            auth_router.database_infrastructure,
            "async_session_factory",
            return_value=context,
        ),
        patch.object(
            auth_router,
            "SqlAlchemyIdentityRepository",
            return_value=repository,
        ),
    ):
        assert await auth_router._is_session_version_current(account_id, 3) is True

    repository.is_session_version_current.assert_awaited_once_with(account_id, 3)


class TestGetDevUser:
    """Couverture de _get_dev_user — lignes 68, 70."""

    def should_return_none_when_dev_login_disabled(self) -> None:
        with patch.object(auth_router._settings, "auth_dev_login_enabled", False):
            result = auth_router._get_dev_user("admin", "changeme")
            assert result is None

    def should_return_none_when_credentials_not_configured(self) -> None:
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_username", ""),
        ):
            result = auth_router._get_dev_user("admin", "changeme")
            assert result is None

    def should_return_none_when_password_not_configured(self) -> None:
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_password", ""),
        ):
            result = auth_router._get_dev_user("admin", "changeme")
            assert result is None

    def should_return_user_when_credentials_valid(self) -> None:
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_username", "admin"),
            patch.object(auth_router._settings, "auth_dev_password", "changeme"),
        ):
            result = auth_router._get_dev_user("admin", "changeme")
            assert result is not None
            assert "admin" in result["roles"]

    def should_return_none_when_username_mismatch(self) -> None:
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_username", "admin"),
            patch.object(auth_router._settings, "auth_dev_password", "changeme"),
        ):
            result = auth_router._get_dev_user("other", "changeme")
            assert result is None

    def should_return_none_when_password_mismatch(self) -> None:
        with (
            patch.object(auth_router._settings, "auth_dev_login_enabled", True),
            patch.object(auth_router._settings, "auth_dev_username", "admin"),
            patch.object(auth_router._settings, "auth_dev_password", "changeme"),
        ):
            result = auth_router._get_dev_user("admin", "wrong")
            assert result is None


class TestLoginDisabled:
    """Couverture ligne 114 — login quand dev_login désactivé."""

    def should_return_404_when_dev_login_disabled(self, client: TestClient) -> None:
        with patch.object(auth_router._settings, "auth_dev_login_enabled", False):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "changeme"},
            )
            assert response.status_code == 404


class TestRefreshRolesEdgeCases:
    """Couverture lignes 194-199 — roles claim string/list/other.

    Mocke le refresh store pour accepter la rotation sans Redis ni
    enregistrement préalable du token.
    """

    def _mock_store(self):
        from unittest.mock import AsyncMock

        store = AsyncMock()
        store.register = AsyncMock()
        store.rotate = AsyncMock(return_value=True)
        store.consume = AsyncMock(return_value=True)
        return store

    def _login_and_refresh(
        self, client: TestClient, roles: list | str | None, username: str = "admin"
    ) -> int:
        """Login puis refresh avec un token ayant des roles personnalisés."""
        # Login d'abord pour obtenir un token valide
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme"},
        )
        assert login_resp.status_code == 200
        # Le refresh token du login a déjà les bons roles (admin)
        # On teste juste le refresh
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        return resp.status_code

    def should_handle_string_roles_claim(self, client: TestClient) -> None:
        """Un refresh token avec roles en string doit être accepté."""
        # Le login produit un token avec roles=["admin"] (liste)
        # On teste le path string en mockant verify_token
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": "admin", "username": "admin"},
        )
        # Override dependency au niveau de l'app
        from unittest.mock import AsyncMock

        from gsie_api.auth.router import get_refresh_token_store as _get_store

        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
        assert response.status_code == 200

    def should_handle_list_roles_claim(self, client: TestClient) -> None:
        """Un refresh token avec roles en liste doit être accepté."""
        from unittest.mock import AsyncMock

        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["admin", "writer"], "username": "admin"},
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
        assert response.status_code == 200

    def should_preserve_auth_provider_claim(self, client: TestClient) -> None:
        """Le refresh conserve le fournisseur de la session d'identité."""
        from unittest.mock import AsyncMock

        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token, verify_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={
                "roles": ["user"],
                "auth_provider": "google",
                "session_version": 1,
            },
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        mock_session_version = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        client.app.dependency_overrides[auth_router.get_session_version_validator] = (
            lambda: mock_session_version
        )
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
            client.app.dependency_overrides.pop(
                auth_router.get_session_version_validator,
                None,
            )

        payload = verify_token(response.json()["access_token"])
        assert response.status_code == 200
        assert payload["auth_provider"] == "google"
        assert payload["session_version"] == 1

    def should_handle_missing_roles_claim(self, client: TestClient) -> None:
        """Un refresh token sans roles doit être accepté (roles=[])."""
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"username": "admin"},
        )
        from unittest.mock import AsyncMock

        from gsie_api.auth.router import get_refresh_token_store as _get_store

        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
        assert response.status_code == 200

    def should_handle_non_string_roles_in_list(self, client: TestClient) -> None:
        """Un refresh token avec roles non-string dans la liste doit filtrer."""
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["admin", 123, True], "username": "admin"},
        )
        from unittest.mock import AsyncMock

        from gsie_api.auth.router import get_refresh_token_store as _get_store

        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
        assert response.status_code == 200

    def should_handle_non_list_roles_claim(self, client: TestClient) -> None:
        """Une valeur de rôles non textuelle devient une liste vide."""
        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": 42, "username": "admin"},
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

        assert response.status_code == 200

    def should_reject_an_already_used_refresh_token(self, client: TestClient) -> None:
        """La rotation atomique refuse tout rejeu du même refresh token."""
        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["user"]},
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=False)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token expired or already used"

    def should_return_401_when_subject_not_string(self, client: TestClient) -> None:
        """Un refresh token avec sub non-string doit être refusé."""
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["admin"]},
        )
        with patch("gsie_api.auth.router.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": 12345,  # non-string
                "jti": "test-jti",
                "exp": 9999999999,
                "type": "refresh",
                "roles": ["admin"],
            }
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        assert response.status_code == 401

    def should_return_401_when_jti_not_string(self, client: TestClient) -> None:
        """Un refresh token avec jti non-string doit être refusé."""
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["admin"]},
        )
        with patch("gsie_api.auth.router.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "test-user",
                "jti": None,  # non-string
                "exp": 9999999999,
                "type": "refresh",
                "roles": ["admin"],
            }
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        assert response.status_code == 401

    def should_return_401_when_identity_subject_is_not_a_uuid(
        self,
        client: TestClient,
    ) -> None:
        """Une session d'identité doit toujours porter un UUID de compte."""
        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject="identifiant-invalide",
            claims={"auth_provider": "google", "session_version": 1},
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token claims"

    def should_return_401_when_identity_session_is_revoked(
        self,
        client: TestClient,
    ) -> None:
        """Un changement sensible invalide les jetons de session antérieurs."""
        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token

        token = create_refresh_token(
            subject=str(uuid4()),
            claims={"auth_provider": "local", "session_version": 1},
        )
        mock_store = AsyncMock()
        mock_store.rotate = AsyncMock(return_value=True)
        validator = AsyncMock(return_value=False)
        client.app.dependency_overrides[_get_store] = lambda: mock_store
        client.app.dependency_overrides[auth_router.get_session_version_validator] = (
            lambda: validator
        )
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
        finally:
            client.app.dependency_overrides.pop(_get_store, None)
            client.app.dependency_overrides.pop(
                auth_router.get_session_version_validator,
                None,
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Session révoquée"


class TestVerifyEndpoint:
    """Couverture lignes 242-249 — verify endpoint."""

    def should_return_expires_at_when_token_valid(self, client: TestClient) -> None:
        """Le verify doit retourner expires_at pour un token valide."""
        from gsie_api.core.auth import create_access_token

        token = create_access_token(subject="test-user", claims={"roles": ["admin"]})
        response = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["expires_at"] is not None
        assert data["subject"] == "test-user"
        assert data["token_type"] == "access"


class TestLogoutEndpoint:
    """Couverture lignes 277-286 — logout endpoint."""

    def should_return_401_when_logout_with_invalid_refresh_token(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    def should_return_401_when_logout_with_access_token(self, client: TestClient) -> None:
        """Un access token n'est pas un refresh token — verify_token lève."""
        from gsie_api.core.auth import create_access_token

        token = create_access_token(subject="test", claims={"roles": ["admin"]})
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": token},
        )
        assert response.status_code == 401

    def should_return_401_when_logout_jti_is_not_text(self, client: TestClient) -> None:
        """Un jeton décodé sans JTI textuel reste inutilisable."""
        with patch("gsie_api.auth.router.verify_token") as mock_verify:
            mock_verify.return_value = {"jti": None, "type": "refresh"}
            response = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": "jeton-simulé"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token claims"

    def should_return_revoked_false_when_logout_twice(self, client: TestClient) -> None:
        from gsie_api.auth.refresh_tokens import MemoryRefreshTokenStore
        from gsie_api.auth.router import get_refresh_token_store as _get_store
        from gsie_api.core.auth import create_refresh_token, verify_token

        # Crée un refresh token valide
        token = create_refresh_token(
            subject=str(auth_router.DEV_USER_ID),
            claims={"roles": ["admin"], "username": "admin"},
        )
        payload = verify_token(token, expected_type="refresh")

        # Mock le store avec MemoryRefreshTokenStore
        store = MemoryRefreshTokenStore()
        # Enregistre le token manuellement via le mock
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(store.register(str(payload["jti"]), float(payload["exp"])))
        loop.close()

        client.app.dependency_overrides[_get_store] = lambda: store
        try:
            first = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": token},
            )
            assert first.status_code == 200
            assert first.json()["revoked"] is True

            second = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": token},
            )
            assert second.status_code == 200
            assert second.json()["revoked"] is False
        finally:
            client.app.dependency_overrides.pop(_get_store, None)


# ===========================================================================
# core/auth.py — reserved claims, production key errors, None token
# ===========================================================================


class TestCoreAuthReservedClaims:
    """Couverture lignes 128-129, 159-160 — reserved claims override."""

    def should_raise_when_access_token_claims_include_reserved(self) -> None:
        """create_access_token doit lever si claims contient des claims réservés."""
        from gsie_api.core.auth import create_access_token

        with pytest.raises(ValueError, match="Reserved JWT claims"):
            create_access_token(subject="test", claims={"sub": "override"})

    def should_raise_when_refresh_token_claims_include_reserved(self) -> None:
        """create_refresh_token doit lever si claims contient des claims réservés."""
        from gsie_api.core.auth import create_refresh_token

        with pytest.raises(ValueError, match="Reserved JWT claims"):
            create_refresh_token(subject="test", claims={"jti": "override"})


class TestCoreAuthProductionKeys:
    """Couverture lignes 46, 58 — RuntimeError en production si clé absente."""

    def should_raise_runtime_error_when_private_key_missing_in_production(self) -> None:
        """_load_private_key doit lever RuntimeError en production sans clé."""

        import gsie_api.core.auth as auth_module

        with (
            patch.object(auth_module._settings, "environment", "production"),
            patch.object(auth_module._settings, "jwt_private_key_path", "/nonexistent/key.pem"),
            pytest.raises(RuntimeError, match="JWT private key not found"),
        ):
            auth_module._load_private_key()

    def should_raise_runtime_error_when_public_key_missing_in_production(self) -> None:
        """_load_public_key doit lever RuntimeError en production sans clé."""
        import gsie_api.core.auth as auth_module

        with (
            patch.object(auth_module._settings, "environment", "production"),
            patch.object(auth_module._settings, "jwt_public_key_path", "/nonexistent/key.pem"),
            pytest.raises(RuntimeError, match="JWT public key not found"),
        ):
            auth_module._load_public_key()


class TestCoreAuthOptionalToken:
    """Couverture ligne 253 — verify_ws_token avec token=None."""

    async def should_return_none_when_token_is_none(self) -> None:
        """verify_ws_token doit retourner None quand token est None."""
        from gsie_api.core.auth import verify_ws_token

        assert await verify_ws_token(None) is None
