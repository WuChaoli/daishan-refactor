import asyncio
import json
import pytest
from dataclasses import dataclass

from src.services.intent_service.base_intent_service import (
    BaseIntentService,
)


@dataclass
class MockResult:
    database: str
    question: str
    total_similarity: float


def test_recognize_intent_should_pick_highest_similarity_database():
    query = "查询园区企业信息"
    all_results = [
        MockResult(database="db_type1", question="Q1", total_similarity=0.62),
        MockResult(database="db_type2", question="Q2", total_similarity=0.91),
        MockResult(database="db_type2", question="Q3", total_similarity=0.78),
        MockResult(database="db_type1", question="Q4", total_similarity=0.65),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query=query,
        all_results=all_results,
        database_mapping={"db_type1": 1, "db_type2": 2},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
    )

    assert result.query == query
    assert result.intent_type == 2
    assert result.database == "db_type2"
    assert result.similarity == 0.91
    assert [item.question for item in result.database_results] == ["Q2", "Q3"]


def test_recognize_intent_should_downgrade_when_similarity_below_threshold():
    all_results = [
        MockResult(database="db_type1", question="Q1", total_similarity=0.30),
        MockResult(database="db_type1", question="Q2", total_similarity=0.21),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="低相似度问题",
        all_results=all_results,
        database_mapping={"db_type1": 1},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
    )

    assert result.intent_type == 0
    assert result.database == "db_type1"
    assert result.similarity == 0.30


def test_recognize_intent_should_use_default_type_when_database_not_mapped():
    all_results = [
        MockResult(database="unknown_db", question="Q1", total_similarity=0.89),
        MockResult(database="unknown_db", question="Q2", total_similarity=0.60),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="未知库问题",
        all_results=all_results,
        database_mapping={"db_type1": 1},
        default_type=0,
        similarity_threshold=0.5,
        top_k=1,
    )

    assert result.intent_type == 0
    assert result.database == "unknown_db"
    assert [item.question for item in result.database_results] == ["Q1"]


def test_recognize_intent_should_handle_empty_results():
    result = BaseIntentService._recognize_intent_from_results(
        query="空结果问题",
        all_results=[],
        database_mapping={"db_type1": 1},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
    )

    assert result.intent_type == 0
    assert result.database == ""
    assert result.similarity == 0.0
    assert result.database_results == []


def test_recognize_intent_should_support_string_mapping_value():
    all_results = [
        MockResult(database="db_type2", question="Q1", total_similarity=0.9),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="字符串映射问题",
        all_results=all_results,
        database_mapping={"db_type2": "2"},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
    )

    assert result.intent_type == 2


def test_recognize_intent_should_fallback_when_mapping_value_invalid_string():
    all_results = [
        MockResult(database="db_type2", question="Q1", total_similarity=0.9),
    ]

    result = BaseIntentService._recognize_intent_from_results(
        query="无效字符串映射问题",
        all_results=all_results,
        database_mapping={"db_type2": "type2"},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
    )

    assert result.intent_type == 0


class MockRagflowClient:
    def __init__(self, all_results):
        self._all_results = all_results
        self._grouped = {}
        for item in all_results:
            self._grouped.setdefault(item.database, []).append(item)

    async def query_all_databases(self, query):
        return self._all_results, []

    async def query_single_database(self, query, database):
        return self._grouped.get(database, [])


def test_recognize_intent_from_results_should_support_custom_judge_function():
    all_results = [
        MockResult(database="table_a", question="A1", total_similarity=0.95),
        MockResult(database="table_b", question="B1", total_similarity=0.91),
    ]

    def pick_table_b(table_results, recognizer_settings):
        table_b = table_results.get("table_b", [])
        return table_b[0] if table_b else None

    result = BaseIntentService._recognize_intent_from_results(
        query="自定义判断",
        all_results=all_results,
        database_mapping={"table_a": 1, "table_b": 2},
        default_type=0,
        similarity_threshold=0.5,
        top_k=5,
        judge_function=pick_table_b,
    )

    assert result.intent_type == 2
    assert result.database == "table_b"
