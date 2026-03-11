from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

if "DaiShanSQL" not in sys.modules:
    daishan_sql_stub = types.ModuleType("DaiShanSQL")

    class _StubSqlFixed:
        @staticmethod
        def sql_ChemicalCompanyInfo():
            return ""

        @staticmethod
        def sql_SecuritySituation():
            return ""

    class _StubServer:
        def __init__(self):
            self.sqlFixed = _StubSqlFixed()

        @staticmethod
        def QueryBySQL(*args, **kwargs):
            return {"data": []}

        @staticmethod
        def get_sql_result(*args, **kwargs):
            return ""

        @staticmethod
        def judgeQuery(*args, **kwargs):
            return []

    daishan_sql_stub.Server = _StubServer
    sys.modules["DaiShanSQL"] = daishan_sql_stub

from rag_stream.services import chat_general_service
from rag_stream.services import source_dispath_srvice
from rag_stream.utils import fetch_table_structures
from rag_stream.utils.daishan_sql_logging import format_daishan_log_text


def test_format_daishan_log_text_should_be_single_line_and_truncated():
    text = "line1\nline2\nline3"
    output = format_daishan_log_text(text, max_length=10)

    assert "\n" not in output
    assert len(output) <= 10
    assert output.endswith("...")


def test_format_daishan_log_text_should_fallback_when_json_dump_fails():
    circular: dict[str, object] = {}
    circular["self"] = circular

    output = format_daishan_log_text(circular, max_length=50)

    assert isinstance(output, str)
    assert "\n" not in output


async def _run_post_process_type2_success():
    with patch.object(chat_general_service, "marker") as mock_marker:
        with patch.object(
            chat_general_service.asyncio,
            "to_thread",
            new=AsyncMock(return_value={"data": [{"id": 1}]}),
        ):
            result = await chat_general_service._post_process_type2(
                "查询内容",
                {"results": []},
            )

    assert result["type"] == 2
    names = [call.args[0] for call in mock_marker.call_args_list]
    assert "DaiShanSQL入参" in names
    assert "DaiShanSQL出参" in names


def test_post_process_type2_should_log_input_output():
    asyncio.run(_run_post_process_type2_success())


async def _run_post_process_type2_error():
    with patch.object(chat_general_service, "marker") as mock_marker:
        with patch.object(
            chat_general_service.asyncio,
            "to_thread",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            try:
                await chat_general_service._post_process_type2("查询内容", {"results": []})
            except RuntimeError:
                pass
            else:
                raise AssertionError("expected RuntimeError")

    has_error_marker = any(
        call.args and call.args[0] == "DaiShanSQL出参" and call.kwargs.get("level") == "ERROR"
        for call in mock_marker.call_args_list
    )
    assert has_error_marker


def test_post_process_type2_should_log_error_and_reraise():
    asyncio.run(_run_post_process_type2_error())


def test_query_accident_from_database_should_log_input_output():
    fake_server = Mock()
    fake_server.QueryBySQL.return_value = {"data": [{"ID": 1}]}

    with patch.object(source_dispath_srvice, "Server", return_value=fake_server):
        with patch.object(source_dispath_srvice, "marker") as mock_marker:
            result = source_dispath_srvice._query_accident_from_database("SELECT 1")

    assert result == {"data": [{"ID": 1}]}
    names = [call.args[0] for call in mock_marker.call_args_list]
    assert "DaiShanSQL入参" in names
    assert "DaiShanSQL出参" in names


async def _run_execute_resource_query_logs():
    fake_server = Mock()
    fake_server.QueryBySQL.return_value = {"data": [{"ID": "1"}]}

    with patch.object(source_dispath_srvice, "_get_sql_from_mapping", return_value="SELECT 1"):
        with patch.object(source_dispath_srvice, "Server", return_value=fake_server):
            with patch.object(source_dispath_srvice, "marker") as mock_marker:
                rows = await source_dispath_srvice._execute_resource_query("emergencySupplies")

    assert rows == [{"ID": "1"}]
    names = [call.args[0] for call in mock_marker.call_args_list]
    assert "DaiShanSQL入参" in names
    assert "DaiShanSQL出参" in names


def test_execute_resource_query_should_log_input_output():
    asyncio.run(_run_execute_resource_query_logs())


def test_query_table_structure_should_log_input_output():
    fake_server = Mock()
    fake_server.QueryBySQL.return_value = {"data": []}

    with patch.object(fetch_table_structures, "marker") as mock_marker:
        columns = fetch_table_structures.query_table_structure(fake_server, "TABLE_A")

    assert columns == []
    names = [call.args[0] for call in mock_marker.call_args_list]
    assert "DaiShanSQL入参" in names
    assert "DaiShanSQL出参" in names


def test_type1_prompt_mapping_load_and_lookup_markers():
    with patch.object(chat_general_service, "marker") as mock_marker:
        with patch.object(
            chat_general_service,
            "_TYPE1_PROMPT_MAPPING_PATH",
            Path(__file__).resolve().parents[1]
            / "src"
            / "services"
            / "data"
            / "type1_question_mapping.json",
        ):
            chat_general_service._clear_prompt_mapping_cache()
            _ = chat_general_service._find_type1_mapping_by_question("I 企业的情况介绍一下")

    names = [call.args[0] for call in mock_marker.call_args_list if call.args]
    assert "type1.prompt_mapping_loaded" in names
    assert "type1.prompt_mapping_lookup" in names


async def _run_fixed_question_prompt_fallback_marker():
    request = chat_general_service.ChatRequest(
        question="查询重点监管危化品",
        user_id="user-001",
        stream=True,
    )

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区有哪些重点监管危化品\tAnswer: v_ai_ipark_enterprise_key_chemicals",
                "similarity": 0.77,
            }
        ]
    )
    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch.object(
            chat_general_service,
            "replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch.object(
            chat_general_service,
            "_find_type3_prompt_by_question",
            return_value="",
        ),
        patch.object(chat_general_service, "marker") as mock_marker,
    ):
        await chat_general_service.handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    names = [call.args[0] for call in mock_marker.call_args_list if call.args]
    assert "fixed_question_prompt_unavailable" in names


