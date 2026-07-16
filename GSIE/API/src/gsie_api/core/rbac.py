"""RBAC — Contrôle d'accès basé sur les rôles par type de resource.

Vérifie le claim `roles` du JWT et restreint l'accès selon le type de
resource et l'action demandée (read, write, delete, admin, rgpd_manager).

Rôles :
- reader : lecture sur tous les types publics
- writer : lecture + écriture sur les types non-RGPD
- admin : tous droits sur tous les types
- rgpd_manager : accès aux types RGPD (consent, data_subject, sensitivity_classification)

Types RGPD (nécessitent rgpd_manager ou admin) :
- consent (63)
- data_subject (64)
- sensitivity_classification (type 41)

Types publics (accessibles à reader) :
- Tous les autres types (assertion, observation, concept, place, etc.)
"""

from typing import Any

from fastapi import HTTPException, status

# Types RGPD — nécessitent le rôle rgpd_manager ou admin
_RGPD_TYPES: frozenset[str] = frozenset(
    {
        "consent",
        "data_subject",
        "sensitivity_classification",
        "access_policy",
    }
)

# Actions possibles
_ACTIONS: frozenset[str] = frozenset({"read", "write", "delete", "admin", "export"})


def _get_user_roles(user: dict[str, Any]) -> set[str]:
    """Extrait les rôles du payload JWT."""
    roles = user.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    return set(roles)


def check_permission(
    user: dict[str, Any],
    resource_type: str,
    action: str,
) -> None:
    """Vérifie que l'utilisateur a la permission d'effectuer l'action.

    Args:
        user: Payload du JWT (contient sub, roles, etc.).
        resource_type: Type de resource (ex. "assertion", "consent").
        action: Action demandée ("read", "write", "delete", "export").

    Raises:
        HTTPException 403 si l'utilisateur n'a pas la permission.
    """
    roles = _get_user_roles(user)

    # admin a tous les droits
    if "admin" in roles:
        return

    # Vérification des types RGPD
    if resource_type in _RGPD_TYPES and "rgpd_manager" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(f"Access to {resource_type} requires rgpd_manager or admin role"),
        )

    # Vérification des actions d'écriture
    is_write_action = action in ("write", "delete", "export")
    if is_write_action and "writer" not in roles and "rgpd_manager" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} action requires writer, rgpd_manager or admin role",
        )


def require_roles(*required_roles: str) -> Any:
    """Dependency factory — exige un des rôles spécifiés.

    Usage :
        @router.get("/admin-only")
        async def admin_endpoint(
            user: dict = Depends(get_current_user),
            _: None = Depends(require_roles("admin")),
        ):
            ...
    """

    async def _check(user: dict[str, Any]) -> None:
        roles = _get_user_roles(user)
        if not any(r in roles for r in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_roles)}",
            )

    return _check
