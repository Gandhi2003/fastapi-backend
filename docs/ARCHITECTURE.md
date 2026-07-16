# CRM Backend — Enterprise Architecture (2026)

A production-ready FastAPI backend designed for a large multi-module CRM (100+
modules) using **Clean Architecture + Repository Pattern + Service Layer +
Dependency Injection**.

- **Stack:** Python 3.13 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) ·
  PostgreSQL · Alembic · Redis · Celery · Docker · Nginx · GitHub Actions.

---

## 1. Project architecture diagram

```
                          ┌────────────────────────────┐
        HTTPS             │            CLIENTS          │
   ────────────────────► │  Web SPA · Mobile · Partners │
                          └──────────────┬─────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │        NGINX        │  TLS, edge rate-limit,
                              │   (reverse proxy)   │  request-id, gzip
                              └──────────┬──────────┘
                                         │
              ┌──────────────────────────▼──────────────────────────┐
              │                 FastAPI APP (gunicorn+uvicorn)       │
              │                                                      │
              │  Middleware:  SecurityHeaders → Prometheus →         │
              │               RequestContext → Session → CORS        │
              │                                                      │
              │  ┌───────────────── PRESENTATION (API) ───────────┐ │
              │  │  /api/v1 routers  ·  deps (DI)  ·  schemas      │ │
              │  └───────────────────────┬────────────────────────┘ │
              │  ┌───────────────── APPLICATION (Service) ────────┐ │
              │  │  business rules · orchestration · use-cases     │ │
              │  └───────────────────────┬────────────────────────┘ │
              │  ┌───────────────── DOMAIN / DATA (Repo+UoW) ─────┐ │
              │  │  repositories · unit of work · ORM models       │ │
              │  └───────────────────────┬────────────────────────┘ │
              └──────────────┬────────────┬──────────────┬──────────┘
                             │            │              │
                     ┌───────▼──┐   ┌─────▼─────┐   ┌────▼─────┐
                     │PostgreSQL│   │   Redis    │   │  Celery  │
                     │ (asyncpg)│   │ sessions / │   │ workers  │
                     │          │   │ cache /    │   │ + beat   │
                     │          │   │ denylist / │   │          │
                     │          │   │ ratelimit  │   │          │
                     └──────────┘   └────────────┘   └────┬─────┘
                                                          │
                              Observability: Prometheus → Grafana, Sentry,
                              structlog JSON → Loki/ELK
```

**Clean Architecture dependency rule:** dependencies point *inward only*.
Routers know services; services know repositories; repositories know the ORM.
Nothing inner imports anything outer — the service layer has zero FastAPI
imports, so business logic is reusable from Celery workers, CLI scripts and
tests without HTTP.

```
  Presentation  ──►  Application  ──►  Domain/Data  ──►  Infrastructure
  (routers,deps)     (services)       (repos, UoW)      (Postgres, Redis)
        │                                                      ▲
        └──────────────── depends on abstractions ────────────┘
```

---

## 2. Complete folder structure

