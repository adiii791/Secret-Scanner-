# Dockerfile — Secret Scanner
# Produces a minimal, production-ready image for AWS ECS / ECR / App Runner.
#
# Build:  docker build -t secret-scanner .
# Run:    docker run -p 5000:5000 --env-file .env secret-scanner

# ---------------------------------------------------------------------------
# Stage 1: dependency builder (keeps the final image lean)
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for psycopg (PostgreSQL C driver).
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install libpq runtime library (required by psycopg binary wheel at runtime).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage.
COPY --from=builder /install /usr/local

# Non-root user — never run as root in production.
RUN useradd --system --create-home appuser
WORKDIR /app
USER appuser

# Copy application source.
COPY --chown=appuser:appuser backend/   ./backend/
COPY --chown=appuser:appuser frontend/  ./frontend/
COPY --chown=appuser:appuser wsgi.py    .
COPY --chown=appuser:appuser gunicorn.conf.py .

# Expose the port gunicorn listens on (overridable via PORT env var).
EXPOSE 5000

# Health-check: Docker / ECS will mark the container unhealthy if /api/health
# returns anything other than HTTP 200.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

# Default command: gunicorn reads its config from gunicorn.conf.py.
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
