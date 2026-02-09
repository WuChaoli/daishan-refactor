import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List

from src.services.intent_recognizer import IntentRecognizerSettings
from src.services.intent_service import BaseIntentService


@dataclass
class MockRetrievalResult:
    database: str
    question: str
    total_similarity: float


class MockRagflowClient:
    def __init__(self, table_payload):
        self._table_payload = table_payload

    async def query_single_database(self, query, database):
        payload = self._table_payload.get(database, [])
        if isinstance(payload, Exception):
            raise payload
        return payload


class DummyIntentService(BaseIntentService):
    def _load_process_settings(self, text_input: str, user_id: str) -> IntentRecognizerSettings:
        return self._load_intent_recognizer_settings()

    async def _query_process_table_results(
        self,
        text_input: str,
        user_id: str,
        recognizer_settings: IntentRecognizerSettings,
    ) -> Dict[str, List[Any]]:
        return await self._query_table_results(
            query=text_input,
            recognizer_settings=recognizer_settings,
        )

    def _sort_process_table_results(
        self,
        text_input: str,
        user_id: str,
        table_results: Dict[str, List[Any]],
        recognizer_settings: IntentRecognizerSettings,
    ) -> List[Any]:
        return self._sort_table_results(
            table_results=table_results,
            recognizer_settings=recognizer_settings,
        )

    async def _post_process_result(self, text_input: str, user_id: str, intent_result) -> dict:
        return {"type": intent_result.type, "data": {"query": text_input, "user_id": user_id}}


def test_base_intent_service_should_run_full_intent_judgment_flow(tmp_path):
    mapping_path = tmp_path / "intent_mapping.test.json"
    mapping_path.write_text(
        json.dumps(
            {
                "database_mapping": {"table_a": 1, "table_b": 2},
                "similarity_threshold": 0.5,
                "top_k": 2,
                "default_type": 0,
            }
        ),
        encoding="utf-8",
    )

    client = MockRagflowClient(
        {
            "table_a": [
                MockRetrievalResult(database="table_a", question="A1", total_similarity=0.61),
            ],
            "table_b": [
                MockRetrievalResult(database="table_b", question="B1", total_similarity=0.91),
                MockRetrievalResult(database="table_b", question="B2", total_similarity=0.83),
            ],
        }
    )
    service = DummyIntentService(ragflow_client=client)

    result = asyncio.run(
        service._intent_judgment(
            query="查询企业态势",
            mapping_file=str(mapping_path),
        )
    )

    assert result.type == 2
    assert result.database == "table_b"
    assert result.similarity == 0.91
    assert [item.question for item in result.results] == ["B1", "B2"]


def test_base_intent_service_should_sort_table_results_by_similarity_desc():
    settings = IntentRecognizerSettings(
        database_mapping={"table_a": 1, "table_b": 2},
        similarity_threshold=0.5,
        top_k=5,
        default_type=0,
    )

    client = MockRagflowClient({})
    service = DummyIntentService(ragflow_client=client)

    table_results = {
        "table_a": [
            MockRetrievalResult(database="table_a", question="A1", total_similarity=0.22),
            MockRetrievalResult(database="table_a", question="A2", total_similarity=0.72),
        ],
        "table_b": [
            MockRetrievalResult(database="table_b", question="B1", total_similarity=0.95),
        ],
        "table_c": [
            MockRetrievalResult(database="table_c", question="C1", total_similarity=0.66),
        ],
    }

    sorted_results = service._sort_table_results(
        table_results=table_results,
        recognizer_settings=settings,
    )

    assert [item.question for item in sorted_results] == ["B1", "A2", "C1", "A1"]


def test_base_intent_service_should_return_empty_list_when_table_query_fails():
    settings = IntentRecognizerSettings(
        database_mapping={"table_a": 1, "table_b": 2, "table_c": 3},
        similarity_threshold=0.5,
        top_k=5,
        default_type=0,
    )

    client = MockRagflowClient(
        {
            "table_a": [MockRetrievalResult(database="table_a", question="A1", total_similarity=0.8)],
            "table_b": RuntimeError("mock query failure"),
            "table_c": "invalid-payload",
        }
    )
    service = DummyIntentService(ragflow_client=client)

    table_results = asyncio.run(service._query_table_results(query="测试", recognizer_settings=settings))

    assert [item.question for item in table_results["table_a"]] == ["A1"]
    assert table_results["table_b"] == []
    assert table_results["table_c"] == []