```
fastapi-backend/
├── app/
│   ├── main.py                     # App factory, middleware order, lifespan, router mount
│   │
│   ├── core/                       # Cross-cutting infrastructure (no business logic)
│   │   ├── config.py               #   Typed settings (Pydantic), single source of truth
│   │   ├── security.py             #   Argon2 hashing + JWT encode/decode primitives
│   │   ├── redis.py                #   Shared async Redis client (pool)
│   │   ├── logging.py              #   structlog config + request-id contextvar
│   │   ├── rate_limit.py           #   Redis fixed-window limiter dependency
│   │   ├── exceptions.py           #   Domain exception hierarchy (AppException)
│   │   └── exception_handlers.py   #   Global handlers → standard error envelope
│   │
│   ├── db/                         # Persistence infrastructure
│   │   ├── base.py                 #   DeclarativeBase + constraint naming convention
│   │   ├── mixins.py               #   UUID PK, timestamps, soft-delete mixins
│   │   ├── session.py              #   Async engine + sessionmaker + get_session dep
│   │   ├── unit_of_work.py         #   Transaction boundary (UoW)
│   │   ├── models_registry.py      #   Imports every model (for Alembic autogenerate)
│   │   ├── repositories/
│   │   │   └── base.py             #   Generic CRUD repository (pagination/filter/sort)
│   │   └── migrations/             #   Alembic env + versioned migrations
│   │
│   ├── common/                     # Shared, reusable building blocks
│   │   ├── schemas/
│   │   │   ├── response.py         #   Standard ResponseEnvelope + Meta + ErrorDetail
│   │   │   └── pagination.py       #   PageParams / Page
│   │   ├── enums/                  #   Cross-module StrEnums (statuses, channels)
│   │   ├── utils/                  #   Pure helpers (dates, slugs, sanitization)
│   │   └── exceptions/             #   (optional) module-specific error subclasses
│   │
│   ├── middleware/                 # ASGI middleware
│   │   ├── request_context.py      #   X-Request-ID, access log, timing
│   │   └── security_headers.py     #   Security headers + body-size guard
│   │
│   ├── api/                        # Presentation layer
│   │   ├── deps/                   #   Dependency-injection providers
│   │   │   ├── database.py         #     request-scoped session
│   │   │   └── auth.py             #     current_user, require_permissions, service factories
│   │   └── v1/
│   │       └── router/__init__.py  #   Aggregates all module routers under /api/v1
│   │
│   ├── modules/                    # ★ Business modules — one vertical slice each
│   │   ├── auth/                   #   models, schemas, service, token_service, mfa_service, router
│   │   ├── users/                  #   user entity + repository + (service/router)
│   │   ├── roles/                  #   RBAC roles + role↔permission join
│   │   ├── permissions/            #   permission atoms
│   │   ├── customers/              #   ★ reference CRUD module (template to copy)
│   │   ├── leads/  products/  orders/  kyc/
│   │   ├── notifications/  reports/  audit_logs/  file_uploads/
│   │   └── health/                 #   liveness / readiness probes
│   │
│   ├── workers/                    # Background processing
│   │   ├── celery_app.py           #   Celery config + beat schedule
│   │   └── tasks/                  #   email, audit, reports, ...
│   │
│   ├── integrations/               # Third-party adapters (anti-corruption layer)
│   │   ├── oauth/providers.py      #   Google / Microsoft OIDC clients
│   │   ├── email/                  #   SMTP / provider adapter
│   │   └── storage/                #   S3-compatible object storage adapter
│   │
│   └── monitoring/
│       └── metrics.py              #   Prometheus middleware + /metrics endpoint
│
├── tests/                          # unit / integration / api / factories
├── deploy/                         # Dockerfile, nginx.conf, prometheus.yml
├── docker-compose.yml              # Local/staging full stack
├── alembic.ini
├── pyproject.toml                  # Deps + Ruff + Black + Mypy + Pytest config
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml        # Quality gate → tests → docker build/push
└── .env.example
```

### Why **module-first** (vertical slices) instead of layer-first

At 100+ modules, a layer-first tree (`/models`, `/schemas`, `/services`, …)
forces you to open five distant folders to touch one feature, and those folders
grow to hundreds of files. A **module-first** tree co-locates everything about a
feature in one folder (`modules/customers/{models,schemas,repository,service,
router}.py`). Adding a module is "copy `customers/`, rename, mount the router."
Teams own folders; merge conflicts shrink; navigation is local.

---

## 3. Purpose of each folder (summary)

