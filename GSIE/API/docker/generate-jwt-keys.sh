#!/bin/sh
# generate-jwt-keys.sh — génère une paire de clés RSA pour JWT RS256
#
# Usage :
#   ./docker/generate-jwt-keys.sh
#
# Crée keys/private.pem et keys/public.pem dans le répertoire courant.
# En production, ces clés doivent être stockées dans un secret manager
# (Vault, AWS Secrets Manager, etc.) et montées en lecture seule.

set -e

KEYS_DIR="keys"
PRIVATE_KEY="${KEYS_DIR}/private.pem"
PUBLIC_KEY="${KEYS_DIR}/public.pem"

mkdir -p "${KEYS_DIR}"

if [ -f "${PRIVATE_KEY}" ]; then
    echo "[jwt-keys] ${PRIVATE_KEY} existe déjà — abandon (écraser manuellement si besoin)."
    exit 1
fi

echo "[jwt-keys] Génération de la clé privée RSA 2048 bits..."
openssl genrsa -out "${PRIVATE_KEY}" 2048
chmod 600 "${PRIVATE_KEY}"

echo "[jwt-keys] Extraction de la clé publique..."
openssl rsa -in "${PRIVATE_KEY}" -pubout -out "${PUBLIC_KEY}"
chmod 644 "${PUBLIC_KEY}"

echo "[jwt-keys] Clés générées :"
echo "  Privée : ${PRIVATE_KEY} (600)"
echo "  Publique : ${PUBLIC_KEY} (644)"
echo ""
echo "[jwt-keys] Variables d'environnement à définir :"
echo "  GSIE_JWT_PRIVATE_KEY_PATH=${PRIVATE_KEY}"
echo "  GSIE_JWT_PUBLIC_KEY_PATH=${PUBLIC_KEY}"
