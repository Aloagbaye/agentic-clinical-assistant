#!/bin/bash
# Script to create initial Alembic migration

set -e

echo "Creating initial Alembic migration..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create initial migration
alembic revision --autogenerate -m "Initial schema: agent runs, tool calls, evidence retrieval, citations, grounding verification, prompt versions, evaluations"

echo "Migration created successfully!"
echo "Review the migration file in alembic/versions/"
echo "Then run: alembic upgrade head"