| Folder | Layer | Responsibility |
|---|---|---|
| `core/` | Infrastructure | Config, security primitives, logging, Redis, errors — no business logic |
| `db/` | Infrastructure | Engine/session, base repository, UoW, mixins, migrations |
| `common/` | Shared kernel | Response envelope, pagination, enums, pure utils |
| `middleware/` | Presentation edge | Request id, security headers, body limits |
| `api/deps/` | Presentation (DI) | Composition root: wires sessions, services, auth into routes |
| `api/v1/router/` | Presentation | Versioned mount point for all module routers |
| `modules/<x>/` | Vertical slice | One business capability end-to-end |
| `workers/` | Application (async) | Celery tasks + schedule, off the request path |
| `integrations/` | Infrastructure | Adapters isolating 3rd-party APIs from the domain |
| `monitoring/` | Observability | Prometheus metrics |
| `tests/` | — | unit / integration / api suites |
| `deploy/` | DevOps | Container, proxy, metrics scrape config |

---

## 4. Authentication flow

### 4.1 Login (with optional MFA)

```
Client                 API (router)        AuthService            Repo / Redis / DB
  │  POST /auth/login      │                    │                        │
  ├───────────────────────►│  authenticate()    │                        │
  │                        ├───────────────────►│  get_by_email()        │
  │                        │                    ├───────────────────────►│  (User + roles)
  │                        │                    │  verify Argon2 hash     │
  │                        │                    │  lockout check          │
  │                        │                    │  email-verified check   │
  │                        │                    │  if mfa_enabled: TOTP   │
  │                        │                    │  issue_pair()           │
  │                        │                    ├──── store RefreshToken ►│  (jti, family_id)
  │  200 {access,refresh}  │◄───────────────────┤                        │
  │◄───────────────────────┤                    │                        │
```

- **Access token (15 min, JWT)** carries `sub`, `jti`, `type=access`, and a
  `perms` claim (flattened permission codes) for fast authorization.
- **Refresh token (30 days, JWT)** carries a `family` claim; a row in
  `refresh_tokens` tracks `jti`, `family_id`, `rotated`, `revoked`.
- **Account lockout:** N failed attempts within a window sets `locked_until`.
- **Timing-safe enumeration defence:** unknown emails still run a dummy Argon2
  verify so response time doesn't reveal account existence.

### 4.2 Refresh-token rotation with reuse detection (OWASP)

```
  POST /auth/refresh (refresh_token)
        │
        ▼
  decode + verify type=refresh
        │
        ▼
  lookup refresh_tokens by jti ──► not found / revoked ──► 401
        │
   already rotated? ──► YES ──► TOKEN THEFT: revoke entire family ──► 401
        │ NO
        ▼
  mark old token rotated → issue NEW access+refresh (same family_id) → 200
```

This is the gold-standard pattern: a stolen refresh token can be used at most
once before the legitimate client's next refresh trips reuse detection and burns
every session in the family.

### 4.3 Revocation / logout

- **Logout:** the access token's `jti` is added to a **Redis denylist** with TTL
  = remaining token lifetime. `get_current_user` checks the denylist on every
  request, so a short-lived access token is killable instantly.
- **Revoke all sessions / device:** flips `revoked` on `refresh_tokens` rows.

### 4.4 Social login (Google / Microsoft)

`Authlib` performs the OIDC dance (state/nonce stored in the signed session
cookie). On callback we read verified userinfo and either link to an existing
`User` or provision one with `auth_provider = google|microsoft`. Local password
auth remains fully independent.

### 4.5 Authorization (RBAC + permissions)

```
User ──< user_roles >── Role ──< role_permissions >── Permission ("customers:create")
```

Routes declare `require_permissions("customers:create")`. The dependency loads
the principal (with roles eager-loaded), flattens permission codes, and rejects
with `403` if any are missing. Superusers bypass via the `*` wildcard. Policy
changes are **data changes** (assign/revoke), never redeploys.

---

## 5. Request lifecycle

