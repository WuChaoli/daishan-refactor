# ============================================================
# Production Dockerfile for Digital_human_command_interface Service
# ============================================================
# Build: docker build -f src/Digital_human_command_interface/Dockerfile -t digital_human:latest .
# Run:   docker run -p 11029:11029 --env-file .env digital_human:latest
# ============================================================

# ------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------
FROM python:3.12-bookworm AS builder

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency package sources first (for layer caching)
COPY src/ragflow_sdk src/ragflow_sdk/
COPY src/log-manager src/log-manager/
COPY src/log_decorator src/log_decorator/

# Copy Digital_human_command_interface package files
COPY src/Digital_human_command_interface/pyproject.toml src/Digital_human_command_interface/
COPY src/Digital_human_command_interface/src src/Digital_human_command_interface/src
COPY src/Digital_human_command_interface/main.py src/Digital_human_command_interface/
COPY src/Digital_human_command_interface/config.yaml src/Digital_human_command_interface/
COPY src/Digital_human_command_interface/README.md src/Digital_human_command_interface/

# Install path dependencies
RUN cd /app/src/ragflow_sdk && pip install -e . && \
    cd /app/src/log-manager && pip install -e . && \
    cd /app/src/log_decorator && pip install -e .

# Install Digital_human_command_interface package
RUN cd /app/src/Digital_human_command_interface && pip install -e .

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
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser

# Copy installed packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code for path dependencies
COPY --from=builder --chown=appuser:appgroup /app/src/ragflow_sdk /app/src/ragflow_sdk
COPY --from=builder --chown=appuser:appgroup /app/src/log-manager /app/src/log-manager
COPY --from=builder --chown=appuser:appgroup /app/src/log_decorator /app/src/log_decorator
COPY --from=builder --chown=appuser:appgroup /app/src/Digital_human_command_interface /app/src/Digital_human_command_interface

# Set PYTHONPATH
ENV PYTHONPATH="/app/src:/app/src/ragflow_sdk:/app/src/log-manager:/app/src/log_decorator"

# Create logs directory
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 11029

# Health check
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11029/health', timeout=5)" || exit 1

# Use exec form CMD for proper signal forwarding
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "11029", "--app-dir", "/app/src/Digital_human_command_interface"]
