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
    Write-Host "  -Demo    Use demo mode (sample data, no Ollama required)" -ForegroundColor Cyan
    Write-Host "  -Help    Show this help message" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\start-dev.ps1 -Demo              # Demo mode (recommended)" -ForegroundColor Green
    Write-Host "  .\start-dev.ps1                    # Local mode (requires Ollama)" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "AI TruthGuard - Development Server" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
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
    Write-Host "Virtual environment not found. Run: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Verify dependencies are installed
Write-Host "Checking dependencies..." -NoNewline
try {
    python -c "import fastapi; import uvicorn" 2>&1 | Out-Null
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "Dependencies not installed. Run: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Set environment variables based on mode
Write-Host ""
if ($Demo) {
    Write-Host "Starting in DEMO mode (sample data, no Ollama required)" -ForegroundColor Yellow
    $env:PROVIDER_MODE = "fixture"
} else {
    Write-Host "Starting in LOCAL mode (requires Ollama running)" -ForegroundColor Yellow
    $env:PROVIDER_MODE = "local"

    # Check Ollama connectivity
    Write-Host "Checking Ollama..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
        $models = ($response.Content | ConvertFrom-Json).models
        if ($models -and $models.Count -gt 0) {
            Write-Host " OK" -ForegroundColor Green
            $modelNames = $models | ForEach-Object { $_.name }
            Write-Host "  Available models: $($modelNames -join ', ')"
            if ($models | Where-Object { $_.name -like "*deepseek-r1*" }) {
                Write-Host "  deepseek-r1 found" -ForegroundColor Green
            } else {
                Write-Host "  Warning: deepseek-r1 not found" -ForegroundColor Yellow
                Write-Host "  Run: ollama pull deepseek-r1:14b" -ForegroundColor Yellow
            }
        } else {
            Write-Host " WARNING" -ForegroundColor Yellow
            Write-Host "  Ollama is running but has no models" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host "  Ollama not reachable at http://localhost:11434" -ForegroundColor Yellow
        Write-Host "  Start Ollama with: ollama serve" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Server..." -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "FRONTEND:    http://localhost:8000" -ForegroundColor Green
Write-Host "API DOCS:    http://localhost:8000/docs" -ForegroundColor Green
Write-Host "HEALTH:      http://localhost:8000/healthz" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
