# Script to create initial Alembic migration (PowerShell)

Write-Host "Creating initial Alembic migration..." -ForegroundColor Cyan

# Activate virtual environment if it exists
if (Test-Path "venv") {
    & .\venv\Scripts\Activate.ps1
}

# Create initial migration
alembic revision --autogenerate -m "Initial schema: agent runs, tool calls, evidence retrieval, citations, grounding verification, prompt versions, evaluations"

Write-Host "Migration created successfully!" -ForegroundColor Green
Write-Host "Review the migration file in alembic/versions/" -ForegroundColor Yellow
Write-Host "Then run: alembic upgrade head" -ForegroundColor Yellow

