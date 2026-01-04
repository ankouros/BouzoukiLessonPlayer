# Bouzouki Lesson Player installation script for PowerShell (Windows)
# - Creates/uses a local .venv
# - Installs Python dependencies from requirements.txt

param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[install] Using Python: $Python"

# Create virtual environment if it doesn't exist
if (-Not (Test-Path .venv)) {
    Write-Host "[install] Creating virtual environment in .venv..."
    & $Python -m venv .venv
} else {
    Write-Host "[install] Reusing existing .venv virtual environment."
}

# Activate virtual environment
$venvActivate = Join-Path .venv "Scripts\Activate.ps1"
. $venvActivate

Write-Host "[install] Upgrading pip..."
python -m pip install --upgrade pip

if (Test-Path requirements.txt) {
    Write-Host "[install] Installing Python dependencies from requirements.txt..."
    python -m pip install -r requirements.txt
} else {
    Write-Warning "[install] requirements.txt not found; skipping Python dependency installation."
}

Write-Host "[install] Installation complete. To run the app in this shell:" -ForegroundColor Green
Write-Host "  python main.py" -ForegroundColor Green

