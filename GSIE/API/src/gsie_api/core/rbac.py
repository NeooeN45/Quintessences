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

# Types RGPD — nécessitent le rôle rgpd_manager ou admin.
# Les migrations 0021 et 0023 ont déplacé data_subject_consent,
# rights_statement et spatial_disclosure_policy vers gsie_rgpd : ils
# portent des données personnelles ou des décisions d'accès et doivent
# être isolés du reader/writer ordinaires.
RGPD_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "consent",
        "data_subject",
        "sensitivity_classification",
        "access_policy",
        "rights_statement",
        "spatial_disclosure_policy",
    }
)

# Types portant des identifiants directs de personnes (nom, ORCID) ou
# des historiques de modification qui peuvent contenir d'anciennes
# valeurs de données personnelles.
#
# `agent` est une table de provenance (PROV-O), pas une table RGPD :
# elle reste dans `public` et les writers peuvent y écrire pour tracer
# l'origine des données. Mais `data_subject.agent_id` pointe vers elle,
# et un reader pouvait reconstituer « propriétaire forestier ↔
# géométrie de sa parcelle » en trois GET (audit 2026-08-01, constat B).
#
# `resource_diff` porte les old_value/new_value de chaque modification
# (champ `changes` JSONB). Quand une donnée personnelle est modifiée ou
# supprimée, le diff en conserve l'ancienne valeur : le droit à
# l'effacement n'est pas honoré si un reader peut le lire
# (audit 2026-08-01, constat J).
#
# La lecture est donc restreinte à writer/rgpd_manager/admin — pas reader.
PERSONAL_DATA_TYPES: frozenset[str] = frozenset({"agent", "resource_diff"})

# Alias temporaire pour compatibilité des imports historiques.
_RGPD_TYPES = RGPD_RESOURCE_TYPES

# Actions possibles
_ACTIONS: frozenset[str] = frozenset({"read", "write", "delete", "admin", "export"})

# Actions accordées à `writer` ou `rgpd_manager`.
_ACTIONS_ECRITURE: frozenset[str] = frozenset({"write", "delete", "export"})

# Actions que `check_permission` évalue par une branche dédiée. Toute action de
# `_ACTIONS` absente d'ici est refusée hors du rôle `admin` — c'est la seule
# lecture sûre d'un oubli. Le fait que ce soit `_ACTIONS - {"admin"}` n'est pas
# un hasard : `admin` est précisément l'action que seul le rôle `admin` obtient,
# et le retour anticipé de la ligne 72 s'en charge.
_ACTIONS_EVALUEES: frozenset[str] = frozenset({"read"}) | _ACTIONS_ECRITURE


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

    # Types portant des identifiants directs de personnes : un reader
    # ne peut pas les lire. `data_subject.agent_id` pointe vers `agent`
    # (nom, ORCID) — sans cette barrière, un reader reconstitue
    # l'identité derrière un pseudonyme (audit 2026-08-01, constat B).
    if (
        resource_type in PERSONAL_DATA_TYPES
        and action == "read"
        and not roles.intersection({"writer", "rgpd_manager"})
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Read access to {resource_type} requires writer, rgpd_manager or admin role",
        )

    # Toute lecture exige un role explicite. Un JWT valide sans autorisation
    # n'accorde aucun droit implicite.
    if action == "read" and not roles.intersection({"reader", "writer", "rgpd_manager"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="read action requires reader, writer, rgpd_manager or admin role",
        )

    # Vérification des actions d'écriture.
    #
    # `rgpd_manager` ne peut écrire que sur les types RGPD : son rôle est
    # de gérer les consentements et les politiques d'accès, pas le
    # métamodèle forestier. Sans cette restriction, un DPO au moindre
    # privilège pouvait modifier ou supprimer tout le métamodèle
    # (assertion, observation, place, etc.) — audit 2026-08-01, constat E.
    is_write_action = action in _ACTIONS_ECRITURE
    if is_write_action:
        if "writer" in roles:
            pass  # writer écrit sur les types non-RGPD (déjà vérifié ci-dessus)
        elif "rgpd_manager" in roles and resource_type in RGPD_RESOURCE_TYPES:
            pass  # rgpd_manager écrit sur les types RGPD uniquement
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"{action} action requires writer role"
                    + (" on non-RGPD types" if "rgpd_manager" in roles else "")
                    + ", rgpd_manager role on RGPD types, or admin role"
                ),
            )

    # Sortie fermée : toute action que les branches ci-dessus n'ont pas évaluée
    # est refusée, jamais accordée par défaut.
    #
    # `admin` figurait dans `_ACTIONS` sans qu'aucune branche la traite : elle
    # traversait donc la fonction et ressortait autorisée — pour un utilisateur
    # sans aucun rôle, sur tout type non-RGPD. Le seul retour de l'admin
    # (ligne 72) l'attrape déjà ; le trou concernait tous les autres.
    #
    # Vérifié : `read`, `write` et `delete` refusées pour un porteur de JWT sans
    # rôle, `admin` accordée. Aucun appelant n'employait l'action, mais une
    # fonction d'autorisation dont l'oubli accorde est un piège — d'autant que
    # le nom `admin` suggère le contrôle le plus fort.
    if action not in _ACTIONS_EVALUEES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} action requires the admin role",
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
