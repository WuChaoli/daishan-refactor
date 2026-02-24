"""log_decorator 新需求测试。"""

import io
import logging as py_logging
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from log_decorator import log, logger, logging
import log_decorator.decorator as decorator_module


@contextmanager
def capture_logger_output():
    """捕获 log_decorator 内部 logger 输出。"""
    stream = io.StringIO()
    handler = py_logging.StreamHandler(stream)
    handler.setFormatter(py_logging.Formatter("%(message)s"))
    original_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(py_logging.DEBUG)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
        handler.close()
        logger.setLevel(original_level)


class UserWithToJson:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def to_json(self):
        return {"user_id": self.user_id}


class UserWithoutToJson:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"UserWithoutToJson(name={self.name})"


def test_should_print_named_arguments_and_full_values():
    @log(print_duration=False)
    def process_data(count, payload, user, raw_user):
        return {"ok": True, "items": [1, 2, 3]}

    with capture_logger_output() as stream:
        process_data(
            3,
            {"channel": "web", "tags": ["a", "b"]},
            UserWithToJson(7),
            UserWithoutToJson("alice"),
        )

    content = stream.getvalue()
    assert "args[0]" not in content
    assert "🧩 [ args ]" in content
    assert "🧪 [ returns ]" in content
    assert "count: 3" in content
    assert "payload: {'channel': 'web', 'tags': ['a', 'b']}" in content
    assert "user: {'user_id': 7}" in content
    assert "raw_user: UserWithoutToJson(name=alice)" in content
    assert "result: {'ok': True, 'items': [1, 2, 3]}" in content


def test_should_print_function_header_only_once():
    @log(print_duration=False)
    def worker(value):
        logging.INFO("inside")
        return value

    with capture_logger_output() as stream:
        worker("ok")

    content = stream.getvalue()
    worker_lines = [line for line in content.splitlines() if "worker" in line]
    assert len(worker_lines) == 1
    assert worker_lines[0].endswith("🔵 worker")


def test_should_ignore_self_and_cls_in_method_arguments():
    class DemoService:
        @log(print_duration=False)
        def run(self, query):
            return query

    with capture_logger_output() as stream:
        DemoService().run("hello")

    content = stream.getvalue()
    assert "self:" not in content
    assert "query: hello" in content


def test_default_should_not_print_duration():
    @log()
    def add(x, y):
        return x + y

    with capture_logger_output() as stream:
        add(1, 2)

    content = stream.getvalue()
    assert "耗时" not in content


def test_should_log_exception_type_and_message_with_error_level():
    @log(print_duration=False)
    def broken_func():
        raise ValueError("invalid payload")

    with capture_logger_output() as stream:
        with pytest.raises(ValueError):
            broken_func()

    content = stream.getvalue()
    assert "✖ 异常: ValueError: invalid payload" in content


def test_runtime_logging_should_warn_outside_context_and_keep_tree_format():
    @log(print_duration=False)
    def worker():
        logging.INFO("inside-info")
        logging.DEBUF("inside-debug")
        return "ok"

    with capture_logger_output() as stream:
        logging.INFO("outside-info")
        worker()

    content = stream.getvalue()
    assert "⚠ 运行日志警告:" in content
    assert "outside-info" in content
    assert "inside-info" in content
    assert "inside-debug" in content
    assert "运行日志:" in content


def test_multiline_output_should_align_with_function_message_column():
    stream = io.StringIO()
    handler = py_logging.StreamHandler(stream)
    handler.setFormatter(decorator_module.AlignedMultilineFormatter("%(asctime)s - %(levelname)-7s - %(message)s"))

    original_handlers = logger.handlers[:]
    original_level = logger.level
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(py_logging.INFO)

    @log(print_duration=False)
    def add(x, y):
        return x + y

    try:
        add(1, 2)
    finally:
        logger.handlers.clear()
        for old_handler in original_handlers:
            logger.addHandler(old_handler)
        logger.setLevel(original_level)

    lines = [line for line in stream.getvalue().splitlines() if line]
    assert any(line.endswith("🔵 add") for line in lines)
    assert any("🧩 [ args ]" in line for line in lines)
    assert any("x: 1" in line for line in lines)
