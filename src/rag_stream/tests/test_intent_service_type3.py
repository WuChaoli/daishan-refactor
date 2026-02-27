import asyncio
from dataclasses import dataclass

from rag_stream.services.intent_service import IntentService
from rag_stream.services.intent_service.base_intent_service import IntentResult, QueryResult


@dataclass
class MockRetrievalResult:
    database: str
    question: str
    total_similarity: float


class MockRagflowClient:
    def __init__(self, grouped_results):
        self._grouped_results = grouped_results

    async def query_single_database(self, query, database):
        return self._grouped_results.get(database, [])


def test_process_query_should_return_type3_when_fixed_question_table_is_top():
    client = MockRagflowClient(
        {
            "岱山-指令集": [
                MockRetrievalResult(
                    database="岱山-指令集",
                    question="Question: Q1\tAnswer: A1",
                    total_similarity=0.61,
                )
            ],
            "岱山-数据库问题": [
                MockRetrievalResult(
                    database="岱山-数据库问题",
                    question="Question: Q2\tAnswer: A2",
                    total_similarity=0.72,
                )
            ],
            "岱山-指令集-固定问题": [
                MockRetrievalResult(
                    database="岱山-指令集-固定问题",
                    question="Question: 东区的安全负责人是谁？\tAnswer: 园区安全负责人是谁",
                    total_similarity=0.95,
                )
            ],
        }
    )
    service = IntentService(ragflow_client=client)

    result = asyncio.run(service.process_query("查询东区安全负责人", "user-001"))

    assert result["type"] == 3
    assert result["database"] == "岱山-指令集-固定问题"
    assert result["answer"] == "园区安全负责人是谁"


def test_post_process_result_should_return_empty_answer_when_no_answer_segment():
    service = IntentService(ragflow_client=MockRagflowClient({}))
    intent_result = IntentResult(
        type=3,
        query="测试问题",
        results=[QueryResult(question="纯文本问题", similarity=0.9)],
        similarity=0.9,
        database="岱山-指令集-固定问题",
    )

    result = asyncio.run(service._post_process_result(intent_result))

    assert result["answer"] == ""


def test_process_query_should_prioritize_instruction_tables_when_reaching_priority_threshold():
    client = MockRagflowClient(
        {
            "岱山-指令集": [
                MockRetrievalResult(
                    database="岱山-指令集",
                    question="Question: Q1\tAnswer: A1",
                    total_similarity=0.71,
                )
            ],
            "岱山-数据库问题": [
                MockRetrievalResult(
                    database="岱山-数据库问题",
                    question="Question: Q2\tAnswer: A2",
                    total_similarity=0.95,
                )
            ],
            "岱山-指令集-固定问题": [],
        }
    )
    service = IntentService(ragflow_client=client)

    result = asyncio.run(service.process_query("测试优先阈值", "user-001"))

    assert result["type"] == 1
    assert result["database"] == "岱山-指令集"
    assert result["similarity"] == 0.71


def test_process_query_should_fallback_to_global_max_when_priority_tables_below_threshold():
    client = MockRagflowClient(
        {
            "岱山-指令集": [
                MockRetrievalResult(
                    database="岱山-指令集",
                    question="Question: Q1\tAnswer: A1",
                    total_similarity=0.69,
                )
            ],
            "岱山-数据库问题": [
                MockRetrievalResult(
                    database="岱山-数据库问题",
                    question="Question: Q2\tAnswer: A2",
                    total_similarity=0.82,
                )
            ],
            "岱山-指令集-固定问题": [
                MockRetrievalResult(
                    database="岱山-指令集-固定问题",
                    question="Question: Q3\tAnswer: A3",
                    total_similarity=0.66,
                )
            ],
        }
    )
    service = IntentService(ragflow_client=client)

    result = asyncio.run(service.process_query("测试降级分流", "user-001"))

    assert result["type"] == 2
    assert result["database"] == "岱山-数据库问题"
    assert result["similarity"] == 0.82
