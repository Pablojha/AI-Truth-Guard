# TruthGuard Development Server Starter
# Run this script to start the FastAPI backend in development mode

param(
    [switch]$Demo = $false
)

Write-Host "🛡️  AI TruthGuard - Development Server" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment not found. Run: python -m venv venv" -ForegroundColor Red
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
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Frontend:  http://localhost:8000" -ForegroundColor Green
Write-Host "API:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health:    http://localhost:8000/healthz" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
