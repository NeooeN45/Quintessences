"""Tests unitaires — couverture résiduelle core/auth.py (clés de dev).

Couvre les lignes manquantes :
- 48-49 : _load_private_key quand fichier absent en non-prod (warning + dev key)
- 60-61 : _load_public_key quand fichier absent en non-prod (warning + dev key)
- 71-81 : _generate_dev_private_key (génération RSA 2048 première fois)
- 87-102 : _generate_dev_public_key (dérivation publique première fois)
- 46 : _load_private_key en production sans fichier (RuntimeError)
- 58 : _load_public_key en production sans fichier (RuntimeError)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gsie_api.core import auth


class TestLoadPrivateKeyDevFallback:
    """Couverture lignes 48-49 — fallback clé privée de dev."""

    def should_use_dev_key_when_file_missing_in_non_prod(self) -> None:
        """En non-prod, si le fichier clé privée n'existe pas, génère une clé de dev."""
        with (
            patch.object(auth._settings, "jwt_private_key_path", "/nonexistent/private.pem"),
            patch.object(auth._settings, "environment", "development"),
            patch.object(auth, "_dev_private_key", None),
        ):
            key = auth._load_private_key()
            assert "BEGIN PRIVATE KEY" in key

    def should_raise_runtime_error_when_file_missing_in_production(self) -> None:
        """Couverture ligne 46 — en production sans fichier, lève RuntimeError."""
        with (
            patch.object(auth._settings, "jwt_private_key_path", "/nonexistent/private.pem"),
            patch.object(auth._settings, "environment", "production"),
            pytest.raises(RuntimeError, match="JWT private key not found"),
        ):
            auth._load_private_key()


class TestLoadPublicKeyDevFallback:
    """Couverture lignes 60-61 — fallback clé publique de dev."""

    def should_use_dev_key_when_file_missing_in_non_prod(self) -> None:
        """En non-prod, si le fichier clé publique n'existe pas, dérive la clé de dev."""
        with (
            patch.object(auth._settings, "jwt_public_key_path", "/nonexistent/public.pem"),
            patch.object(auth._settings, "environment", "development"),
            patch.object(auth, "_dev_private_key", None),
            patch.object(auth, "_dev_public_key", None),
        ):
            key = auth._load_public_key()
            assert "BEGIN PUBLIC KEY" in key

    def should_raise_runtime_error_when_file_missing_in_production(self) -> None:
        """Couverture ligne 58 — en production sans fichier, lève RuntimeError."""
        with (
            patch.object(auth._settings, "jwt_public_key_path", "/nonexistent/public.pem"),
            patch.object(auth._settings, "environment", "production"),
            pytest.raises(RuntimeError, match="JWT public key not found"),
        ):
            auth._load_public_key()


class TestGenerateDevPrivateKey:
    """Couverture lignes 71-81 — génération RSA 2048."""

    def should_generate_rsa_private_key_on_first_call(self) -> None:
        """_generate_dev_private_key génère une clé PEM RSA 2048 à la première invocation."""
        with patch.object(auth, "_dev_private_key", None):
            key = auth._generate_dev_private_key()
            assert "BEGIN PRIVATE KEY" in key
            assert key.rstrip().endswith("END PRIVATE KEY-----")

    def should_cache_private_key_on_second_call(self) -> None:
        """La seconde invocation retourne la même clé (cache global)."""
        with patch.object(auth, "_dev_private_key", None):
            key1 = auth._generate_dev_private_key()
            key2 = auth._generate_dev_private_key()
            assert key1 == key2


class TestGenerateDevPublicKey:
    """Couverture lignes 87-102 — dérivation clé publique depuis la privée."""

    def should_derive_public_key_from_private_on_first_call(self) -> None:
        """_generate_dev_public_key dérive la clé publique de la clé privée de dev."""
        with (
            patch.object(auth, "_dev_private_key", None),
            patch.object(auth, "_dev_public_key", None),
        ):
            pub_key = auth._generate_dev_public_key()
            assert "BEGIN PUBLIC KEY" in pub_key

    def should_cache_public_key_on_second_call(self) -> None:
        """La seconde invocation retourne la même clé (cache global)."""
        with (
            patch.object(auth, "_dev_private_key", None),
            patch.object(auth, "_dev_public_key", None),
        ):
            pub1 = auth._generate_dev_public_key()
            pub2 = auth._generate_dev_public_key()
            assert pub1 == pub2


class TestDevKeyRoundTrip:
    """Vérifie que les clés de dev générées permettent un round-trip JWT."""

    def should_create_and_verify_token_with_dev_keys(self) -> None:
        """Un token créé avec les clés de dev doit être vérifiable avec la clé publique de dev."""
        with (
            patch.object(auth._settings, "jwt_private_key_path", "/nonexistent/private.pem"),
            patch.object(auth._settings, "jwt_public_key_path", "/nonexistent/public.pem"),
            patch.object(auth._settings, "environment", "development"),
            patch.object(auth, "_dev_private_key", None),
            patch.object(auth, "_dev_public_key", None),
        ):
            token = auth.create_access_token(subject="test-user")
            payload = auth.verify_token(token, expected_type="access")
            assert payload["sub"] == "test-user"
            assert payload["type"] == "access"