```
1.  NGINX           TLS terminate, edge rate-limit, add/propagate X-Request-ID
2.  SecurityHeaders middleware  enforce body-size cap, set hardening headers
3.  Prometheus middleware       start timer, count request
4.  RequestContext middleware   bind request_id into structlog contextvar
5.  Session + CORS middleware   OAuth state cookie, CORS preflight
6.  Routing                     match /api/v1/... to a path operation
7.  Dependency resolution       db_session, get_current_user, require_permissions,
                                service factories — resolved & cached per request
8.  Pydantic validation         request body/query/path → typed DTO (422 on fail)
9.  Handler (router)            thin: call service method
10. Service                     business rules; uses repositories
11. Repository                  builds SQL via SQLAlchemy; flush (no commit)
12. UoW / session               commit on success, rollback on exception
13. Response model              ORM → read schema → ResponseEnvelope
14. Exception handlers          any AppException/validation/integrity → envelope
15. Middleware unwinds          metrics observed, access line logged, headers set
16. NGINX                       gzip, return to client
```

Every error path converges on the **standard envelope** so clients parse one
shape. Every log line within the request carries the same `request_id`.

---

## 6. Dependency injection flow

FastAPI's `Depends` graph is the **composition root** — objects are assembled
per request and are individually overridable in tests.

```
require_permissions("customers:read")
        └─ get_current_user
             ├─ HTTPBearer (extract token)
             ├─ get_user_repository ──► db_session ──► AsyncSessionLocal
             └─ get_token_service   ──► db_session
                                    └─► get_redis (shared pool)

get_service (CustomerService)
        ├─ CustomerRepository ──► db_session
        └─ db_session
```

- **Why DI here, not globals:** swapping the DB session or Redis for a fake in a
  test is one `app.dependency_overrides[...] = ...` line — no monkeypatching of
  imports, no hidden singletons.
- **Service factories** (`get_auth_service`, `get_service`) keep routers free of
  construction logic (SRP) and make the wiring explicit and discoverable.

---

## 7. Database flow

```
Service.method()
   │
   ├─ Repository.create/update/list()        # builds SQLAlchemy Core/ORM stmt
   │       └─ session.execute(stmt)           # asyncpg sends to PostgreSQL
   │       └─ session.flush()                 # emit SQL, populate PK/defaults
   │                                          #   (NO commit here)
   ├─ ... possibly several repositories ...
   │
   └─ UnitOfWork.__aexit__ / session.commit() # ONE atomic transaction
            success → COMMIT      exception → ROLLBACK
```

Key decisions:

- **Async end-to-end** (`asyncpg`) — high concurrency on I/O-bound CRM
  workloads without thread-pool overhead.
- **Repository owns queries, UoW owns the transaction.** Repositories only
  `flush`; the UoW (or request-scoped session) decides commit/rollback, so a
  multi-repository use-case is atomic.
- **UUIDv4 PKs** (server default `gen_random_uuid()`): no enumeration attacks,
  safe in URLs, mergeable across shards/regions.
- **Soft delete** (`deleted_at`): the base repository auto-filters deleted rows;
  history is preserved for audit/undo/analytics.
- **Automatic timestamps** via DB `server_default`/`onupdate` — correct even for
  writes that bypass the ORM.
- **Pagination/filter/sort** are generic on the base repository — uniform
  `?page=&page_size=&sort=&order=` on every list endpoint.
- **Indexes** on FKs, `email`, `status`, `created_at`, `deleted_at`; Alembic
  naming convention keeps migration diffs deterministic.

---

## 8. Starter code

All starter code is in the repository (see the tree in §2). The highest-signal
files to read first:

| Concern | File |
|---|---|
| App wiring | `app/main.py` |
| Settings | `app/core/config.py` |
| Crypto | `app/core/security.py` |
| Errors | `app/core/exceptions.py`, `app/core/exception_handlers.py` |
| Generic repo | `app/db/repositories/base.py` |
| UoW | `app/db/unit_of_work.py` |
| Mixins | `app/db/mixins.py` |
| AuthN/Z deps | `app/api/deps/auth.py` |
| Token rotation | `app/modules/auth/token_service.py` |
| Auth use-cases | `app/modules/auth/service.py` |
| **Module template** | `app/modules/customers/*` |
| Celery | `app/workers/celery_app.py` |

