import asyncio
import json
from dataclasses import dataclass

from rag_stream.services.intent_service import IntentService


@dataclass
class MockRetrievalResult:
    database: str
    question: str
    total_similarity: float


class MockRagflowClient:
    def __init__(self, all_results):
        self._grouped = {}
        for item in all_results:
            self._grouped.setdefault(item.database, []).append(item)

    async def query_single_database(self, query, database):
        return self._grouped.get(database, [])


def test_intent_judgment_should_return_mapped_type_and_table_results():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fp:
        json.dump({"database_mapping": {"table_a": 1, "table_b": 2}}, fp)
        mapping_file = fp.name

    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.61),
        MockRetrievalResult(database="table_b", question="B1", total_similarity=0.95),
        MockRetrievalResult(database="table_b", question="B2", total_similarity=0.73),
        MockRetrievalResult(database="table_a", question="A2", total_similarity=0.45),
    ]
    client = MockRagflowClient(all_results=all_results)
    service = IntentService(ragflow_client=client)

    result = asyncio.run(
        service._intent_judgment(
            query="查询企业态势",
            mapping_file=mapping_file,
        )
    )

    assert result.type == 2
    assert result.database == "table_b"
    assert result.similarity == 0.95
    assert [item.question for item in result.results] == ["B1", "B2"]


def test_intent_judgment_should_downgrade_when_top_similarity_not_reach_threshold():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fp:
        json.dump(
            {
                "database_mapping": {"table_a": 1},
                "similarity_threshold": 0.8,
                "default_type": 0,
                "top_k": 5,
            },
            fp,
        )
        mapping_file = fp.name

    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.45),
        MockRetrievalResult(database="table_a", question="A2", total_similarity=0.44),
    ]
    client = MockRagflowClient(all_results=all_results)
    service = IntentService(ragflow_client=client)

    result = asyncio.run(
        service._intent_judgment(
            query="低相似度查询",
            mapping_file=mapping_file,
        )
    )

    assert result.type == 0
    assert result.database == "table_a"
    assert result.similarity == 0.45
    assert [item.question for item in result.results] == ["A1", "A2"]


def test_intent_judgment_should_support_custom_judge_function():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fp:
        json.dump({"database_mapping": {"table_a": 1, "table_b": 2}}, fp)
        mapping_file = fp.name

    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.95),
        MockRetrievalResult(database="table_b", question="B1", total_similarity=0.89),
    ]
    client = MockRagflowClient(all_results=all_results)
    service = IntentService(ragflow_client=client)

    def pick_table_b(table_results, recognizer_settings):
        table_b = table_results.get("table_b", [])
        return table_b[0] if table_b else None

    result = asyncio.run(
        service._intent_judgment(
            query="自定义判断函数",
            judge_function=pick_table_b,
            mapping_file=mapping_file,
        )
    )

    assert result.type == 2
    assert result.database == "table_b"
    assert result.similarity == 0.89


def test_intent_judgment_should_prioritize_instruction_table_when_over_threshold():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fp:
        json.dump(
            {
                "database_mapping": {
                    "岱山-指令集": 1,
                    "岱山-数据库问题": 2,
                },
                "similarity_threshold": 0.5,
                "default_type": 0,
                "top_k": 5,
            },
            fp,
        )
        mapping_file = fp.name

    all_results = [
        MockRetrievalResult(database="岱山-指令集", question="I1", total_similarity=0.8),
        MockRetrievalResult(database="岱山-数据库问题", question="D1", total_similarity=0.95),
    ]
    client = MockRagflowClient(all_results=all_results)
    service = IntentService(ragflow_client=client)

    result = asyncio.run(
        service._intent_judgment(
            query="优先指令集",
            mapping_file=mapping_file,
        )
    )

    assert result.type == 1
    assert result.database == "岱山-指令集"


def test_intent_judgment_should_fallback_to_db_question_table_when_instruction_not_over_threshold():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fp:
        json.dump(
            {
                "database_mapping": {
                    "岱山-指令集": 1,
                    "岱山-数据库问题": 2,
                },
                "similarity_threshold": 0.7,
                "default_type": 0,
                "top_k": 5,
            },
            fp,
        )
        mapping_file = fp.name

    all_results = [
        MockRetrievalResult(database="岱山-指令集", question="I1", total_similarity=0.6),
        MockRetrievalResult(database="岱山-数据库问题", question="D1", total_similarity=0.55),
    ]
    client = MockRagflowClient(all_results=all_results)
    service = IntentService(ragflow_client=client)

    result = asyncio.run(
        service._intent_judgment(
            query="回退数据库问题",
            mapping_file=mapping_file,
        )
    )

    assert result.type == 2
    assert result.database == "岱山-数据库问题"
