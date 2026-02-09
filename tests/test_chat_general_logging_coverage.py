"""校验 chat_general 下游链路函数均使用 @log 装饰。"""

from __future__ import annotations

import ast
from pathlib import Path


def _decorator_is_log(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "log"
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
        return decorator.func.id == "log"
    return False


def _module_functions_with_log(source_path: str) -> dict[str, bool]:
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    result: dict[str, bool] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = any(_decorator_is_log(d) for d in node.decorator_list)
    return result


def _class_methods_with_log(source_path: str, class_name: str) -> dict[str, bool]:
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            result: dict[str, bool] = {}
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[method.name] = any(
                        _decorator_is_log(d) for d in method.decorator_list
                    )
            return result
    raise AssertionError(f"Class {class_name} not found in {source_path}")


def test_chat_general_service_downstream_functions_have_log_decorator():
    functions_with_log = _module_functions_with_log(
        "src/rag_stream/src/services/chat_general_service.py"
    )
    expected = {
        "_extract_questions_for_sql",
        "_post_process_type1",
        "_route_with_sql_result",
        "_post_process_and_route_type1",
        "_post_process_type2",
        "_post_process_and_route_type2",
        "handle_chat_general",
    }

    missing = [name for name in sorted(expected) if not functions_with_log.get(name)]
    assert not missing, f"Missing @log decorator for functions: {', '.join(missing)}"


def test_chat_general_service_avoids_manual_logger_calls():
    tree = ast.parse(
        Path("src/rag_stream/src/services/chat_general_service.py").read_text(
            encoding="utf-8"
        )
    )

    logger_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "logger":
                logger_calls.append(node.attr)

    assert not logger_calls, (
        "chat_general_service should avoid manual logger calls, "
        f"but found: {', '.join(sorted(set(logger_calls)))}"
    )


def test_process_query_chain_methods_have_log_decorator():
    base_methods_with_log = _class_methods_with_log(
        "src/rag_stream/src/services/intent_service/base_intent_service.py",
        "BaseIntentService",
    )
    intent_methods_with_log = _class_methods_with_log(
        "src/rag_stream/src/services/intent_service/intent_service.py",
        "IntentService",
    )

    expected_intent = {
        "process_query",
        "_load_process_settings",
        "_query_process_table_results",
        "_sort_process_table_results",
        "_get_process_judge_function",
        "_post_process_result",
    }

    base_should_not_log = {
        "__init__",
        "process_query",
        "_load_intent_recognizer_settings",
        "_query_table_results",
        "_sort_table_results",
        "_intent_judgment",
    }
    unexpected_base = [
        name for name in sorted(base_should_not_log) if base_methods_with_log.get(name)
    ]
    missing_intent = [
        name for name in sorted(expected_intent) if not intent_methods_with_log.get(name)
    ]

    assert not unexpected_base, (
        "BaseIntentService should not use @log decorators, but found on methods: "
        f"{', '.join(unexpected_base)}"
    )
    assert not missing_intent, f"Missing @log decorator for IntentService methods: {', '.join(missing_intent)}"


def test_intent_service_avoids_manual_logger_calls():
    tree = ast.parse(
        Path("src/rag_stream/src/services/intent_service/intent_service.py").read_text(
            encoding="utf-8"
        )
    )

    logger_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "logger":
                logger_calls.append(node.attr)

    assert not logger_calls, (
        "intent_service.py should avoid manual logger calls, "
        f"but found: {', '.join(sorted(set(logger_calls)))}"
    )
