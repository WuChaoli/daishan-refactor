# ============================================================
# Production Dockerfile for rag_stream FastAPI Service
# ============================================================
# Build: docker build -f src/rag_stream/Dockerfile -t rag_stream:latest .
# Run:   docker run -p 11028:11028 --env-file .env rag_stream:latest
# ============================================================

# ------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency package sources first (for layer caching)
# These are path dependencies required by rag_stream
COPY src/DaiShanSQL src/DaiShanSQL/
COPY src/dify_sdk src/dify_sdk/
COPY src/ragflow_sdk src/ragflow_sdk/
COPY src/log-manager src/log-manager/

# Copy rag_stream package files
COPY src/rag_stream/pyproject.toml src/rag_stream/
COPY src/rag_stream/src src/rag_stream/src
COPY src/rag_stream/static src/rag_stream/static
COPY src/rag_stream/README.md src/rag_stream/

# Create virtual environment and install packages
# First install path dependencies as editable packages
RUN cd /app/src/DaiShanSQL && pip install -e . && \
    cd /app/src/dify_sdk && pip install -e . && \
    cd /app/src/ragflow_sdk && pip install -e . && \
    cd /app/src/log-manager && pip install -e .

# Install rag_stream package
RUN cd /app/src/rag_stream && pip install -e .

# ------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Create non-root user and group
# Using fixed UID/GID 1000 for consistency across deployments
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy source code for path dependencies (required for editable installs)
COPY --from=builder --chown=appuser:appgroup /app/src/DaiShanSQL /app/src/DaiShanSQL
COPY --from=builder --chown=appuser:appgroup /app/src/dify_sdk /app/src/dify_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/ragflow_sdk /app/src/ragflow_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/log-manager /app/src/log-manager
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream /app/src/rag_stream

# Set PYTHONPATH to include all source directories
ENV PYTHONPATH="/app/src:/app/src/DaiShanSQL:/app/src/dify_sdk:/app/src/ragflow_sdk:/app/src/log-manager"

# Create logs directory for backward compatibility (owned by appuser)
# Note: In production, logs should go to stdout/stderr
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 11028

# Health check using Python's built-in http.client
# Falls back to checking if the process is responsive
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11028/health', timeout=5)" || exit 1

# Use exec form CMD for proper signal forwarding (SIGTERM handling)
# This ensures graceful shutdown when container receives stop signal
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "11028", "--workers", "4"]
