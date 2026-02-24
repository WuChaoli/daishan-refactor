"""测试错误日志增强功能（阶段4）"""
import sys
import os
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_decorator.decorator import log, log_entry


class TestErrorEnhancement:
    """测试错误上下文、error.log和Mermaid链接"""

    def test_error_log_contains_context_chain_and_sanitized_args(self):
        """错误日志包含调用链路和脱敏后的入参"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import log_decorator.decorator as decorator_module

            original_log_dir = decorator_module._LOG_DIR
            decorator_module._LOG_DIR = tmpdir

            try:
                @log()
                def level2(payload):
                    raise ValueError("boom")

                @log_entry()
                def level1(payload):
                    return level2(payload)

                payload = {
                    "api_key": "ragflow-very-secret-key",
                    "password": "super-secret-password",
                    "nested": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
                }

                with pytest.raises(ValueError):
                    level1(payload)

                error_log = os.path.join(tmpdir, "error.log")
                assert os.path.exists(error_log)

                with open(error_log, "r", encoding="utf-8") as f:
                    content = f.read()

                assert "调用链路" in content
                assert "level1 -> level2" in content

                assert "ragflow-***" in content
                assert "super-secret-password" not in content
                assert "eyJhbG...VCJ9" in content

            finally:
                decorator_module._LOG_DIR = original_log_dir

    def test_error_log_supports_exception_chain(self):
        """错误日志支持 __cause__ / __context__ 异常链"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import log_decorator.decorator as decorator_module

            original_log_dir = decorator_module._LOG_DIR
            decorator_module._LOG_DIR = tmpdir

            try:
                @log_entry()
                def raise_with_cause():
                    try:
                        raise RuntimeError("inner-error")
                    except RuntimeError as e:
                        raise ValueError("outer-error") from e

                with pytest.raises(ValueError):
                    raise_with_cause()

                error_log = os.path.join(tmpdir, "error.log")
                with open(error_log, "r", encoding="utf-8") as f:
                    content = f.read()

                assert "异常链" in content
                assert "ValueError: outer-error" in content
                assert "__cause__" in content
                assert "RuntimeError: inner-error" in content

            finally:
                decorator_module._LOG_DIR = original_log_dir

    def test_error_log_contains_mermaid_file_link(self):
        """错误日志包含Mermaid文件链接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import log_decorator.decorator as decorator_module

            original_log_dir = decorator_module._LOG_DIR
            decorator_module._LOG_DIR = tmpdir

            try:
                @log_entry(enable_mermaid=True)
                def raise_error():
                    raise KeyError("missing")

                with pytest.raises(KeyError):
                    raise_error()

                error_log = os.path.join(tmpdir, "error.log")
                with open(error_log, "r", encoding="utf-8") as f:
                    content = f.read()

                assert "Mermaid文件" in content
                assert ".md" in content

            finally:
                decorator_module._LOG_DIR = original_log_dir

    def test_non_entry_exception_should_write_error_summary_and_location(self):
        """非入口异常也应写入 error.log，包含摘要与代码位置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import log_decorator.decorator as decorator_module

            original_log_dir = decorator_module._LOG_DIR
            decorator_module._LOG_DIR = tmpdir

            try:
                @log()
                def only_log_error(payload):
                    raise RuntimeError(f"bad-{payload}")

                with pytest.raises(RuntimeError):
                    only_log_error("data")

                error_log = os.path.join(tmpdir, "error.log")
                assert os.path.exists(error_log)

                with open(error_log, "r", encoding="utf-8") as f:
                    content = f.read()

                assert "错误摘要: RuntimeError: bad-data" in content
                assert "错误位置:" in content
                assert "only_log_error" in content
            finally:
                decorator_module._LOG_DIR = original_log_dir
