.PHONY: help install install-dev test lint format type-check clean run-api run-worker migrate

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make type-check    - Run type checker"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make run-api       - Run API server"
	@echo "  make run-worker    - Run Celery worker"
	@echo "  make migrate       - Run database migrations"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest --cov=agentic_clinical_assistant --cov-report=term-missing

lint:
	ruff check src tests
	black --check src tests
	isort --check-only src tests

format:
	black src tests
	isort src tests
	ruff check --fix src tests

type-check:
	mypy src

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run-api:
	python scripts/run_api.py

run-worker:
	celery -A agentic_clinical_assistant.workers.celery_app worker --loglevel=info

run-worker-queues:
	celery -A agentic_clinical_assistant.workers.celery_app worker --loglevel=info --queues=default,agent,ingestion,evaluation,benchmark

run-beat:
	celery -A agentic_clinical_assistant.workers.celery_app beat --loglevel=info

migrate:
	alembic upgrade head

migrate-create:
	@echo "Usage: alembic revision --autogenerate -m 'description'"

init-db:
	python scripts/init_db.py

