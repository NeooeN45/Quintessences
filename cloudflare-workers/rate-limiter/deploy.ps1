<#
.SYNOPSIS
    Déploie le Worker rate-limiter sur Cloudflare.

.DESCRIPTION
    1. Crée le namespace KV RATE_LIMITS s'il n'existe pas.
    2. Met à jour wrangler.toml avec les IDs du namespace.
    3. Déploie le Worker.
    4. Attache le Worker à la route `api.quintessences-platform.com/*`.

.PREREQUIS
    - Node.js >= 18
    - `npx wrangler` configuré (`wrangler login` ou variable CLOUDFLARE_API_TOKEN)

.EXAMPLE
    .\deploy.ps1 -CreateRoute
#>
[CmdletBinding()]
param(
    [switch]$CreateRoute,
    [string]$RoutePattern = "api.quintessences-platform.com/*"
)

$ErrorActionPreference = "Stop"
$WorkerDir = $PSScriptRoot
Set-Location $WorkerDir

# Vérifie wrangler
$wrangler = & npx --yes wrangler --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "wrangler non disponible. Lancez 'npm install -g wrangler' ou 'npx wrangler login'."
}

Write-Host "Création du namespace KV RATE_LIMITS si absent..." -ForegroundColor Cyan
$ns = npx wrangler kv:namespace list --json | ConvertFrom-Json | Where-Object { $_.title -eq "gsie-rate-limiter-RATE_LIMITS" }
if (-not $ns) {
    $create = npx wrangler kv:namespace create RATE_LIMITS --json | ConvertFrom-Json
    $ns = $create
    Write-Host "Namespace créé : $($ns.id)" -ForegroundColor Green
} else {
    Write-Host "Namespace existant : $($ns.id)" -ForegroundColor Green
}

$previewNs = npx wrangler kv:namespace list --preview --json | ConvertFrom-Json | Where-Object { $_.title -eq "gsie-rate-limiter-RATE_LIMITS_preview" }
if (-not $previewNs) {
    $previewCreate = npx wrangler kv:namespace create RATE_LIMITS --preview --json | ConvertFrom-Json
    $previewNs = $previewCreate
}

# Mise à jour de wrangler.toml
$toml = Get-Content wrangler.toml -Raw
$toml = $toml -replace 'id = "\{\{KV_NAMESPACE_ID\}\}"', "id = `"$($ns.id)`""
$toml = $toml -replace 'preview_id = "\{\{KV_PREVIEW_ID\}\}"', "preview_id = `"$($previewNs.id)`""
$toml | Set-Content wrangler.toml -NoNewline

Write-Host "Déploiement du Worker..." -ForegroundColor Cyan
npx wrangler deploy

if ($CreateRoute) {
    Write-Host "Attachement de la route $RoutePattern ..." -ForegroundColor Cyan
    $zoneId = "3133186ecc2ab4bad529337f21c1e5da"
    $scriptName = "gsie-rate-limiter"
    $body = @{
        pattern = $RoutePattern
        script  = $scriptName
    } | ConvertTo-Json
    $headers = @{ "Content-Type" = "application/json" }
    if ($env:CLOUDFLARE_API_TOKEN) {
        $headers["Authorization"] = "Bearer $($env:CLOUDFLARE_API_TOKEN)"
    } else {
        throw "CLOUDFLARE_API_TOKEN requis pour attacher la route."
    }
    Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/workers/routes" -Method Post -Headers $headers -Body $body
}

Write-Host "Déploiement terminé." -ForegroundColor Green
