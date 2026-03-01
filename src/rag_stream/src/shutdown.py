"""Shutdown cleanup utilities for rag_stream service.

This module provides cleanup functions for releasing HTTP client pools
and other resources during graceful shutdown.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def close_http_client(client: Optional[httpx.AsyncClient] = None) -> None:
    """Close httpx client and release connection pool.

    Args:
        client: httpx.AsyncClient to close. If None, logs a warning.

    Note:
        This function handles exceptions gracefully - if cleanup fails,
        the error is logged but not raised to prevent crashing shutdown.
    """
    if client is None:
        logger.info("[SHUTDOWN] No HTTP client to close")
        return

    logger.info("[SHUTDOWN] Closing HTTP client connection pool...")

    try:
        await client.aclose()
        logger.info("[SHUTDOWN] HTTP client connection pool closed successfully")

    except Exception as exc:
        logger.error(f"[SHUTDOWN] Error closing HTTP client: {exc}", exc_info=True)
        # Don't re-raise - shutdown should continue


async def close_database(db_resource: Optional[object] = None) -> None:
    """Close database-related resources.

    This is a placeholder for database cleanup. Currently, the service
    uses RAGFlow for data access rather than direct database connections.
    This function logs cleanup status for observability.

    Args:
        db_resource: Database resource to close (if any)

    Note:
        This function handles exceptions gracefully - if cleanup fails,
        the error is logged but not raised to prevent crashing shutdown.
    """
    if db_resource is None:
        logger.info("[SHUTDOWN] No database resources to close")
        return

    logger.info("[SHUTDOWN] Cleaning up database resources...")

    try:
        # Currently no direct database connections to clean up
        # RAGFlow client handles its own connection management
        logger.info("[SHUTDOWN] Database resources cleanup completed")

    except Exception as exc:
        logger.error(
            f"[SHUTDOWN] Error cleaning up database resources: {exc}", exc_info=True
        )
        # Don't re-raise - shutdown should continue


async def cleanup_all_resources(
    db_resource: Optional[object] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> dict:
    """Perform complete resource cleanup during shutdown.

    This is a convenience function that calls all cleanup functions
    in the correct order (higher-level resources first).

    Args:
        db_resource: Database resource to close (if any)
        http_client: HTTP client to close

    Returns:
        Dictionary with cleanup status for each resource:
        {"database": bool, "http_client": bool}
    """
    logger.info("[SHUTDOWN] Starting resource cleanup...")

    results = {
        "database": False,
        "http_client": False,
    }

    try:
        # Close HTTP client first (higher-level resource)
        await close_http_client(http_client)
        results["http_client"] = True

        # Close database resources (if any)
        await close_database(db_resource)
        results["database"] = True

        logger.info("[SHUTDOWN] Resource cleanup completed")

    except Exception as exc:
        logger.error(
            f"[SHUTDOWN] Unexpected error during cleanup: {exc}", exc_info=True
        )

    return results
