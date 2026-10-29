# TruthGuard Windows Setup Script
# This script sets up the project for Windows development

Write-Host "🛡️  AI TruthGuard - Windows Setup" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -NoNewline
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    $pythonVersion = python --version 2>&1
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "  $pythonVersion"
} else {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "  Python not found. Install from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Setting up virtual environment..." -NoNewline
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " (already exists)" -ForegroundColor Green
}

# Activate virtual environment
$venvActivate = ".\venv\Scripts\Activate.ps1"
& $venvActivate

# Upgrade pip
Write-Host "Upgrading pip..." -NoNewline
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Host " ✓" -ForegroundColor Green

# Install dependencies
Write-Host "Installing dependencies..." -NoNewline
pip install -e ".[dev]" --quiet 2>&1 | Out-Null
Write-Host " ✓" -ForegroundColor Green

# Copy .env.example to .env if it doesn't exist
Write-Host "Configuring environment..." -NoNewline
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "  Created .env (edit as needed)"
} else {
    Write-Host " (already configured)" -ForegroundColor Green
}

Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review .env configuration"
Write-Host "2. Check Ollama: ollama list"
Write-Host "3. Start server: .\start-dev.ps1"
Write-Host "4. Open browser: http://localhost:8000"
Write-Host ""
Write-Host "Run tests: pytest tests/ -v" -ForegroundColor Gray
