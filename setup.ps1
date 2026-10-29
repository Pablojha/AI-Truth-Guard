# TruthGuard Windows Setup Script
# This script sets up the project for Windows development

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "AI TruthGuard - Windows Setup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -NoNewline
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    $pythonVersion = python --version 2>&1
    Write-Host " OK" -ForegroundColor Green
    Write-Host "  Version: $pythonVersion"
} else {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "  Python not found. Install from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -NoNewline
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " (already exists)" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -NoNewline
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " ERROR" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -NoNewline
python -m pip install --upgrade pip 2>&1 | Out-Null
Write-Host " OK" -ForegroundColor Green

# Install dependencies
Write-Host "Installing dependencies..." -NoNewline
pip install -e ".[dev]" 2>&1 | Out-Null
Write-Host " OK" -ForegroundColor Green

# Copy .env.example to .env if it doesn't exist
Write-Host "Configuring environment..." -NoNewline
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host " OK" -ForegroundColor Green
    Write-Host "  Created .env (edit as needed)"
} else {
    Write-Host " (already configured)" -ForegroundColor Green
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start the server:"
Write-Host "     .\start-dev.ps1 -Demo"
Write-Host ""
Write-Host "  2. Open your browser:"
Write-Host "     http://localhost:8000"
Write-Host ""
