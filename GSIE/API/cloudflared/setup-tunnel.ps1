# Script de configuration du tunnel Cloudflare nommé — GSIE API
# DEC-000028 : exposition publique sécurisée via Cloudflare Tunnel
#
# Prérequis :
#   1. Le domaine quintessences-platform.com doit être acheté sur Cloudflare
#   2. L'API GSIE doit tourner sur http://127.0.0.1:8000
#
# Usage :
#   .\cloudflared\setup-tunnel.ps1

$ErrorActionPreference = "Stop"
$CLOUDFLARED = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$DOMAIN = "quintessences-platform.com"
$SUBDOMAIN = "api.$DOMAIN"
$TUNNEL_NAME = "gsie-api"
$CONFIG_DIR = "$env:USERPROFILE\.cloudflared"
$CONFIG_FILE = "E:\Projets\Quintessences\GSIE\API\cloudflared\config.yml"

Write-Host "=== Configuration du tunnel Cloudflare nommé ===" -ForegroundColor Cyan
Write-Host "Domaine : $DOMAIN"
Write-Host "Sous-domaine API : $SUBDOMAIN"
Write-Host "Tunnel : $TUNNEL_NAME"
Write-Host ""

# Vérification que cloudflared est installé
if (-not (Test-Path $CLOUDFLARED)) {
    Write-Host "ERREUR : cloudflared non trouve a $CLOUDFLARED" -ForegroundColor Red
    Write-Host "Telechargez-le depuis : https://github.com/cloudflare/cloudflared/releases/latest"
    exit 1
}

# Etape 1 : Authentification (ouvre le navigateur)
if (-not (Test-Path "$CONFIG_DIR\cert.pem")) {
    Write-Host "[1/4] Authentification Cloudflare..." -ForegroundColor Yellow
    Write-Host "  Une page navigateur va s'ouvrir. Selectionnez le domaine $DOMAIN" -ForegroundColor Gray
    & $CLOUDFLARED tunnel login
    if (-not (Test-Path "$CONFIG_DIR\cert.pem")) {
        Write-Host "ERREUR : Authentification echouee (cert.pem absent)" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK : cert.pem genere" -ForegroundColor Green
} else {
    Write-Host "[1/4] Authentification : deja faite (cert.pem present)" -ForegroundColor Green
}

# Etape 2 : Creation du tunnel nommé
$existingTunnel = & $CLOUDFLARED tunnel list 2>&1 | Select-String $TUNNEL_NAME
if ($existingTunnel) {
    Write-Host "[2/4] Tunnel '$TUNNEL_NAME' : deja cree" -ForegroundColor Green
} else {
    Write-Host "[2/4] Creation du tunnel '$TUNNEL_NAME'..." -ForegroundColor Yellow
    & $CLOUDFLARED tunnel create $TUNNEL_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERREUR : Echec de la creation du tunnel" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK : Tunnel cree" -ForegroundColor Green
}

# Etape 3 : Configuration DNS (CNAME vers le tunnel)
Write-Host "[3/4] Configuration DNS pour $SUBDOMAIN..." -ForegroundColor Yellow
& $CLOUDFLARED tunnel route dns $TUNNEL_NAME $SUBDOMAIN
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ATTENTION : Le route DNS a peut-etre echoue (deja configure ?)" -ForegroundColor DarkYellow
} else {
    Write-Host "  OK : CNAME $SUBDOMAIN -> tunnel configure" -ForegroundColor Green
}

# Etape 4 : Verification de la configuration
Write-Host "[4/4] Verification de la configuration..." -ForegroundColor Yellow
if (Test-Path $CONFIG_FILE) {
    Write-Host "  OK : config.yml present" -ForegroundColor Green
} else {
    Write-Host "  ATTENTION : config.yml absent, creation avec valeurs par defaut" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== Configuration terminee ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour demarrer le tunnel :"
Write-Host "  .\cloudflared\start-tunnel.ps1" -ForegroundColor White
Write-Host ""
Write-Host "L'API sera accessible sur : https://$SUBDOMAIN" -ForegroundColor Cyan
