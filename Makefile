.PHONY: install dev lint lint-fix type-check  migrate \
        env-local env-stage env-prod docker-build docker-up docker-down clean

DOCKERFILE := deploy/docker/Dockerfile
IMAGE      := wealthified-api


install:
	uv venv
	uv pip install -r requirements.txt
	uv pip install mypy pre-commit
	.venv/bin/pre-commit install
	@echo "✓ ready — hooks active, commit will auto-format"

dev:
	uv run uvicorn app.main:app --reload --port 8001 --reload-dir app

lint:
	uv run ruff check app/ && uv run ruff format --check app/

lint-fix:
	uv run ruff check --fix app/ && uv run ruff format app/

type-check:
	uv run mypy app/

migrate:
	uv run alembic upgrade head

env-local:
	@echo "Using existing .env (local)"

env-stage:
	cp .env.stage .env && echo "✓ .env now = staging"

env-prod:
	cp .env.prod .env && echo "✓ .env now = production"

docker-build:
	docker build -f $(DOCKERFILE) -t $(IMAGE) .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__
