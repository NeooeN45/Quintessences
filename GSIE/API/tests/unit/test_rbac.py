"""Tests du RBAC — contrôle d'accès basé sur les rôles par type.

Vérifie que :
- reader peut lire tous les types publics
- writer peut écrire sur les types non-RGPD
- admin a tous les droits
- rgpd_manager peut accéder aux types RGPD
- reader/writer ne peuvent pas accéder aux types RGPD
- reader ne peut pas écrire
"""

import pytest
from fastapi import HTTPException

from gsie_api.core.rbac import (
    _RGPD_TYPES,
    check_permission,
    require_roles,
)


class TestCheckPermission:
    """Tests de la fonction check_permission."""

    @pytest.mark.parametrize("action", ["read", "write", "delete", "export"])
    def test_should_allow_admin_all_actions_on_all_types(self, action: str) -> None:
        user = {"sub": "admin1", "roles": ["admin"]}
        for rtype in ("assertion", "consent", "data_subject", "observation"):
            check_permission(user, rtype, action)  # ne lève pas

    @pytest.mark.parametrize("action", ["read", "write", "delete", "export"])
    def test_should_allow_reader_read_on_public_types(self, action: str) -> None:
        user = {"sub": "reader1", "roles": ["reader"]}
        if action == "read":
            check_permission(user, "assertion", action)  # OK
        else:
            with pytest.raises(HTTPException) as exc:
                check_permission(user, "assertion", action)
            assert exc.value.status_code == 403

    def test_should_deny_reader_access_to_rgpd_types(self) -> None:
        user = {"sub": "reader1", "roles": ["reader"]}
        for rtype in _RGPD_TYPES:
            with pytest.raises(HTTPException) as exc:
                check_permission(user, rtype, "read")
            assert exc.value.status_code == 403

    def test_should_allow_rgpd_manager_access_to_rgpd_types(self) -> None:
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        for rtype in _RGPD_TYPES:
            check_permission(user, rtype, "read")  # ne lève pas

    def test_should_allow_writer_write_on_public_types(self) -> None:
        user = {"sub": "writer1", "roles": ["writer"]}
        check_permission(user, "assertion", "write")  # ne lève pas
        check_permission(user, "observation", "delete")  # ne lève pas

    def test_should_deny_writer_access_to_rgpd_types(self) -> None:
        user = {"sub": "writer1", "roles": ["writer"]}
        with pytest.raises(HTTPException) as exc:
            check_permission(user, "consent", "write")
        assert exc.value.status_code == 403

    def test_should_allow_user_with_multiple_roles(self) -> None:
        user = {"sub": "multi1", "roles": ["reader", "writer"]}
        check_permission(user, "assertion", "read")  # OK via reader
        check_permission(user, "assertion", "write")  # OK via writer

    def test_should_deny_user_without_roles(self) -> None:
        user = {"sub": "norole1", "roles": []}
        with pytest.raises(HTTPException) as exc:
            check_permission(user, "assertion", "write")
        assert exc.value.status_code == 403

    def test_should_handle_string_roles_claim(self) -> None:
        """Le claim roles peut être une string unique (compat)."""
        user = {"sub": "admin1", "roles": "admin"}
        check_permission(user, "consent", "delete")  # ne lève pas

    def test_should_handle_missing_roles_claim(self) -> None:
        """Si le claim roles est absent, accès refusé."""
        user = {"sub": "norole1"}
        with pytest.raises(HTTPException) as exc:
            check_permission(user, "assertion", "write")
        assert exc.value.status_code == 403


class TestRequireRoles:
    """Tests de la dependency factory require_roles."""

    @pytest.mark.asyncio
    async def test_should_allow_user_with_required_role(self) -> None:
        check = require_roles("admin")
        user = {"sub": "admin1", "roles": ["admin"]}
        await check(user)  # ne lève pas

    @pytest.mark.asyncio
    async def test_should_deny_user_without_required_role(self) -> None:
        check = require_roles("admin")
        user = {"sub": "reader1", "roles": ["reader"]}
        with pytest.raises(HTTPException) as exc:
            await check(user)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_should_allow_user_with_any_of_required_roles(self) -> None:
        check = require_roles("admin", "rgpd_manager")
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        await check(user)  # ne lève pas (rgpd_manager suffit)
