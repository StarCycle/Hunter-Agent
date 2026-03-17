$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Repo root: $repoRoot"

Write-Host "[1/4] Checking Python build prerequisites"
python -c "import setuptools" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "setuptools is required before running setup.ps1. Install it in the active Python environment first."
}

Write-Host "[2/4] Installing package in editable mode"
python -m pip install -e $repoRoot --no-build-isolation

Write-Host "[3/4] Ensuring data directories exist"
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot "exports") | Out-Null

Write-Host "[4/4] Running CLI smoke check"
python -m hunter_agent.cli --help | Out-Null

Write-Host "Setup completed."
