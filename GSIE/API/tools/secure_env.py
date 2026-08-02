#!/usr/bin/env python3
"""Chiffrement/déchiffrement du fichier .env (audit sécurité P1-1).

Le fichier ``.env`` contient des secrets en clair (clé API Météo-France,
mots de passe DB/Redis). Ce outil les chiffre avec Fernet (AES-128-CBC +
HMAC-SHA256) via la librairie ``cryptography``.

La clé Fernet est stockée hors du repo, dans
``%USERPROFILE%\\.config\\gsie\\env.key`` (Windows) ou
``~/.config/gsie/env.key`` (Linux/macOS). Elle n'est jamais commitée.

Usage :
    python tools/secure_env.py encrypt   # .env → .env.enc (supprime .env)
    python tools/secure_env.py decrypt   # .env.enc → .env (pour debug)
    python tools/secure_env.py status    # affiche l'état des fichiers
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path

# Force UTF-8 sur stdout/stderr (Windows console utilise cp1252 par défaut).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from cryptography.fernet import Fernet  # noqa: E402

# Répertoire de la clé — hors du repo, dans le profil utilisateur.
_KEY_DIR = Path.home() / ".config" / "gsie"
_KEY_FILE = _KEY_DIR / "env.key"

# Fichiers dans le répertoire de l'API.
_API_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _API_DIR / ".env"
_ENV_ENC_FILE = _API_DIR / ".env.enc"


def _ensure_key() -> bytes:
    """Charge ou génère la clé Fernet (stockée hors du repo)."""
    _KEY_DIR.mkdir(parents=True, exist_ok=True)
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    # Permissions restrictives (best-effort sur Windows).
    with contextlib.suppress(OSError):
        _KEY_FILE.chmod(0o600)
    print(f"Clé Fernet générée : {_KEY_FILE}")
    return key


def encrypt() -> int:
    """Chiffre .env → .env.enc et supprime le plaintext."""
    if not _ENV_FILE.exists():
        print("Erreur : .env introuvable — rien à chiffrer.", file=sys.stderr)
        return 1
    if _ENV_ENC_FILE.exists():
        print("Attention : .env.enc existe déjà — écrasement.", file=sys.stderr)

    key = _ensure_key()
    fernet = Fernet(key)

    plaintext = _ENV_FILE.read_bytes()
    ciphertext = fernet.encrypt(plaintext)
    _ENV_ENC_FILE.write_bytes(ciphertext)

    _ENV_FILE.unlink()
    print(f".env chiffré → .env.enc ({len(plaintext)} → {len(ciphertext)} octets)")
    print(f"Plaintext .env supprimé. Clé : {_KEY_FILE}")
    return 0


def decrypt() -> int:
    """Déchiffre .env.enc → .env (pour debug temporaire)."""
    if not _ENV_ENC_FILE.exists():
        print("Erreur : .env.enc introuvable — rien à déchiffrer.", file=sys.stderr)
        return 1
    if not _KEY_FILE.exists():
        print(f"Erreur : clé introuvable ({_KEY_FILE}).", file=sys.stderr)
        return 1

    fernet = Fernet(_KEY_FILE.read_bytes())
    ciphertext = _ENV_ENC_FILE.read_bytes()
    plaintext = fernet.decrypt(ciphertext)
    _ENV_FILE.write_bytes(plaintext)
    print(f".env.enc déchiffré → .env ({len(ciphertext)} → {len(plaintext)} octets)")
    print("Attention : .env est en clair sur disque — re-chiffre après usage.")
    return 0


def status() -> int:
    """Affiche l'état des fichiers .env / .env.enc / clé."""
    env_exists = _ENV_FILE.exists()
    enc_exists = _ENV_ENC_FILE.exists()
    key_exists = _KEY_FILE.exists()

    print(f"  .env      : {'présent (CLAIR)' if env_exists else 'absent'}")
    print(f"  .env.enc  : {'présent (chiffré)' if enc_exists else 'absent'}")
    print(f"  clé       : {'présente' if key_exists else 'absente'} ({_KEY_FILE})")

    if env_exists and not enc_exists:
        print("\n  ⚠ .env en clair — lancez : python tools/secure_env.py encrypt")
    elif env_exists and enc_exists:
        print("\n  ⚠ .env ET .env.enc présents — le plaintext devrait être supprimé.")
    elif not env_exists and enc_exists and key_exists:
        print("\n  ✓ Configuration sécurisée — .env.enc chiffré, clé présente.")
    elif not env_exists and enc_exists and not key_exists:
        print("\n  ✗ .env.enc présent mais clé absente — déchiffrement impossible.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chiffrement/déchiffrement du fichier .env (Fernet)."
    )
    parser.add_argument(
        "action",
        choices=["encrypt", "decrypt", "status"],
        help="encrypt : .env → .env.enc (supprime .env) | "
        "decrypt : .env.enc → .env (debug) | "
        "status : affiche l'état",
    )
    args = parser.parse_args()

    if args.action == "encrypt":
        return encrypt()
    elif args.action == "decrypt":
        return decrypt()
    else:
        return status()


if __name__ == "__main__":
    sys.exit(main())
