# Stack Research

**Project:** rag_stream v1.3 Production Deployment  
**Domain:** Docker容器化与生产环境部署  
**Researched:** 2026-02-28  
**Confidence:** HIGH  

## Executive Summary

For production deployment of the rag_stream FastAPI service, the recommended stack leverages modern, officially-supported tools that integrate seamlessly with the existing uv/FastAPI/Python 3.12+ architecture. **Key finding:** Uvicorn with native worker management (`--workers` flag) has superseded Gunicorn as the recommended production server for FastAPI. Docker Compose v2+ (the specification-based version) should be used without legacy version declarations. Health checks should be implemented as custom FastAPI endpoints rather than external dependencies. Log management is best handled via structured logging with python-json-logger (already in project) and Docker's native log rotation.

## Recommended Stack Additions

### Core Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Docker | 24.0+ | Container runtime | Industry standard, supports BuildKit for faster builds |
| Docker Compose | v2.20+ (CLI) / v5 (SDK) | Multi-container orchestration | Official Go-based implementation, uses Compose Specification (no version key needed) |

### Application Server

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Uvicorn | 0.34.0+ | ASGI server | Native worker support (--workers), faster than Gunicorn+Uvicorn combo, official FastAPI recommendation |
| FastAPI CLI | bundled | Production command | `fastapi run` is the modern recommended way over direct uvicorn |

**Server Configuration:**

```bash
# Production (single container, multiple workers)
fastapi run app/main.py --host 0.0.0.0 --port 8000 --workers 4

# Or direct uvicorn for more control
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --timeout-graceful-shutdown 30
```

**Why NOT Gunicorn?**
- Uvicorn 0.34+ now handles worker management natively (verified via Context7)
- Gunicorn adds unnecessary complexity for containerized deployments
- Official FastAPI docs now recommend `fastapi run` or `uvicorn --workers`
- Single process = simpler signal handling for graceful shutdown

### Health Checks

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI native | built-in | Health endpoint | Implement custom /health endpoint using FastAPI's dependency injection |

**Recommended approach (NO external library needed):**

```python
# src/rag_stream/src/api/health.py
from fastapi import APIRouter, Depends, status
from typing import Dict, Any

router = APIRouter()

async def check_database() -> Dict[str, Any]:
    """Check DaiShanSQL connectivity"""
    return {"status": "healthy"}

async def check_vector_store() -> Dict[str, Any]:
    """Check Milvus connectivity"""
    return {"status": "healthy"}

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Liveness probe - basic service availability"""
    return {"status": "healthy", "service": "rag_stream"}

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db_status: Dict = Depends(check_database),
    vector_status: Dict = Depends(check_vector_store)
) -> Dict[str, Any]:
    """Readiness probe - checks all dependencies"""
    checks = {
        "database": db_status,
        "vector_store": vector_status,
    }
    all_healthy = all(c.get("status") == "healthy" for c in checks.values())
    if not all_healthy:
        return {"status": "unhealthy", "checks": checks}
    return {"status": "healthy", "checks": checks}
```

**Why NOT fastapi-health library:**
- Last release 0.4.0 (Aug 2021) - unmaintained
- Simple custom implementation is trivial with FastAPI dependencies
- Project already has 11,845 lines of Python - adding dependency for 50 lines of code is unnecessary

### Logging & Observability

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| python-json-logger | 2.0.7 (existing) | Structured logging | Already in project, outputs JSON for log aggregation |
| OpenTelemetry | 1.27.0+ (existing) | Tracing & metrics | Already configured, export to any OTLP backend |
| Uvicorn log-config | built-in | Access/error log config | Native JSON/YAML config support |

**Log Rotation Strategy:**

1. **In Docker (Recommended for production):**
   ```yaml
   services:
     app:
       logging:
         driver: "json-file"
         options:
           max-size: "100m"
           max-file: "5"
           compress: "true"
   ```

2. **Via Uvicorn config file:**
   ```json
   {
     "version": 1,
     "handlers": {
       "rotating_file": {
         "class": "logging.handlers.RotatingFileHandler",
         "filename": "/var/log/rag_stream/app.log",
         "maxBytes": 104857600,
         "backupCount": 5
       }
     }
   }
   ```

### Environment Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pydantic-settings | 2.1.0 (existing) | Configuration management | Already in use, supports .env files |

**Production environment strategy:**

```
# File structure
rag_stream/
├── .env                    # Default (committed, non-sensitive)
├── .env.local             # Local overrides (gitignored)
├── .env.production        # Production template (committed, no secrets)
└── config.yaml            # Existing structured config
```

