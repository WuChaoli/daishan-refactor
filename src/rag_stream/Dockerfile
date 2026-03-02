# ============================================================
# Production Dockerfile for rag_stream FastAPI Service
# ============================================================
# Build: docker build -f src/rag_stream/Dockerfile -t rag_stream:latest .
# Run:   docker run -p 11027:11027 --env-file .env rag_stream:latest
# ============================================================

# ------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1

ARG APP_ENV=production

WORKDIR /app

# Copy dependency package sources first (for layer caching)
# These are path dependencies required by rag_stream
COPY src/DaiShanSQL src/DaiShanSQL/
COPY src/dify_sdk src/dify_sdk/
COPY src/ragflow_sdk src/ragflow_sdk/
COPY src/log-manager src/log-manager/

# Copy rag_stream package files
COPY src/rag_stream/pyproject.toml src/rag_stream/
COPY src/rag_stream/config.yaml src/rag_stream/
COPY src/rag_stream/src src/rag_stream/src
COPY src/rag_stream/static src/rag_stream/static
COPY src/rag_stream/README.md src/rag_stream/

# Install workspace dependencies in non-editable mode to avoid stdlib shadowing issues
RUN uv pip install --system /app/src/DaiShanSQL && \
    uv pip install --system /app/src/dify_sdk && \
    uv pip install --system /app/src/ragflow_sdk && \
    uv pip install --system /app/src/log-manager

# Install rag_stream package
RUN uv pip install --system /app/src/rag_stream

# ------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ARG APP_ENV=production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    APP_ENV=${APP_ENV}

WORKDIR /app

# Create non-root user and group
# Using fixed UID/GID 1000 for consistency across deployments
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser

# Copy installed packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src/rag_stream/config.yaml /usr/local/lib/python3.12/site-packages/config.yaml
COPY --from=builder /app/src/rag_stream/static /usr/local/lib/python3.12/site-packages/static
COPY --from=builder /app/src/rag_stream/src/utils/source_type_mapping.json /usr/local/lib/python3.12/site-packages/rag_stream/utils/source_type_mapping.json

# Copy source code for path dependencies (required for editable installs)
COPY --from=builder --chown=appuser:appgroup /app/src/DaiShanSQL /app/src/DaiShanSQL
COPY --from=builder --chown=appuser:appgroup /app/src/dify_sdk /app/src/dify_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/ragflow_sdk /app/src/ragflow_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/log-manager /app/src/log-manager
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream /app/src/rag_stream

# Keep import path aligned with installed package location
ENV PYTHONPATH="/usr/local/lib/python3.12/site-packages"

# Create logs directory for backward compatibility (owned by appuser)
# Note: In production, logs should go to stdout/stderr
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs && \
    mkdir -p /usr/local/lib/python3.12/site-packages/.log-manager && \
    chown -R appuser:appgroup /usr/local/lib/python3.12/site-packages/.log-manager

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 11027

# Health check using Python's built-in http.client
# Falls back to checking if the process is responsive
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11027/health', timeout=5)" || exit 1

# Use exec form CMD for proper signal forwarding (SIGTERM handling)
# This ensures graceful shutdown when container receives stop signal
# Workers=4 matches docker-compose resource limits
# Timeout settings align with docker-compose stop_grace_period: 30s
CMD ["uvicorn", "rag_stream.main:app", "--host", "0.0.0.0", "--port", "11027", "--workers", "4", "--timeout-keep-alive", "30", "--timeout-graceful-shutdown", "30"]
