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
    _ACTIONS,
    _RGPD_TYPES,
    PERSONAL_DATA_TYPES,
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
        for action in ("read", "write"):
            with pytest.raises(HTTPException) as exc:
                check_permission(user, "assertion", action)
            assert exc.value.status_code == 403

    def test_should_handle_string_roles_claim(self) -> None:
        """Le claim roles peut être une string unique (compat)."""
        user = {"sub": "admin1", "roles": "admin"}
        check_permission(user, "consent", "delete")  # ne lève pas

    def test_should_handle_missing_roles_claim(self) -> None:
        """Si le claim roles est absent, accès refusé."""
        user = {"sub": "norole1"}
        for action in ("read", "write"):
            with pytest.raises(HTTPException) as exc:
                check_permission(user, "assertion", action)
            assert exc.value.status_code == 403


class TestConstatERgpdManagerRestreint:
    """Le rgpd_manager ne peut écrire que sur les types RGPD.

    Audit 2026-08-01, constat E : sans cette restriction, un DPO au
    moindre privilège pouvait modifier ou supprimer tout le métamodèle.
    """

    def test_should_deny_rgpd_manager_write_on_non_rgpd_type(self) -> None:
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        for action in ("write", "delete", "export"):
            with pytest.raises(HTTPException) as exc:
                check_permission(user, "assertion", action)
            assert exc.value.status_code == 403

    def test_should_allow_rgpd_manager_write_on_rgpd_type(self) -> None:
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        for rtype in _RGPD_TYPES:
            check_permission(user, rtype, "write")  # ne lève pas

    def test_should_allow_rgpd_manager_read_on_non_rgpd_type(self) -> None:
        """La lecture reste ouverte : un DPO peut auditer le métamodèle."""
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        check_permission(user, "assertion", "read")  # ne lève pas


class TestConstatBPersonalDataTypes:
    """Les types portant des identifiants directs sont isolés du reader.

    Audit 2026-08-01, constat B : `agent` (nom, ORCID) est dans public
    sans RLS. `data_subject.agent_id` pointe vers lui : un reader
    reconstituait l'identité derrière un pseudonyme en un GET.

    Audit 2026-08-01, constat J : `resource_diff` conserve les
    old_value/new_value de chaque modification — le droit à l'effacement
    n'est pas honoré si un reader peut les lire.
    """

    def test_should_deny_reader_read_on_personal_data_types(self) -> None:
        user = {"sub": "reader1", "roles": ["reader"]}
        for rtype in PERSONAL_DATA_TYPES:
            with pytest.raises(HTTPException) as exc:
                check_permission(user, rtype, "read")
            assert exc.value.status_code == 403

    def test_should_allow_writer_read_on_personal_data_types(self) -> None:
        user = {"sub": "writer1", "roles": ["writer"]}
        for rtype in PERSONAL_DATA_TYPES:
            check_permission(user, rtype, "read")  # ne lève pas

    def test_should_allow_writer_write_on_agent(self) -> None:
        """Les writers peuvent créer des agents (provenance PROV-O)."""
        user = {"sub": "writer1", "roles": ["writer"]}
        check_permission(user, "agent", "write")  # ne lève pas

    def test_should_deny_rgpd_manager_write_on_agent(self) -> None:
        """Le rgpd_manager ne gère pas la provenance."""
        user = {"sub": "rgpd1", "roles": ["rgpd_manager"]}
        with pytest.raises(HTTPException) as exc:
            check_permission(user, "agent", "write")
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


class TestSortieFermee:
    """Aucune action n'est accordée par omission."""

    @pytest.mark.parametrize("action", sorted(_ACTIONS))
    def test_should_deny_every_action_to_a_user_without_role(self, action: str) -> None:
        """Un porteur de JWT sans rôle n'obtient rien, pour aucune action.

        Défaut vérifié avant correction : `admin` figurait dans `_ACTIONS` sans
        qu'aucune branche de `check_permission` l'évalue. Elle traversait donc la
        fonction et ressortait **autorisée** — pour un utilisateur sans aucun
        rôle, sur tout type non-RGPD. `read`, `write` et `delete` étaient bien
        refusées ; seule l'action dont le nom suggère le contrôle le plus fort
        ne l'était pas.

        Le paramétrage porte sur `_ACTIONS` et non sur une liste écrite à la
        main : c'est ce qui rend ce contrôle durable. La liste en dur de
        `TestCheckPermission` — `["read", "write", "delete", "export"]` — omettait
        exactement l'action fautive, et c'est ainsi que le trou a survécu. Toute
        action ajoutée à `_ACTIONS` sans branche dédiée fera désormais tomber ce
        test.
        """
        with pytest.raises(HTTPException) as exc:
            check_permission({"sub": "sans-role", "roles": []}, "entity", action)
        assert exc.value.status_code == 403

    @pytest.mark.parametrize("action", sorted(_ACTIONS))
    def test_should_grant_every_action_to_admin(self, action: str) -> None:
        """Le rôle `admin` conserve tous les droits.

        Sans ce contrôle, refuser tout ferait passer le test précédent — une
        fonction d'autorisation qui refuse tout le monde le satisfait.
        """
        check_permission({"sub": "admin1", "roles": ["admin"]}, "entity", action)

    def test_should_reject_an_unknown_action(self) -> None:
        """Une action hors du vocabulaire est une erreur de programmation.

        `ValueError` et non 403 : un appelant qui écrit `"writes"` a un bug, il
        ne se voit pas refuser un droit.
        """
        with pytest.raises(ValueError, match="Unknown RBAC action"):
            check_permission({"sub": "u", "roles": ["admin"]}, "entity", "writes")