---

## 9. Why each decision is production-ready

| Decision | Production rationale |
|---|---|
| **Clean Architecture + Service Layer** | Business logic is framework-free → testable, reusable from workers/CLI, survives a framework swap. |
| **Repository + UoW** | Single place for persistence; atomic multi-entity use-cases; trivial to mock. |
| **Generic base repository** | DRY across 100+ entities; one audited implementation of pagination/soft-delete. |
| **Pydantic v2 settings** | Misconfig fails fast at boot, not mid-request; 12-factor; typed. |
| **Argon2id** | OWASP-recommended, memory-hard; resists GPU cracking. (passlib is unmaintained.) |
| **RS256 JWT + jti + denylist** | Asymmetric verify without sharing signing keys; instant revocation despite stateless tokens. |
| **Refresh rotation + reuse detection** | Limits blast radius of a stolen refresh token to a single use. |
| **RBAC + permission strings** | Authorization is data, not code; least privilege; auditable. |
| **Standard response envelope** | One client-side parser; consistent errors across all modules. |
| **Global exception handlers** | No stack traces/SQL leak to clients; consistent HTTP mapping. |
| **Request-id + structlog JSON** | End-to-end tracing across app, Sentry, downstream services. |
| **Async SQLAlchemy + asyncpg** | Scales I/O-bound CRM traffic; `pool_pre_ping`/`recycle` survive proxy drops. |
| **Celery + beat** | Slow/unreliable work (email, reports, KYC) off the request path; retries with backoff. |
| **Redis** | One system for sessions, cache, rate-limit, denylist — fewer moving parts. |
| **Multi-stage Docker, non-root, healthcheck** | Small attack surface; safe rollouts; orchestrator-friendly. |
| **Nginx edge** | TLS, edge rate-limit, header hardening; hides internal `/metrics`. |
| **Prometheus + Grafana + Sentry** | RED metrics + error tracking = real SLOs and fast incident response. |
| **CI quality gate** | Ruff + Black + Mypy + tests on real PG/Redis block regressions before merge. |
| **Alembic + naming convention** | Reversible, deterministic, reviewable schema changes. |

---

## 10. 2026 enterprise best practices applied

1. **Python 3.13 + full async** end-to-end (ASGI, asyncpg, redis.asyncio).
2. **Pydantic v2** for both validation and settings (Rust core, fast).
3. **Ruff** as the single fast linter/import-sorter; **Black** formatting;
   **Mypy strict** typing; **pre-commit** mirrors CI locally.
4. **Module-first vertical slices** for team-scale ownership of 100+ modules.
5. **API versioning** baked into routing (`/api/v1`, parallel `/api/v2`).
6. **OpenAPI/Swagger/ReDoc** auto-generated from typed routes.
7. **Security by default:** Argon2id, RS256, MFA (TOTP), rotation+reuse
   detection, lockout, denylist, rate limiting, CSRF-safe OAuth session,
   security headers, body-size limits, input sanitization, parameterized
   queries (no raw SQL string-building → SQLi-safe).
8. **Observability-first:** structured JSON logs, request-id correlation,
   Prometheus metrics, Sentry, OTel-ready.
9. **12-factor config & secrets** via env + mounted secret files (JWT keys),
   never committed.
10. **Reproducible builds & GitOps-ready CI/CD:** multi-stage images,
    GHCR push, deployable to Kubernetes (liveness/readiness probes present).

---

## Quickstart

```bash
cp .env.example .env

# Generate RS256 keypair for JWT (or set JWT_ALGORITHM=HS256 for local)
mkdir -p keys
openssl genpkey -algorithm RSA -out keys/private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in keys/private.pem -out keys/public.pem

docker compose up --build              # full stack
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic revision --autogenerate -m "create tables"

# Local dev (without Docker)
uv pip install -r pyproject.toml --extra dev
pre-commit install
uvicorn app.main:app --reload          # http://localhost:8000/docs
pytest
```
