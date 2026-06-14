# ─── Rudraksh AI Backend ───
# Multi-stage build for minimal image size
# Optimised for CPU-only inference on 16 GB RAM machines

# ── Stage 1: Builder ──
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.12-slim AS runtime

LABEL maintainer="abhi8523@gmail.com"
LABEL description="Rudraksh AI — locally-hosted AI intelligence suite"

# Create non-root user
RUN groupadd -r rudraksh && useradd -r -g rudraksh -m rudraksh

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/data/uploads /app/data/db && \
    chown -R rudraksh:rudraksh /app

USER rudraksh

# Expose FastAPI port
EXPOSE 8000

# Health-check against the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

# Run with uvicorn — 2 workers is sensible for 16 GB / no-GPU
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--http", "httptools"]
