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

# Copy workspace dependency files first (for optimal layer caching)
# Copy root workspace files
COPY pyproject.toml uv.lock ./

# Copy workspace member pyproject.toml files (needed for workspace resolution)
COPY src/rag_stream/pyproject.toml src/rag_stream/
COPY src/DaiShanSQL/pyproject.toml src/DaiShanSQL/
COPY src/dify_sdk/pyproject.toml src/dify_sdk/
COPY src/ragflow_sdk/pyproject.toml src/ragflow_sdk/
COPY src/log-manager/pyproject.toml src/log-manager/

# Copy source directories (needed for editable installs)
COPY src/DaiShanSQL/DaiShanSQL src/DaiShanSQL/DaiShanSQL
COPY src/dify_sdk/dify_sdk src/dify_sdk/dify_sdk
COPY src/ragflow_sdk/ragflow_sdk src/ragflow_sdk/ragflow_sdk
COPY src/log-manager/log_manager src/log-manager/log_manager

# Copy rag_stream source (excluding tests - handled by .dockerignore)
COPY src/rag_stream/src src/rag_stream/src
COPY src/rag_stream/static src/rag_stream/static
COPY src/rag_stream/config.yaml src/rag_stream/config.yaml
COPY src/rag_stream/README.md src/rag_stream/

# Install dependencies using uv sync
# --frozen: Use exact versions from lockfile
# --no-dev: Skip dev dependencies for production
RUN cd src/rag_stream && uv sync --frozen --no-dev

# ------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create non-root user and group
# Using fixed UID/GID 1000 for consistency across deployments
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream/.venv /app/.venv

# Copy application code with correct ownership
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream/src ./src
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream/static ./static
COPY --from=builder --chown=appuser:appgroup /app/src/rag_stream/config.yaml ./config.yaml

# Copy workspace dependencies (editable installs)
COPY --from=builder --chown=appuser:appgroup /app/src/DaiShanSQL /app/src/DaiShanSQL
COPY --from=builder --chown=appuser:appgroup /app/src/dify_sdk /app/src/dify_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/ragflow_sdk /app/src/ragflow_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/log-manager /app/src/log-manager

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
