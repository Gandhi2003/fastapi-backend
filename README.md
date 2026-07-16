# CRM Backend

Production-ready, enterprise-grade **FastAPI** backend for a large multi-module
CRM — built with Clean Architecture, the Repository Pattern, a Service Layer and
Dependency Injection.

**Stack:** Python 3.13 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) ·
PostgreSQL · Alembic · Redis · Celery · Docker · Nginx · GitHub Actions.

> 📐 Full design — folder purposes, auth flow, request lifecycle, DI flow,
> database flow, architecture diagram and design rationale — lives in
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Features

- **Auth & security:** JWT (RS256), refresh-token rotation with reuse detection,
  Argon2id hashing, RBAC + permission-based authorization, OAuth2 (Google /
  Microsoft), TOTP MFA, email verification, forgot-password, account lockout,
  device/session management, token revocation (Redis denylist), rate limiting,
  CORS, security headers, input sanitization, audit logging.
- **Data:** async SQLAlchemy, generic CRUD repository, Unit of Work, soft
  delete, UUID PKs, automatic timestamps, pagination/filter/sort, indexes.
- **API:** versioned (`/api/v1`), OpenAPI/Swagger/ReDoc, standard response
  envelope, global exception handling, request-id middleware.
- **Ops:** Docker (multi-stage, non-root), Compose, Nginx, GitHub Actions CI/CD,
  Prometheus + Grafana, Sentry, structured JSON logging, health probes.

## Quickstart

```bash
cp .env.example .env

mkdir -p keys
openssl genpkey -algorithm RSA -out keys/private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in keys/private.pem -out keys/public.pem

docker compose up --build
docker compose run --rm api alembic upgrade head
```

API docs: <http://localhost:8000/docs> · Metrics: Grafana on `:3001`,
Prometheus on `:9090` · Mail UI (Mailpit): `:8025`.

## Adding a new module

Copy `app/modules/customers/` → rename, adjust the model/schemas, then mount its
router in `app/api/v1/router/__init__.py` and add the model to
`app/db/models_registry.py`. That's the entire pattern, repeated for all 100+
modules.

## Development

```bash
uv pip install -r pyproject.toml --extra dev
pre-commit install
uvicorn app.main:app --reload
ruff check app tests && black --check app tests && mypy app && pytest
```
