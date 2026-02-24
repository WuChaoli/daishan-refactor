"""测试 @log_entry / @log_end 新装饰器行为。"""

import io
import logging as py_logging
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from log_decorator import log, logger, log_end, log_entry


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


def test_log_should_reject_is_entry_parameter():
    with pytest.raises(TypeError):
        log(is_entry=True)


def test_log_entry_should_create_entry_log_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        import log_decorator.decorator as decorator_module

        original_log_dir = decorator_module._LOG_DIR
        decorator_module._LOG_DIR = tmpdir

        try:
            @log_entry(print_duration=False)
            def entry_func(value):
                return value

            assert entry_func("ok") == "ok"

            entry_log = os.path.join(tmpdir, "entries", "test_log_entry_end_decorators.entry_func.log")
            assert os.path.exists(entry_log)
            with open(entry_log, "r", encoding="utf-8") as file:
                content = file.read()
            assert "entry_func" in content
        finally:
            decorator_module._LOG_DIR = original_log_dir


def test_nested_log_entry_should_not_override_outer_entry_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        import log_decorator.decorator as decorator_module

        original_log_dir = decorator_module._LOG_DIR
        decorator_module._LOG_DIR = tmpdir

        try:
            @log_entry(print_duration=False)
            def inner_func():
                return "inner"

            @log_entry(print_duration=False)
            def outer_func():
                return inner_func()

            assert outer_func() == "inner"

            assert os.path.exists(
                os.path.join(tmpdir, "entries", "test_log_entry_end_decorators.outer_func.log")
            )
            assert not os.path.exists(
                os.path.join(tmpdir, "entries", "test_log_entry_end_decorators.inner_func.log")
            )
        finally:
            decorator_module._LOG_DIR = original_log_dir


def test_log_entry_should_write_into_entries_directory_with_module_prefix():
    with tempfile.TemporaryDirectory() as tmpdir:
        import log_decorator.decorator as decorator_module

        original_log_dir = decorator_module._LOG_DIR
        decorator_module._LOG_DIR = tmpdir

        try:
            @log_entry(print_duration=False)
            def named_entry():
                return "ok"

            assert named_entry() == "ok"

            expected_path = os.path.join(
                tmpdir,
                "entries",
                "test_log_entry_end_decorators.named_entry.log",
            )
            assert os.path.exists(expected_path)
            assert not os.path.exists(os.path.join(tmpdir, "named_entry.log"))
        finally:
            decorator_module._LOG_DIR = original_log_dir


def test_log_end_should_work_independently():
    @log_end(print_duration=False)
    def cleanup():
        return "done"

    with capture_logger_output() as stream:
        assert cleanup() == "done"

    content = stream.getvalue()
    assert "🟣 cleanup" in content


def test_log_entry_should_render_entry_function_icon():
    @log_entry(print_duration=False)
    def entry_icon_func():
        return "ok"

    with capture_logger_output() as stream:
        assert entry_icon_func() == "ok"

    content = stream.getvalue()
    assert "🟢 entry_icon_func" in content


def test_should_load_icons_from_minimal_theme_config():
    import log_decorator.decorator as decorator_module

    original_config = decorator_module._config.copy()
    original_function_icons = decorator_module._FUNCTION_ICON_MAP.copy()
    original_args_icon = decorator_module._ARGS_SECTION_ICON
    original_returns_icon = decorator_module._RETURNS_SECTION_ICON

    try:
        decorator_module._config["icon_theme"] = "minimal"
        decorator_module._config["icon_themes"] = {
            "minimal": {
                "function": {"log": "◽", "entry": "◻", "end": "◼"},
                "section": {"args": "▫", "returns": "▪"},
            }
        }
        decorator_module._load_icon_theme()

        @log(print_duration=False)
        def themed_func():
            return "ok"

        with capture_logger_output() as stream:
            themed_func()

        content = stream.getvalue()
        assert "◽ themed_func" in content
        assert "▫ [ args ]" in content
        assert "▪ [ returns ]" in content
    finally:
        decorator_module._config.clear()
        decorator_module._config.update(original_config)
        decorator_module._FUNCTION_ICON_MAP = original_function_icons
        decorator_module._ARGS_SECTION_ICON = original_args_icon
        decorator_module._RETURNS_SECTION_ICON = original_returns_icon
        decorator_module._load_icon_theme()


def test_log_end_should_cut_current_branch_and_start_new_downstream_trace():
    with tempfile.TemporaryDirectory() as tmpdir:
        import log_decorator.decorator as decorator_module

        original_log_dir = decorator_module._LOG_DIR
        decorator_module._LOG_DIR = tmpdir

        try:
            @log(print_duration=False)
            def before_step():
                return "before"

            @log_end(print_duration=False)
            def finish_branch():
                return "finish"

            @log(print_duration=False)
            def raise_after_end():
                raise ValueError("boom")

            @log_entry(print_duration=False)
            def entry_flow():
                before_step()
                finish_branch()
                raise_after_end()

            with pytest.raises(ValueError):
                entry_flow()

            error_log = os.path.join(tmpdir, "error.log")
            assert os.path.exists(error_log)
            with open(error_log, "r", encoding="utf-8") as file:
                content = file.read()

            assert "raise_after_end" in content
            assert "before_step" not in content
        finally:
            decorator_module._LOG_DIR = original_log_dir
