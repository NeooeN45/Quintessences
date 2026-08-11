# Verification de mise a jour manuelle de cloudflared (Windows)
# cloudflared ne se met pas a jour automatiquement sur Windows.
# Ce script compare la version locale a la derniere release GitHub.

$ErrorActionPreference = "Stop"
$CLOUDFLARED = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$RELEASES_URL = "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"

Write-Host "=== Verification de cloudflared ===" -ForegroundColor Cyan

# Version locale
$localVersion = & $CLOUDFLARED --version 2>&1 | ForEach-Object { if ($_ -match "cloudflared version (\S+)") { $matches[1] } }
if (-not $localVersion) {
    Write-Host "ERREUR : impossible de lire la version locale de cloudflared" -ForegroundColor Red
    exit 1
}
Write-Host "Version locale : $localVersion" -ForegroundColor Gray

# Derniere version disponible
try {
    $release = Invoke-RestMethod -Uri $RELEASES_URL -UseBasicParsing -TimeoutSec 15
    $latestVersion = $release.tag_name -replace "^v", ""
    Write-Host "Derniere version : $latestVersion" -ForegroundColor Gray
} catch {
    Write-Host "AVERTISSEMENT : impossible de contacter GitHub ($($_.Exception.Message))" -ForegroundColor Yellow
    exit 0
}

# Comparaison
if ($localVersion -eq $latestVersion) {
    Write-Host "cloudflared est a jour." -ForegroundColor Green
} else {
    Write-Host "Mise a jour disponible : $localVersion -> $latestVersion" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour mettre a jour :" -ForegroundColor Cyan
    Write-Host "  1. Telecharger la derniere version :"
    Write-Host "     https://github.com/cloudflare/cloudflared/releases/latest"
    Write-Host "  2. Arreter le tunnel en cours."
    Write-Host "  3. Remplacer l'executable a : $CLOUDFLARED"
    Write-Host "  4. Relancer le tunnel : .\GSIE\API\cloudflared\start-tunnel.ps1"
}
