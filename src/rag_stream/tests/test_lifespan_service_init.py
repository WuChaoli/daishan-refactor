"""Tests for service initialization in application lifespan."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI

from rag_stream.lifespan import lifespan


async def _run_lifespan_once() -> tuple[object, object]:
    app = FastAPI()
    mock_ragflow_client = Mock()
    mock_ragflow_client.test_connection.return_value = True
    mock_intent_service = Mock()

    with (
        patch("rag_stream.lifespan.init_database", AsyncMock(return_value=None)),
        patch("rag_stream.lifespan.init_http_client", AsyncMock(return_value=Mock())),
        patch(
            "rag_stream.lifespan.wait_for_external_services",
            AsyncMock(return_value={"dify": True, "ragflow": True}),
        ),
        patch("rag_stream.lifespan.close_http_client", AsyncMock()),
        patch("rag_stream.lifespan.close_database", AsyncMock()),
        patch(
            "rag_stream.lifespan.RagflowClient",
            return_value=mock_ragflow_client,
        ),
        patch(
            "rag_stream.lifespan.IntentService",
            return_value=mock_intent_service,
        ),
    ):
        async with lifespan(app):
            ragflow_client = getattr(app.state, "ragflow_client", None)
            intent_service = getattr(app.state, "intent_service", None)
            return ragflow_client, intent_service


def test_lifespan_should_initialize_ragflow_and_intent_service():
    ragflow_client, intent_service = asyncio.run(_run_lifespan_once())
    assert ragflow_client is not None
    assert intent_service is not None
