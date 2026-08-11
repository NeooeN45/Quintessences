# Demarrage du tunnel Cloudflare nommé — GSIE API
# DEC-000028 : exposition publique sécurisée via Cloudflare Tunnel
#
# Prérequis :
#   1. Le tunnel a ete configure via setup-tunnel.ps1
#   2. L'API GSIE tourne sur http://127.0.0.1:8000
#
# Usage :
#   .\cloudflared\start-tunnel.ps1

$ErrorActionPreference = "Stop"
$CLOUDFLARED = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$TUNNEL_NAME = "gsie-api"
$CONFIG_FILE = "E:\Projets\Quintessences\GSIE\API\cloudflared\config.yml"

Write-Host "=== Demarrage du tunnel Cloudflare : $TUNNEL_NAME ===" -ForegroundColor Cyan
Write-Host "API locale : http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host "URL publique : https://api.quintessences-platform.com" -ForegroundColor Gray
Write-Host ""

# Verification que l'API repond
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "API GSIE : $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "ATTENTION : L'API GSIE ne repond pas sur http://127.0.0.1:8000" -ForegroundColor Red
    Write-Host "Demarrez l'API avant le tunnel." -ForegroundColor Yellow
    exit 1
}

# Demarrage du tunnel
Write-Host "Demarrage du tunnel... (Ctrl+C pour arreter)" -ForegroundColor Yellow
& $CLOUDFLARED --config $CONFIG_FILE tunnel run $TUNNEL_NAME
