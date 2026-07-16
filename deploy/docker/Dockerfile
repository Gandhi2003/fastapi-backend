# Multi-stage build: a fat builder, a slim non-root runtime.
# Why multi-stage: build tools (compilers, headers) never reach the final image,
# shrinking attack surface and image size.

# --------------------------------------------------------------------------- #
# Stage 1 — builder
# --------------------------------------------------------------------------- #
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# uv for fast, reproducible installs (drop-in; swap for pip if preferred).
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
# Resolve deps into a venv we can copy wholesale to the runtime stage.
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r pyproject.toml

# --------------------------------------------------------------------------- #
# Stage 2 — runtime
# --------------------------------------------------------------------------- #
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# libpq for psycopg; curl for the container healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Run as an unprivileged user (never root in production containers).
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home app

COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app:app . .

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health/live || exit 1

# Gunicorn manages uvicorn workers. Tune workers to (2 × CPU) + 1.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--timeout", "60", "--graceful-timeout", "30"]
