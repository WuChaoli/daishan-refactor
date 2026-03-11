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
        query_timeout=timeout,
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
        client = RagflowClient(ragflow_config, intent_config)
    client.datasets = [SimpleNamespace(name="db_a", id="dataset_1")]
    client.dataset_map = {"db_a": client.datasets[0]}
    return client


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



def test_query_single_database_should_log_summary_only():
    client = _build_client(timeout=17)

    async def fake_query_with_sdk(query, dataset):
        _ = (query, dataset)
        return [
            SimpleNamespace(
                database="db_a",
                question="问题A",
                total_similarity=0.91,
                keyword_similarity=0.0,
                vector_similarity=0.0,
            )
        ]

    client._query_with_sdk = fake_query_with_sdk

    with patch("rag_stream.utils.ragflow_client.marker") as mocked_marker:
        result = asyncio.run(client.query_single_database("hello", "db_a"))

    assert len(result) == 1
    matched = [call for call in mocked_marker.call_args_list if call.args and call.args[0] == "ragflow.query_single.complete"]
    assert matched
    payload = matched[-1].args[1]
    assert payload["database"] == "db_a"
    assert payload["query_len"] == 5
    assert payload["chunk_count"] == 1
    assert payload["top_question"] == "问题A"
    assert payload["top_similarity"] == 0.91
    assert "results" not in payload
    assert "chunks" not in payload


def test_query_all_databases_should_log_summary_only():
    client = _build_client(timeout=17)
    client.ragflow_config.database_mapping = {"db_a": 1, "db_b": 2}

    async def fake_query_single_database(query, database):
        _ = query
        if database == "db_a":
            return [
                SimpleNamespace(
                    database="db_a",
                    question="问题A",
                    total_similarity=0.91,
                    keyword_similarity=0.0,
                    vector_similarity=0.0,
                )
            ]
        return [
            SimpleNamespace(
                database="db_b",
                question="问题B",
                total_similarity=0.85,
                keyword_similarity=0.0,
                vector_similarity=0.0,
            )
        ]

    client.query_single_database = fake_query_single_database

    with patch("rag_stream.utils.ragflow_client.marker") as mocked_marker:
        all_results, _ = asyncio.run(client.query_all_databases("hello"))

    assert len(all_results) == 2
    matched = [call for call in mocked_marker.call_args_list if call.args and call.args[0] == "ragflow.query_all.complete"]
    assert matched
    payload = matched[-1].args[1]
    assert payload["query_len"] == 5
    assert payload["database_count"] == 2
    assert payload["result_count"] == 2
    assert payload["exception_count"] == 0
    assert payload["top_results"][0]["question"] == "问题A"
    assert payload["top_results"][0]["similarity"] == 0.91
    assert len(payload["top_results"]) == 2
    assert "results" not in payload
