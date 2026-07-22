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

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status

from gsie_api.core.auth import get_current_user

# Types RGPD — nécessitent le rôle rgpd_manager ou admin
RGPD_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "consent",
        "data_subject",
        "sensitivity_classification",
        "access_policy",
    }
)

# Alias temporaire pour compatibilité des imports historiques.
_RGPD_TYPES = RGPD_RESOURCE_TYPES

# Actions possibles
_ACTIONS: frozenset[str] = frozenset({"read", "write", "delete", "admin", "export"})


def get_user_roles(user: dict[str, Any]) -> set[str]:
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
    roles = get_user_roles(user)
    if action not in _ACTIONS:
        raise ValueError(f"Unknown RBAC action: {action}")

    # admin a tous les droits
    if "admin" in roles:
        return

    # Vérification des types RGPD
    if resource_type in RGPD_RESOURCE_TYPES and "rgpd_manager" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(f"Access to {resource_type} requires rgpd_manager or admin role"),
        )

    # Toute lecture exige un role explicite. Un JWT valide sans autorisation
    # n'accorde aucun droit implicite.
    if action == "read" and not roles.intersection({"reader", "writer", "rgpd_manager"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="read action requires reader, writer, rgpd_manager or admin role",
        )

    # Vérification des actions d'écriture
    is_write_action = action in ("write", "delete", "export")
    if is_write_action and "writer" not in roles and "rgpd_manager" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} action requires writer, rgpd_manager or admin role",
        )


def can_access_resource(
    user: dict[str, Any],
    resource_type: str,
    action: str = "read",
) -> bool:
    """Retourne la décision RBAC sans convertir un refus en erreur HTTP."""
    try:
        check_permission(user, resource_type, action)
    except HTTPException:
        return False
    return True


def require_permission(resource_type: str, action: str = "read") -> Any:
    """Dependency factory — exige une permission RBAC sur un type logique.

    Les moteurs utilisent le type logique ``engine`` pour appliquer la même
    politique que le CRUD : reader pour la lecture, writer/rgpd_manager pour
    l'écriture, et admin pour toutes les actions.
    """

    async def _check(
        user: Annotated[dict[str, Any], Depends(get_current_user)],
    ) -> dict[str, Any]:
        check_permission(user, resource_type, action)
        return user

    return _check


EngineReadUser = Annotated[dict[str, Any], Depends(require_permission("engine", "read"))]
EngineWriteUser = Annotated[dict[str, Any], Depends(require_permission("engine", "write"))]


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

    async def _check(
        user: Annotated[dict[str, Any], Depends(get_current_user)],
    ) -> dict[str, Any]:
        roles = get_user_roles(user)
        if not any(r in roles for r in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_roles)}",
            )
        return user

    return _check
