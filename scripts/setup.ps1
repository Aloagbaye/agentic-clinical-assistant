# Setup script for agentic-clinical-assistant (PowerShell)

Write-Host "🚀 Setting up agentic-clinical-assistant..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python version: $pythonVersion" -ForegroundColor Green

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Install pre-commit hooks
Write-Host "🪝 Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

# Create .env from example if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env file with your configuration" -ForegroundColor Yellow
}

# Create data directory
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path data/faiss_index | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your configuration"
Write-Host "2. Set up PostgreSQL and Redis"
Write-Host "3. Run database migrations: alembic upgrade head"
Write-Host "4. Start the API: make run-api (or uvicorn agentic_clinical_assistant.api.main:app --reload)"
Write-Host "5. Start the worker: make run-worker (or celery -A agentic_clinical_assistant.workers.celery_app worker)"

