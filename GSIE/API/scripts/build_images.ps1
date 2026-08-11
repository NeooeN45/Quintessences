<#
.SYNOPSIS
Construit les images GSIE avec une autorité de certification locale optionnelle.

.DESCRIPTION
Les antivirus ou proxies qui inspectent HTTPS peuvent signer les téléchargements
avec une autorité absente des images Debian. Le certificat est monté par BuildKit
comme secret éphémère : il ne doit jamais être commité ni passé en ARG/ENV.

Le script ne désactive jamais la validation TLS. Sans -CaFile, le build utilise
le magasin standard de Debian.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$CaFile,

    [switch]$Pull
)

$ErrorActionPreference = "Stop"
$apiRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoRoot = (Resolve-Path (Join-Path $apiRoot "..\..")).Path

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker est requis pour construire les images GSIE."
}

$buildOptions = @()
if ($Pull) {
    $buildOptions += "--pull"
}
if ($CaFile) {
    $resolvedCa = (Resolve-Path -LiteralPath $CaFile -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolvedCa -PathType Leaf)) {
        throw "Le fichier d'autorité de certification est introuvable : $CaFile"
    }
    $buildOptions += "--secret"
    $buildOptions += "id=gsie_host_ca,src=$resolvedCa"
}

Write-Host "Construction de api-db..."
$dbArgs = @("build") + $buildOptions + @("-t", "api-db:latest", "-f", "Dockerfile.db", ".")
Push-Location $apiRoot
try {
    & docker @dbArgs
    if ($LASTEXITCODE -ne 0) { throw "La construction de api-db a échoué (code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}

Write-Host "Construction de api-api..."
$apiArgs = @("build") + $buildOptions + @("-t", "api-api:latest", "-f", "GSIE/API/Dockerfile", ".")
Push-Location $repoRoot
try {
    & docker @apiArgs
    if ($LASTEXITCODE -ne 0) { throw "La construction de api-api a échoué (code $LASTEXITCODE)." }
    & docker tag api-api:latest api-outbox-worker:latest
    if ($LASTEXITCODE -ne 0) { throw "Le marquage de l'image outbox-worker a échoué (code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}

Write-Host "Images construites : api-db:latest, api-api:latest, api-outbox-worker:latest"
