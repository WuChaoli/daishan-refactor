"""FastAPI lifespan context manager for service lifecycle management.

This module provides the main lifespan context manager that orchestrates
startup initialization and graceful shutdown for the rag_stream service.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from rag_stream.shutdown import close_database, close_http_client
from rag_stream.startup import (
    init_database,
    init_http_client,
    wait_for_external_services,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown management.

    This context manager handles:
    - Startup: Initialize database check, HTTP client, and external services
    - Shutdown: Release all resources in reverse order of initialization

    Resources are stored in app.state for access by request handlers.

    Args:
        app: The FastAPI application instance

    Yields:
        None (control passes to application runtime)

    Example:
        app = FastAPI(lifespan=lifespan)
    """
    start_time = time.time()
    logger.info("[LIFECYCLE] ========================================")
    logger.info("[LIFECYCLE] Service startup sequence initiated")
    logger.info("[LIFECYCLE] ========================================")

    # Track resources for cleanup
    http_client = None

    try:
        # ============================================
        # STARTUP PHASE
        # ============================================

        # 1. Check database configuration
        try:
            db_resource = await init_database()
            app.state.db_resource = db_resource
            logger.info("[LIFECYCLE] Database configuration checked")
        except Exception as exc:
            logger.error(f"[LIFECYCLE] Database configuration check failed: {exc}")
            app.state.db_resource = None

        # 2. Initialize HTTP client with connection pooling
        try:
            http_client = await init_http_client()
            app.state.http_client = http_client
            logger.info("[LIFECYCLE] HTTP client initialized and stored in app.state")
        except ValueError as exc:
            logger.error(f"[LIFECYCLE] HTTP client initialization failed: {exc}")
            app.state.http_client = None

        # 3. Check external services (best-effort)
        try:
            service_status = await wait_for_external_services(http_client)
            app.state.service_status = service_status
            ready_count = sum(1 for v in service_status.values() if v)
            total_count = len(service_status)
            logger.info(
                f"[LIFECYCLE] External services check complete: "
                f"{ready_count}/{total_count} ready"
            )
        except Exception as exc:
            logger.warning(f"[LIFECYCLE] External service check failed: {exc}")
            app.state.service_status = {"dify": False, "ragflow": False}

        # Calculate startup duration
        startup_duration = time.time() - start_time
        logger.info("[LIFECYCLE] ========================================")
        logger.info(f"[LIFECYCLE] Startup completed in {startup_duration:.2f}s")
        logger.info("[LIFECYCLE] Service is ready to accept requests")
        logger.info("[LIFECYCLE] ========================================")

        # Yield control to application
        yield

    except Exception as exc:
        logger.exception("[LIFECYCLE] Fatal error during startup")
        raise

    finally:
        # ============================================
        # SHUTDOWN PHASE
        # ============================================
        shutdown_start = time.time()
        logger.info("[LIFECYCLE] ========================================")
        logger.info("[LIFECYCLE] Shutdown sequence initiated (SIGTERM received)")
        logger.info("[LIFECYCLE] ========================================")

        try:
            # Retrieve resources from app.state (may have been set elsewhere)
            db_resource = getattr(app.state, "db_resource", None)
            http_client = getattr(app.state, "http_client", http_client)

            # Close HTTP client first (higher-level resource)
            await close_http_client(http_client)

            # Clean up database resources
            await close_database(db_resource)

            shutdown_duration = time.time() - shutdown_start
            logger.info("[LIFECYCLE] ========================================")
            logger.info(f"[LIFECYCLE] Shutdown completed in {shutdown_duration:.2f}s")
            logger.info("[LIFECYCLE] All resources released successfully")
            logger.info("[LIFECYCLE] ========================================")

        except Exception as exc:
            logger.exception("[LIFECYCLE] Error during shutdown cleanup")
            # Don't re-raise - process should exit cleanly


# Export for direct import
app_lifespan = lifespan
