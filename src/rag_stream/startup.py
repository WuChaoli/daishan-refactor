"""Startup initialization utilities for rag_stream service.

This module provides initialization functions for HTTP clients
and external service checks during application startup.
"""

import asyncio
import logging
from typing import Optional

import httpx

from rag_stream.config.settings import settings

logger = logging.getLogger(__name__)


async def init_http_client(
    timeout: float = 30.0,
    pool_connections: int = 10,
    pool_maxsize: int = 10,
) -> httpx.AsyncClient:
    """Create shared HTTP client with connection pooling.

    Args:
        timeout: Request timeout in seconds
        pool_connections: Number of connection pools to cache
        pool_maxsize: Maximum number of connections to save in pool

    Returns:
        Configured httpx.AsyncClient instance

    Raises:
        ValueError: If HTTP client initialization fails
    """
    logger.info("[STARTUP] Initializing HTTP client...")

    try:
        limits = httpx.Limits(
            max_connections=pool_maxsize,
            max_keepalive_connections=pool_connections,
        )

        client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=limits,
        )

        logger.info(
            f"[STARTUP] HTTP client initialized "
            f"(timeout={timeout}s, pool={pool_connections}/{pool_maxsize})"
        )
        return client

    except Exception as exc:
        logger.error(f"[STARTUP] HTTP client initialization failed: {exc}")
        raise ValueError(f"Failed to initialize HTTP client: {exc}") from exc


async def init_database() -> None:
    """Initialize database-related resources.

    This is a placeholder for database initialization. Currently,
    the service uses RAGFlow for data access rather than direct
    database connections. This function logs the database configuration
    status for observability.

    Returns:
        None - database is accessed via RAGFlow client
    """
    logger.info("[STARTUP] Checking database configuration...")

    try:
        # Check MySQL configuration is available
        if settings.mysql and settings.mysql.host:
            logger.info(
                f"[STARTUP] MySQL configured: {settings.mysql.host}:{settings.mysql.port}"
            )
        else:
            logger.warning("[STARTUP] MySQL configuration not found")

        # Return None - actual DB connections are managed by RAGFlow client
        return None

    except Exception as exc:
        logger.error(f"[STARTUP] Database configuration check failed: {exc}")
        # Don't raise - service can operate in degraded mode
        return None


async def wait_for_external_services(
    http_client: Optional[httpx.AsyncClient] = None,
    timeout: float = 30.0,
) -> dict:
    """Best-effort check for external service readiness.

    Polls Dify and RAGFlow services to check their availability.
    This is a best-effort check - service startup continues even if
    external services are not ready yet.

    Args:
        http_client: HTTP client to use for checks (creates new if None)
        timeout: Maximum time to wait for services in seconds

    Returns:
        Dictionary with service status: {"dify": bool, "ragflow": bool}
    """
    logger.info("[STARTUP] Checking external service readiness...")

    results = {"dify": False, "ragflow": False}
    client = http_client or httpx.AsyncClient(timeout=httpx.Timeout(5.0))

    try:
        # Check Dify service (if configured)
        if settings.dify and settings.dify.base_url:
            try:
                dify_base = str(settings.dify.base_url).rstrip("/")
                response = await client.get(
                    f"{dify_base}/health",
                    timeout=5.0,
                    follow_redirects=True,
                )
                results["dify"] = response.status_code == 200
                logger.info(
                    f"[STARTUP] Dify service check: "
                    f"{'ready' if results['dify'] else 'not ready'}"
                )
            except Exception as exc:
                logger.warning(f"[STARTUP] Dify service not reachable: {exc}")
        else:
            logger.info("[STARTUP] Dify service not configured, skipping check")

        # Check RAGFlow service (if configured)
        if settings.ragflow and settings.ragflow.base_url:
            try:
                ragflow_base = str(settings.ragflow.base_url).rstrip("/")
                response = await client.get(
                    f"{ragflow_base}/api/health",
                    timeout=5.0,
                    follow_redirects=True,
                )
                results["ragflow"] = response.status_code == 200
                logger.info(
                    f"[STARTUP] RAGFlow service check: "
                    f"{'ready' if results['ragflow'] else 'not ready'}"
                )
            except Exception as exc:
                logger.warning(f"[STARTUP] RAGFlow service not reachable: {exc}")
        else:
            logger.info("[STARTUP] RAGFlow service not configured, skipping check")

    except Exception as exc:
        logger.warning(f"[STARTUP] External service check failed: {exc}")

    finally:
        if http_client is None:
            await client.aclose()

    return results
