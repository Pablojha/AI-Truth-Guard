# TruthGuard Development Server Starter
# Run this script to start the FastAPI backend in development mode

param(
    [switch]$Demo = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host "Usage: .\start-dev.ps1 [-Demo]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Demo    Use demo mode (sample data, no Ollama required)"
    Write-Host "  -Help    Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\start-dev.ps1 -Demo              # Demo mode"
    Write-Host "  .\start-dev.ps1                    # Local mode (needs Ollama)"
    exit 0
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🛡️  AI TruthGuard - Development Server" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " OK ($pythonVersion)" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "Python not found. Install from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -NoNewline
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "Virtual environment not found. Run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: pip install -e '.[dev]'" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
if ($Demo) {
    Write-Host "📋 Starting in DEMO mode (fixture provider, sample data)" -ForegroundColor Yellow
    $env:PROVIDER_MODE = "fixture"
} else {
    Write-Host "⚙️  Starting in LOCAL mode (requires Ollama running)" -ForegroundColor Yellow
    $env:PROVIDER_MODE = "local"

    # Check Ollama connectivity
    Write-Host ""
    Write-Host "Checking Ollama... " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
        $models = ($response.Content | ConvertFrom-Json).models
        if ($models) {
            Write-Host "✓ Ollama is running" -ForegroundColor Green
            $modelNames = $models | ForEach-Object { $_.name }
            Write-Host "  Available models: $modelNames"

            if ($models | Where-Object { $_.name -like "*deepseek-r1*" }) {
                Write-Host "  ✓ deepseek-r1 found" -ForegroundColor Green
            } else {
                Write-Host "  ✗ deepseek-r1 not found. Run: ollama pull deepseek-r1:14b" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "✗ Ollama not reachable at http://localhost:11434" -ForegroundColor Yellow
        Write-Host "  Make sure Ollama is running: ollama serve" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Server..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "FRONTEND:    http://localhost:8000" -ForegroundColor Green
Write-Host "API DOCS:    http://localhost:8000/docs" -ForegroundColor Green
Write-Host "HEALTH:      http://localhost:8000/healthz" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