def test_fixed_question_prompt_mapping_fallback_marker():
    asyncio.run(_run_fixed_question_prompt_fallback_marker())


async def _run_fixed_question_fallback_reason_marker_at_threshold():
    request = chat_general_service.ChatRequest(
        question="园区地址在哪",
        user_id="user-threshold",
        stream=True,
    )

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区地址在哪	Answer: 园区地址信息",
                "similarity": 0.6,
            }
        ]
    )
    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch.object(
            chat_general_service,
            "replace_economic_zone",
            new=AsyncMock(return_value=request.question),
        ),
        patch.object(chat_general_service, "marker") as mock_marker,
    ):
        await chat_general_service.handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    matched_calls = [
        call
        for call in mock_marker.call_args_list
        if call.args and call.args[0] == "fixed_question_route_fallback"
    ]
    assert matched_calls

    fallback_data = matched_calls[-1].args[1]
    assert fallback_data["reason"] == "single_candidate_at_similarity_threshold"
    assert fallback_data["best_similarity"] == 0.6
    assert fallback_data["raw_candidate_count"] == 1
    assert fallback_data["top_candidate_count"] == 1


def test_fixed_question_fallback_reason_marker_at_threshold():
    asyncio.run(_run_fixed_question_fallback_reason_marker_at_threshold())


async def _run_fixed_question_ragflow_and_decision_logging():
    request = chat_general_service.ChatRequest(
        question="介绍一下岱山经开区情况",
        user_id="user-log",
        session_id="session-log",
        stream=False,
    )

    intent_service = AsyncMock()
    intent_service.query_fixed_question_candidates = AsyncMock(
        return_value=[
            {
                "question": "Question: 园区地址在哪\tAnswer: 园区地址信息",
                "similarity": 0.70,
            },
            {
                "question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
                "similarity": 0.65,
            },
        ]
    )
    chat_with_category = AsyncMock(return_value={"ok": True})

    with (
        patch.object(
            chat_general_service,
            "replace_economic_zone",
            new=AsyncMock(return_value="介绍一下园区情况"),
        ),
        patch.object(
            chat_general_service,
            "_find_type3_prompt_by_question",
            return_value="PROMPT",
        ),
        patch.object(
            chat_general_service,
            "asyncio",
            wraps=chat_general_service.asyncio,
        ) as mocked_asyncio,
        patch.object(chat_general_service, "marker") as mock_marker,
    ):
        mocked_asyncio.to_thread = AsyncMock(return_value={"rows": [{"name": "园区"}]})
        await chat_general_service.handle_chat_general(
            request=request,
            intent_service=intent_service,
            chat_with_category=chat_with_category,
        )

    matched_ragflow_calls = [
        call
        for call in mock_marker.call_args_list
        if call.args and call.args[0] == "fixed_question_ragflow_result"
    ]
    assert matched_ragflow_calls
    ragflow_payload = matched_ragflow_calls[-1].args[1]
    assert ragflow_payload["query_original"] == "介绍一下岱山经开区情况"
    assert ragflow_payload["query_rewritten"] == "介绍一下园区情况"
    assert ragflow_payload["similarity_threshold"] == 0.6
    assert ragflow_payload["direct_threshold"] == 0.7
    assert ragflow_payload["ragflow_candidates"][0]["question"] == "园区地址在哪"
    assert ragflow_payload["ragflow_candidates"][0]["similarity"] == 0.7

    matched_decision_calls = [
        call
        for call in mock_marker.call_args_list
        if call.args and call.args[0] == "fixed_question_decision"
    ]
    assert matched_decision_calls
    decision_payload = matched_decision_calls[-1].args[1]
    assert decision_payload["decision"] == "direct_hit"
    assert decision_payload["selected_question"] == "园区地址在哪"
    assert decision_payload["best_similarity"] == 0.7


def test_fixed_question_should_log_ragflow_result_and_decision_process():
    asyncio.run(_run_fixed_question_ragflow_and_decision_logging())


def test_mysql_manager_should_print_full_sql_before_request():
    import importlib.util
    from unittest.mock import Mock, patch

    module_path = (
        Path(__file__).resolve().parents[2]
        / "DaiShanSQL"
        / "DaiShanSQL"
        / "SQL"
        / "sql_utils.py"
    )
    spec = importlib.util.spec_from_file_location("daishan_sql_utils_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)

    manager = module.MySQLManager()
    manager.api_url_ds = "http://sql-api.example/query"
    manager.request_timeout = 3

    response = Mock()
    response.status_code = 200
    response.json.return_value = {"code": 200, "msg": "ok", "data": []}

    sql_text = "SELECT id, company_name FROM demo_table WHERE park_name = '岱山经济开发区'"

    with patch.object(module.requests, "post", return_value=response) as mock_post:
        with patch("builtins.print") as mock_print:
            result = manager.request_api_sql(sql_text)

    assert result["code"] == 200
    mock_post.assert_called_once()
    mock_print.assert_any_call(f"[DaiShanSQL FULL SQL] {sql_text}", flush=True)
