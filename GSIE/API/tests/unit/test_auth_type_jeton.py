"""Un jeton de rafraîchissement n'ouvre aucun endpoint protégé.

`verify_token` contrôle la revendication `type`, et `get_current_user` exige
`access`. Ce garde existait mais n'était couvert par aucun test : un audit par
mutation a montré qu'on pouvait le supprimer sans qu'un seul des tests ne
tombe. Un contrôle d'authentification que rien ne surveille est un contrôle en
sursis — ces tests le verrouillent.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from gsie_api.core.auth import (
    create_access_token,
    create_mfa_challenge_token,
    create_mfa_setup_token,
    create_refresh_token,
    get_current_user_or_mfa_setup,
    verify_token,
)


def test_should_reject_reserved_claims_in_mfa_challenge_token() -> None:
    """create_mfa_challenge_token ne doit pas laisser écraser ses claims réservés."""
    with pytest.raises(ValueError, match="Reserved JWT claims cannot be overridden"):
        create_mfa_challenge_token(subject="forestier", claims={"type": "access"})


def test_un_jeton_de_rafraichissement_est_refuse_comme_acces() -> None:
    jeton = create_refresh_token(subject="forestier")

    with pytest.raises(HTTPException) as erreur:
        verify_token(jeton, expected_type="access")

    assert erreur.value.status_code == 401
    assert "access" in str(erreur.value.detail)


def test_un_jeton_d_acces_est_refuse_comme_rafraichissement() -> None:
    """La confusion doit être refusée dans les deux sens."""
    jeton = create_access_token(subject="forestier")

    with pytest.raises(HTTPException) as erreur:
        verify_token(jeton, expected_type="refresh")

    assert erreur.value.status_code == 401


def test_chaque_jeton_est_accepte_dans_son_role() -> None:
    """Témoin : le refus ci-dessus tient au type, pas à un jeton invalide."""
    assert (
        verify_token(create_access_token(subject="f"), expected_type="access")["type"] == "access"
    )
    assert (
        verify_token(create_refresh_token(subject="f"), expected_type="refresh")["type"]
        == "refresh"
    )


def test_create_mfa_setup_token_rejette_les_claims_reserves() -> None:
    with pytest.raises(ValueError, match="Reserved JWT claims cannot be overridden"):
        create_mfa_setup_token(subject="admin-sans-mfa", claims={"type": "access"})


def test_create_mfa_setup_token_fusionne_des_claims_additionnels() -> None:
    jeton = create_mfa_setup_token(subject="admin-sans-mfa", claims={"login_key": "admin@ex.fr"})

    payload = verify_token(jeton, expected_type="mfa_setup_required")

    assert payload["login_key"] == "admin@ex.fr"


def test_un_jeton_de_bootstrap_mfa_est_refuse_comme_acces() -> None:
    """Le jeton restreint émis à un admin sans MFA (ROADMAP — MFA admin) ne
    doit ouvrir aucune route protégée par `get_current_user` (RBAC compris),
    seulement `/mfa/setup` et `/mfa/verify` via `get_current_user_or_mfa_setup`.
    """
    jeton = create_mfa_setup_token(subject="admin-sans-mfa")

    with pytest.raises(HTTPException) as erreur:
        verify_token(jeton, expected_type="access")

    assert erreur.value.status_code == 401


async def test_get_current_user_or_mfa_setup_accepte_les_deux_types() -> None:
    """La dependency dédiée à /mfa/setup et /mfa/verify accepte un token
    d'accès normal ET le token restreint de bootstrap MFA."""
    acces = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=create_access_token(subject="forestier")
    )
    bootstrap = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=create_mfa_setup_token(subject="admin-sans-mfa")
    )

    payload_acces = await get_current_user_or_mfa_setup(acces)
    payload_bootstrap = await get_current_user_or_mfa_setup(bootstrap)

    assert payload_acces["type"] == "access"
    assert payload_bootstrap["type"] == "mfa_setup_required"
    assert payload_bootstrap["sub"] == "admin-sans-mfa"


async def test_get_current_user_or_mfa_setup_refuse_un_refresh_token() -> None:
    """Ni access ni mfa_setup_required : un refresh token reste refusé."""
    refresh = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=create_refresh_token(subject="forestier")
    )

    with pytest.raises(HTTPException) as erreur:
        await get_current_user_or_mfa_setup(refresh)

    assert erreur.value.status_code == 401


async def test_get_current_user_or_mfa_setup_refuse_credentials_absentes() -> None:
    with pytest.raises(HTTPException) as erreur:
        await get_current_user_or_mfa_setup(None)

    assert erreur.value.status_code == 401
