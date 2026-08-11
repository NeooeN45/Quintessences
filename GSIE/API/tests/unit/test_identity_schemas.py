"""Tests des contrats Pydantic publics de l'identité."""

import pytest
from pydantic import ValidationError

from gsie_api.auth.schemas import GoogleLoginRequest, LocalLoginRequest, RegistrationRequest


def should_normalize_registration_email_and_trim_display_name() -> None:
    request = RegistrationRequest(
        email=" Forestier@Example.FR ",
        password="mot-de-passe-long-et-unique",
        display_name="  Forestier Test  ",
    )

    assert str(request.email) == "forestier@example.fr"
    assert request.display_name == "Forestier Test"


@pytest.mark.parametrize("password", ["court", "x" * 129])
def should_reject_registration_password_outside_security_bounds(password: str) -> None:
    with pytest.raises(ValidationError):
        RegistrationRequest(email="forestier@example.fr", password=password)


def should_forbid_unknown_login_fields() -> None:
    with pytest.raises(ValidationError):
        LocalLoginRequest(
            email="forestier@example.fr",
            password="mot-de-passe-long-et-unique",
            admin=True,
        )


def should_hide_google_token_from_model_representation() -> None:
    request = GoogleLoginRequest(
        id_token="secret-google-token",
        nonce="nonce-attendu-avec-au-moins-32-caracteres",
    )

    assert "secret-google-token" not in repr(request)
