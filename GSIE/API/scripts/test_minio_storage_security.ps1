<#!
.SYNOPSIS
    Vérifie le stockage MinIO de développement sans conserver de secret.

.DESCRIPTION
    Génère des identifiants de test seulement pour le processus courant, démarre
    MinIO et minio-init, puis vérifie :
      - le compte API peut écrire, lire et supprimer dans gsie-assets ;
      - le compte API est refusé sur un autre bucket ;
      - l'upload réel via S3Storage fonctionne avec le compte runtime.

    Pré-requis : Docker Desktop démarré et environnement Python GSIE disponible.
    Les conteneurs de test sont arrêtés à la fin. Les volumes sont conservés pour
    inspection et peuvent être supprimés explicitement avec Docker Compose.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function New-TestSecret {
    param([int]$ByteCount = 48)

    $bytes = [byte[]]::new($ByteCount)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes)
}

$composeFile = Join-Path $PSScriptRoot '..\docker-compose.yml'
$apiRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $apiRoot '.venv\Scripts\python.exe'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker est requis pour ce smoke test.'
}
if (-not (Test-Path $python)) {
    throw "Environnement Python introuvable : $python"
}

$env:GSIE_MINIO_ROOT_USER = 'gsie-minio-root-audit'
$env:GSIE_MINIO_ROOT_PASSWORD = New-TestSecret
$env:GSIE_OBJECT_STORAGE_S3_ACCESS_KEY = 'gsie-minio-api-audit'
$env:GSIE_OBJECT_STORAGE_S3_SECRET_KEY = New-TestSecret
$env:GSIE_DB_PASSWORD = New-TestSecret 32
$env:GSIE_API_DB_PASSWORD = New-TestSecret 32
$env:GSIE_VIZ_DB_PASSWORD = New-TestSecret 32
$env:GSIE_REDIS_PASSWORD = New-TestSecret 32
$env:PGBACKREST_REPO1_CIPHER_PASS = New-TestSecret
$env:GSIE_ENVIRONMENT = 'development'

Push-Location $apiRoot
try {
    & docker compose -f $composeFile up -d minio minio-init
    if ($LASTEXITCODE -ne 0) { throw 'Échec du démarrage MinIO/minio-init.' }

    $pythonCode = @'
import asyncio
from io import BytesIO

from gsie_api.infrastructure.object_storage import S3Storage


async def main() -> None:
    storage = S3Storage(
        endpoint="http://127.0.0.1:9000",
        access_key="__ACCESS_KEY__",
        secret_key="__SECRET_KEY__",
        bucket="gsie-assets",
    )
    key = "audit-security/smoke.txt"
    await storage.put(key, BytesIO(b"gsie-minio-security-smoke"), "text/plain")
    content = await storage.get(key)
    assert content.read() == b"gsie-minio-security-smoke"
    assert await storage.delete(key) is True


asyncio.run(main())
'@
    $pythonCode = $pythonCode.Replace('__ACCESS_KEY__', $env:GSIE_OBJECT_STORAGE_S3_ACCESS_KEY)
    $pythonCode = $pythonCode.Replace('__SECRET_KEY__', $env:GSIE_OBJECT_STORAGE_S3_SECRET_KEY)
    & $python -c $pythonCode
    if ($LASTEXITCODE -ne 0) { throw 'Échec de l’upload S3Storage réel.' }

    & docker compose -f $composeFile exec -T minio-init sh -c @'
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing local/audit-denied
mc alias set runtime http://minio:9000 "$GSIE_OBJECT_STORAGE_S3_ACCESS_KEY" "$GSIE_OBJECT_STORAGE_S3_SECRET_KEY"
if mc ls runtime/audit-denied; then
  echo "Le compte runtime accède à un bucket non autorisé."
  exit 1
fi
'@
    if ($LASTEXITCODE -ne 0) { throw 'Isolation du compte MinIO non démontrée.' }

    Write-Host 'Smoke test MinIO sécurité réussi.'
}
finally {
    & docker compose -f $composeFile stop minio minio-init | Out-Null
    Pop-Location
}
