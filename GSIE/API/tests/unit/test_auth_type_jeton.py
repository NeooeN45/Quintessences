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

from gsie_api.core.auth import create_access_token, create_refresh_token, verify_token


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