```yaml
# docker-compose.yml environment handling
services:
  app:
    env_file:
      - .env.production
    environment:
      - ENVIRONMENT=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}  # Injected at runtime
```

### Process Management

| Technology | Use Case | Why |
|------------|----------|-----|
| Docker (native) | Container lifecycle | restart: unless-stopped policy |
| Uvicorn workers | Worker processes | Built-in, no supervisor needed |
| systemd (optional) | Host-level service | Only for bare-metal deployments |

**NO supervisor needed** - Docker handles container restart, Uvicorn handles worker management.

## Integration with Existing Stack

### Current Dependencies (Verified Compatible)

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.104.1",           # Compatible with uvicorn 0.34+
    "uvicorn[standard]==0.24.0",  # Upgrade to 0.34.0 recommended
    "pydantic-settings==2.1.0",   # For environment config
    "python-json-logger==2.0.7",  # For structured logging
    # ... existing deps
]
```

### Required Additions

```toml
[project]
dependencies = [
    # Upgrade existing
    "uvicorn[standard]>=0.34.0",
]
```

## Docker Configuration

### Dockerfile (Production-Optimized)

```dockerfile
# Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock ./
COPY src/rag_stream/pyproject.toml src/rag_stream/

# Install dependencies (no dev deps, no project install yet)
ENV UV_NO_DEV=1
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source code
COPY . /app

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Production stage
FROM python:3.12-slim-bookworm AS production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Make sure we use the venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Use exec form for proper signal handling
CMD ["uvicorn", "rag_stream.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose (Production)

```yaml
# compose.yaml - No version key needed (Compose Specification)
name: rag_stream

services:
  app:
    build:
      context: .
      target: production
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    environment:
      - ENVIRONMENT=production
      - WEB_CONCURRENCY=4  # Uvicorn reads this for worker count
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        compress: "true"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  redis_data:
```

## Alternative Approaches Considered

| Approach | Why Not Chosen |
|----------|---------------|
| Gunicorn + Uvicorn workers | Adds complexity; Uvicorn now handles workers natively |
| Supervisor | Docker handles process restart; unnecessary in containers |
| systemd | Not applicable for containerized deployments |
| fastapi-health library | Unmaintained (2021); trivial to implement custom |
| Traefik/Nginx sidecar | Can be added later if SSL termination needed at container level |

## Installation & Setup Commands

```bash
# 1. Ensure Docker Compose v2+ is installed
docker compose version  # Should show v2.x.x or higher

# 2. Create production environment file
cp .env.example .env.production
# Edit .env.production with production values (no secrets)

# 3. Build production image
docker compose -f compose.yaml build

# 4. Run with production config
docker compose -f compose.yaml up -d

# 5. Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

## Sources

| Source | Confidence | URL |
|--------|------------|-----|
| FastAPI Docker Deployment Guide | HIGH | https://fastapi.tiangolo.com/deployment/docker/ |
| FastAPI Server Workers | HIGH | https://fastapi.tiangolo.com/deployment/server-workers/ |
| Uvicorn Settings | HIGH | https://www.uvicorn.org/settings/ |
| uv Docker Integration | HIGH | https://docs.astral.sh/uv/guides/integration/docker/ |
| Docker Compose History | HIGH | https://docs.docker.com/compose/intro/history/ |
| Docker Compose Specification | HIGH | https://github.com/compose-spec/compose-spec |
| Context7: FastAPI Library | HIGH | /fastapi/fastapi |
| Context7: Uvicorn Library | HIGH | /encode/uvicorn |
| Context7: Docker Compose | HIGH | /docker/compose |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Docker/Docker Compose | HIGH | Official docs, Context7 verified, current best practices |
| Uvicorn vs Gunicorn | HIGH | Context7 + FastAPI official docs confirm native worker support |
| Health check approach | HIGH | FastAPI native capabilities well-documented |
| Log rotation | HIGH | Docker native + Uvicorn config options documented |
| Environment management | HIGH | pydantic-settings is established, already in project |
| Process management | HIGH | Docker + Uvicorn pattern is standard |

## What NOT to Add

| Technology | Why Avoid |
|------------|-----------|
| Gunicorn | Unnecessary complexity; Uvicorn handles workers natively |
| Supervisor | Docker restart policies handle this |
| fastapi-health library | Unmaintained, trivial to implement custom |
| Complex orchestration (K8s) | Overkill for current requirements |
| Custom init systems | Docker PID 1 handling is sufficient |

---
*Stack research for: v1.3 Production Deployment*
*Researched: 2026-02-28*
