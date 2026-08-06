# Déploiement de la landing page Quintessences sur Cloudflare Pages
# Usage : .\deploy-landing.ps1

$ErrorActionPreference = "Stop"

$ProjectName = "quintessences-landing"
$BuildDir = "E:\Projets\Quintessences\landing-quintessences\public"
$WranglerCmd = "npx"

Write-Host "=== Deploiement landing page Quintessences ===" -ForegroundColor Cyan
Write-Host "Projet : $ProjectName"
Write-Host "Source : $BuildDir"
Write-Host ""

# Verifier que le dossier public existe
if (-not (Test-Path $BuildDir)) {
    Write-Host "ERREUR : dossier $BuildDir introuvable" -ForegroundColor Red
    exit 1
}

# Verifier wrangler
$wrangler = Get-Command wrangler -ErrorAction SilentlyContinue
if (-not $wrangler) {
    Write-Host "Installation de wrangler..." -ForegroundColor Yellow
    npm install -g wrangler
}

# Authentification si necessaire
$whoami = & $WranglerCmd wrangler whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Authentification Cloudflare necessaire." -ForegroundColor Yellow
    & $WranglerCmd wrangler login
}

# Creer le projet si necessaire
$projectExists = & $WranglerCmd wrangler pages project list 2>&1 | Select-String $ProjectName
if (-not $projectExists) {
    Write-Host "Creation du projet Cloudflare Pages..." -ForegroundColor Yellow
    & $WranglerCmd wrangler pages project create $ProjectName
} else {
    Write-Host "Projet $ProjectName existant." -ForegroundColor Green
}

# Deployer
Write-Host "Deploiement..." -ForegroundColor Yellow
& $WranglerCmd wrangler pages deploy $BuildDir --project-name=$ProjectName

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR : le deploiement a echoue" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Landing page deployee avec succes." -ForegroundColor Green
Write-Host "Prochaines etapes :" -ForegroundColor Cyan
Write-Host "  1. Dans le dashboard Cloudflare Pages, lier le domaine :"
Write-Host "     quintessences-platform.com"
Write-Host "  2. Creer l'enregistrement CNAME 'www' vers le projet Pages."
Write-Host "  3. Verifier : https://quintessences-platform.com"
