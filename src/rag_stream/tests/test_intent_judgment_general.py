from dataclasses import dataclass

from rag_stream.services.intent_service import BaseIntentService
from rag_stream.services.intent_service import IntentService
from rag_stream.services.intent_service.base_intent_service import IntentRecognizerSettings


@dataclass
class MockRetrievalResult:
    database: str
    question: str
    total_similarity: float


def test_intent_recognizer_should_return_mapped_type_and_table_results():
    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.61),
        MockRetrievalResult(database="table_b", question="B1", total_similarity=0.95),
        MockRetrievalResult(database="table_b", question="B2", total_similarity=0.73),
        MockRetrievalResult(database="table_a", question="A2", total_similarity=0.45),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="查询企业态势",
        all_results=all_results,
        database_mapping={"table_a": 1, "table_b": 2},
        default_type=0,
        similarity_threshold=0.6,
        top_k=5,
    )

    assert result.intent_type == 2
    assert result.database == "table_b"
    assert result.similarity == 0.95
    assert [item.question for item in result.database_results] == ["B1", "B2"]


def test_intent_recognizer_should_downgrade_when_top_similarity_not_reach_threshold():
    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.45),
        MockRetrievalResult(database="table_a", question="A2", total_similarity=0.44),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="低相似度查询",
        all_results=all_results,
        database_mapping={"table_a": 1},
        default_type=0,
        similarity_threshold=0.8,
        top_k=5,
    )

    assert result.intent_type == 0
    assert result.database == "table_a"
    assert result.similarity == 0.45
    assert [item.question for item in result.database_results] == ["A1", "A2"]


def test_intent_recognizer_should_support_custom_judge_function():
    all_results = [
        MockRetrievalResult(database="table_a", question="A1", total_similarity=0.95),
        MockRetrievalResult(database="table_b", question="B1", total_similarity=0.89),
    ]

    def pick_table_b(table_results, recognizer_settings):
        table_b = table_results.get("table_b", [])
        return table_b[0] if table_b else None

    result = BaseIntentService._recognize_intent_from_results(
        query="自定义判断函数",
        all_results=all_results,
        database_mapping={"table_a": 1, "table_b": 2},
        default_type=0,
        similarity_threshold=0.6,
        top_k=5,
        judge_function=pick_table_b,
    )

    assert result.intent_type == 2
    assert result.database == "table_b"
    assert result.similarity == 0.89


def test_daishan_priority_should_prioritize_instruction_table_when_over_threshold():
    recognizer_settings = IntentRecognizerSettings(
        database_mapping={
            "岱山-指令集": 1,
            "岱山-数据库问题": 2,
            "岱山-指令集-固定问题-0311": 3,
        },
        similarity_threshold=0.5,
        top_k=5,
        default_type=2,
        priority_similarity_threshold=0.6,
    )
    table_results = {
        "岱山-指令集": [
            MockRetrievalResult(database="岱山-指令集", question="I1", total_similarity=0.8)
        ],
        "岱山-数据库问题": [
            MockRetrievalResult(database="岱山-数据库问题", question="D1", total_similarity=0.95)
        ],
        "岱山-指令集-固定问题-0311": [],
    }

    result = IntentService._judge_daishan_intent_priority(table_results, recognizer_settings)

    assert result.database == "岱山-指令集"
    assert result.total_similarity == 0.8


def test_daishan_priority_should_fallback_to_db_question_table_when_priority_not_over_threshold():
    recognizer_settings = IntentRecognizerSettings(
        database_mapping={
            "岱山-指令集": 1,
            "岱山-数据库问题": 2,
            "岱山-指令集-固定问题-0311": 3,
        },
        similarity_threshold=0.7,
        top_k=5,
        default_type=2,
        priority_similarity_threshold=0.6,
    )
    table_results = {
        "岱山-指令集": [
            MockRetrievalResult(database="岱山-指令集", question="I1", total_similarity=0.59)
        ],
        "岱山-数据库问题": [
            MockRetrievalResult(database="岱山-数据库问题", question="D1", total_similarity=0.55)
        ],
        "岱山-指令集-固定问题-0311": [
            MockRetrievalResult(
                database="岱山-指令集-固定问题-0311", question="F1", total_similarity=0.58
            )
        ],
    }

    result = IntentService._judge_daishan_intent_priority(table_results, recognizer_settings)

    assert result.database == "岱山-数据库问题"
    assert result.total_similarity == 0.55


def test_daishan_priority_should_support_0311_fixed_question_table_name():
    recognizer_settings = IntentRecognizerSettings(
        database_mapping={
            "岱山-指令集": 1,
            "岱山-数据库问题": 2,
            "岱山-指令集-固定问题-0311": 3,
        },
        similarity_threshold=0.5,
        top_k=5,
        default_type=2,
        priority_similarity_threshold=0.6,
    )
    table_results = {
        "岱山-指令集": [
            MockRetrievalResult(database="岱山-指令集", question="I1", total_similarity=0.58)
        ],
        "岱山-数据库问题": [
            MockRetrievalResult(database="岱山-数据库问题", question="D1", total_similarity=0.55)
        ],
        "岱山-指令集-固定问题-0311": [
            MockRetrievalResult(
                database="岱山-指令集-固定问题-0311", question="F1", total_similarity=0.88
            )
        ],
    }

    result = IntentService._judge_daishan_intent_priority(table_results, recognizer_settings)

    assert result.database == "岱山-指令集-固定问题-0311"
    assert result.total_similarity == 0.88
