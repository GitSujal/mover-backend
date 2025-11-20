# MoveHub Backend - Development Makefile
# Using UV for blazing fast package management

.PHONY: help install dev test lint format clean docker-up docker-down migrate shell

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with UV
	uv pip install -e .

install-dev: ## Install all dependencies including dev tools
	uv pip install -e ".[dev,test]"

dev: ## Run development server with auto-reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run all tests with coverage
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-unit: ## Run only unit tests
	pytest -m unit --cov=app

test-integration: ## Run only integration tests
	pytest -m integration

lint: ## Run all linters
	black --check app/ tests/
	ruff check app/ tests/
	mypy app/

format: ## Format code with Black and Ruff
	black app/ tests/
	ruff --fix app/ tests/

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/
	rm -rf .uv_cache/

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f api

docker-build: ## Build Docker image
	docker-compose build

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	alembic revision --autogenerate -m "$(MSG)"

migrate-up: ## Run all migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

shell: ## Open Python shell with app context
	python -i -c "from app.core.database import *; from app.models import *"

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	make migrate-up

seed: ## Seed database with sample data
	python scripts/seed_data.py

sync: ## Sync dependencies (install from pyproject.toml)
	uv pip install -e ".[dev,test]"

lock: ## Generate requirements.txt from pyproject.toml
	uv pip compile pyproject.toml -o requirements.txt --all-extras

upgrade: ## Upgrade all dependencies
	uv pip compile --upgrade pyproject.toml -o requirements.txt
	uv pip install -r requirements.txt

check: lint test ## Run all checks (lint + test)

ci: check ## Run CI pipeline locally
	@echo "✓ All CI checks passed!"
