import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from rag_stream.config.settings import IntentConfig, RAGFlowConfig
from rag_stream.utils.ragflow_client import RagflowClient


def _build_client(timeout: int) -> RagflowClient:
    ragflow_config = RAGFlowConfig(
        api_key="mock_key",
        base_url="http://mock.example.com/v1",
        timeout=timeout,
        max_retries=0,
        database_mapping={"db_a": 1},
    )
    intent_config = IntentConfig(
        similarity_threshold=0.5,
        top_k_per_database=10,
        default_type=0,
    )

    with patch.object(
        RagflowClient,
        "_get_datasets",
        return_value=[SimpleNamespace(name="db_a", id="dataset_1")],
    ):
        return RagflowClient(ragflow_config, intent_config)


def test_query_single_database_should_use_ragflow_timeout_from_config():
    client = _build_client(timeout=17)

    async def fake_query_with_sdk(query, dataset):
        _ = (query, dataset)
        return []

    client._query_with_sdk = fake_query_with_sdk

    captured: dict[str, float] = {}

    async def fake_wait_for(coro, timeout):
        captured["timeout"] = timeout
        return await coro

    with patch("rag_stream.utils.ragflow_client.asyncio.wait_for", new=AsyncMock(side_effect=fake_wait_for)):
        result = asyncio.run(client.query_single_database("hello", "db_a"))

    assert result == []
    assert captured["timeout"] == 17.0

