<#
.SYNOPSIS
    Master test local — exécute toutes les portes qualité avant un commit.

.DESCRIPTION
    Lance successivement :
    1. Ruff check + format check
    2. mypy
    3. tests unitaires avec couverture 100 %
    4. (optionnel) harnais de mutation

    Le script s'arrête au premier échec (fail fast).

.EXAMPLE
    .\scripts\run-master-tests.ps1
    .\scripts\run-master-tests.ps1 -Mutation
#>
[CmdletBinding()]
param(
    [switch] $Mutation
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Environnement virtuel introuvable : $VenvPython"
}

function Invoke-Step {
    param([string]$Title, [string]$Command)
    Write-Host "`n[MASTER TEST] $Title" -ForegroundColor Cyan
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Échec : $Title"
    }
}

Invoke-Step "Ruff check" "$VenvPython -m ruff check src tests"
Invoke-Step "Ruff format check" "$VenvPython -m ruff format --check src tests"
Invoke-Step "Mypy type check" "$VenvPython -m mypy src/gsie_api"
Invoke-Step "Unit tests with 100% coverage" `
    "$VenvPython -m pytest tests/unit -q -n 0 --cov=src/gsie_api --cov-report=term-missing"

if ($Mutation) {
    Invoke-Step "Mutation harness" "$VenvPython tests/mutation/harnais.py"
}

Write-Host "`n[MASTER TEST] Toutes les portes qualité sont vertes." -ForegroundColor Green
