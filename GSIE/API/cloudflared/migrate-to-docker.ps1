# Migration API : host Windows -> conteneur Docker
# PS1 : arrête le processus uvicorn host, démarre le conteneur api,
# vérifie /health, et relance le tunnel cloudflared si nécessaire.

$ErrorActionPreference = "Stop"

$containerPort = 8000
$compose = "E:\Projets\Quintessences\GSIE\API"

Write-Output "1. Construction/relance du conteneur api..."
Stop-Process -Name "uvicorn" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
docker compose -f "$compose\docker-compose.yml" up -d --wait api

Write-Output "2. Vérification santé conteneur..."
$maxAttempts = 30
$healthy = $false
for ($i = 0; $i -lt $maxAttempts; $i++) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$containerPort/health" -UseBasicParsing -TimeoutSec 5
        if ($r.status -eq "healthy") {
            $healthy = $true
            break
        }
    } catch {
        Write-Output "  essai $i : pas prêt"
    }
    Start-Sleep -Seconds 2
}

if (-not $healthy) {
    Write-Output "ERREUR : conteneur non healthy. Relance uvicorn host."
    docker compose -f "$compose\docker-compose.yml" stop api
    Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn gsie_api.app:app --host 127.0.0.1 --port 8000" -WorkingDirectory $compose -WindowStyle Hidden
    exit 1
}

Write-Output "3. Vérification tunnel..."
try {
    $r = Invoke-RestMethod -Uri "https://api.quintessences-platform.com/health" -UseBasicParsing -TimeoutSec 10
    Write-Output "OK : api.quintessences-platform.com healthy"
} catch {
    Write-Output "WARN : vérifier cloudflared manuellement."
}

Write-Output "Migration terminée."
