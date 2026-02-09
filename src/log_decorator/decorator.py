"""日志装饰器模块

提供统一的函数日志记录装饰器，支持：
- 自动记录入参、出参、耗时
- 智能解析复杂对象
- 双日志文件（全局+功能级）
- 配置化日志行为
- 嵌套缩进输出
- 自定义文本标记
- 自定义处理函数
- Mermaid执行路径图
"""
import logging
import time
import functools
import os
import threading
import inspect
from typing import Any, Callable, Optional, List

from .config import load_config
from .parser import parse_obj, format_args_multiline, format_result_multiline, sanitize_sensitive_data
from .mermaid import MermaidRecorder, get_current_recorder, set_current_recorder

# 加载配置
_config = load_config()

# 获取项目根目录
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PROJECT_ROOT)

# 日志目录
_LOG_DIR = os.path.join(_PROJECT_ROOT, _config["log_dir"])

# 初始化全局日志
logger = logging.getLogger("custom_logger")
logger.setLevel(getattr(logging, _config["level"]))
logger.handlers.clear()

# 全局日志处理器
global_log_file = os.path.join(_LOG_DIR, _config["global_log_file"])
global_handler = logging.FileHandler(global_log_file, encoding=_config["encoding"])
global_handler.setFormatter(
    logging.Formatter(_config["format"], datefmt=_config["time_format"])
)
logger.addHandler(global_handler)

# 控制台处理器
if _config["console_enabled"]:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(_config["format"], datefmt=_config["time_format"])
    )
    logger.addHandler(console_handler)

# 当前入口函数标记
_current_entry: Optional[str] = None


# 调用栈管理（线程安全）
class CallStack:
    """线程安全的调用栈管理"""

    def __init__(self):
        self._local = threading.local()

    @property
    def stack(self):
        """获取当前线程的调用栈"""
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def push(self, func_name: str) -> int:
        """入栈，返回当前深度"""
        self.stack.append(func_name)

        if hasattr(self._local, "trace"):
            self._local.trace.append(func_name)

        return len(self.stack) - 1

    def pop(self) -> Optional[str]:
        """出栈，返回函数名"""
        if self.stack:
            return self.stack.pop()
        return None

    def depth(self) -> int:
        """获取当前栈深度"""
        return len(self.stack)

    def clear(self):
        """清空当前线程栈"""
        if hasattr(self._local, "stack"):
            self._local.stack.clear()

    def start_trace(self):
        """开始记录调用轨迹"""
        self._local.trace = []

    def get_trace(self) -> List[str]:
        """获取调用轨迹"""
        if not hasattr(self._local, "trace"):
            return []
        return self._local.trace

    def clear_trace(self):
        """清理调用轨迹"""
        if hasattr(self._local, "trace"):
            del self._local.trace


# 全局调用栈实例
_call_stack = CallStack()


def _get_error_log_file() -> str:
    """获取错误日志文件路径"""
    return os.path.join(_LOG_DIR, "error.log")


def _build_exception_chain(exc: Exception) -> List[str]:
    """构建异常链文本列表"""
    chain_lines: List[str] = []

    if exc.__cause__ is not None:
        chain_lines.append(f"  - __cause__: {type(exc.__cause__).__name__}: {exc.__cause__}")

    if exc.__context__ is not None and exc.__context__ is not exc.__cause__:
        chain_lines.append(f"  - __context__: {type(exc.__context__).__name__}: {exc.__context__}")

    return chain_lines


def _write_error_context(
    entry_func: str,
    call_chain: List[str],
    args: tuple,
    kwargs: dict,
    error: Exception,
    mermaid_path: Optional[str] = None,
):
    """写入错误上下文到 error.log"""
    os.makedirs(_LOG_DIR, exist_ok=True)

    timestamp = time.strftime(_config["time_format"], time.localtime())
    sanitized_args = sanitize_sensitive_data(parse_obj(args, compact=False))
    sanitized_kwargs = sanitize_sensitive_data(parse_obj(kwargs, compact=False))

    lines = [
        f"[{timestamp}] 入口函数: {entry_func}",
        f"错误类型: {type(error).__name__}",
        f"错误信息: {error}",
        f"主异常: {type(error).__name__}: {error}",
        "调用链路:",
        f"  {' -> '.join(call_chain) if call_chain else entry_func}",
        "脱敏入参:",
        f"  args={sanitized_args}",
        f"  kwargs={sanitized_kwargs}",
    ]

    chain_lines = _build_exception_chain(error)
    if chain_lines:
        lines.append("异常链:")
        lines.extend(chain_lines)

    if mermaid_path:
        lines.append(f"Mermaid文件: {mermaid_path}")

    lines.append("-" * 80)

    with open(_get_error_log_file(), "a", encoding=_config["encoding"]) as error_file:
        error_file.write("\n".join(lines) + "\n")


def _get_tree_prefix(depth: int, is_last: bool = False) -> str:
    """根据深度生成树形结构前缀

    Args:
        depth: 当前深度
        is_last: 是否是最后一个子节点

    Returns:
        树形前缀字符串
    Examples:
        depth=0: ""
        depth=1: "├─ "
        depth=2: "│  ├─ "
        depth=3: "│  │  ├─ "
    """
    if depth == 0:
        return ""

    # 生成层级前缀
    prefix_parts = []
    for i in range(depth - 1):
        prefix_parts.append("│  ")

    # 添加当前层级的连接符
    if is_last:
        prefix_parts.append("└─ ")
    else:
        prefix_parts.append("├─ ")

    return "".join(prefix_parts)


def _get_continuation_prefix(depth: int) -> str:
    """生成续行前缀（用于入参、出参等多行日志）

    Args:
        depth: 当前深度

    Returns:
        续行前缀字符串
    Examples:
        depth=0: ""
        depth=1: "│  "
        depth=2: "│  │  "
    """
    if depth == 0:
        return ""

    return "│  " * depth


# 当前入口函数标记
_current_entry: Optional[str] = None


def _resolve_log_level(log_level: Optional[Any]) -> int:
    """解析日志级别

    Args:
        log_level: 日志级别，可以是字符串、lambda函数或None

    Returns:
        logging级别常量（如logging.INFO）
    """
    # 如果未指定，使用全局配置
    if log_level is None:
        return getattr(logging, _config["level"])

    # 如果是callable（lambda），调用获取级别
    if callable(log_level):
        try:
            log_level = log_level()
        except Exception as e:
            logger.warning(f"日志级别lambda执行失败: {e}，使用全局级别")
            return getattr(logging, _config["level"])

    # 验证级别字符串
    if isinstance(log_level, str):
        level_upper = log_level.upper()
        if hasattr(logging, level_upper):
            return getattr(logging, level_upper)
        else:
            logger.warning(f"无效的日志级别: {log_level}，使用全局级别")
            return getattr(logging, _config["level"])

    # 其他类型，使用全局级别
    logger.warning(f"不支持的日志级别类型: {type(log_level)}，使用全局级别")
    return getattr(logging, _config["level"])


def log(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = True,
    is_entry: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None
) -> Callable:
    """日志装饰器

    Args:
        print_args: 是否打印入参
        print_result: 是否打印出参
        print_duration: 是否打印耗时
        is_entry: 是否为入口函数（生成功能级日志）
        message: 自定义文本标记
        args_handler: 自定义入参处理函数，接收 (args, kwargs) 返回可序列化对象
        result_handler: 自定义结果处理函数
        enable_mermaid: 是否启用Mermaid图生成
        force_mermaid: 是否强制输出Mermaid（无论日志级别）
        log_level: 日志级别（字符串或lambda函数），如'DEBUG'、'INFO'等

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        def _prepare_call(args: tuple, kwargs: dict) -> dict:
            global _current_entry

            if is_entry and _current_entry is None:
                _call_stack.start_trace()

            effective_level = _resolve_log_level(log_level)
            original_level = logger.level

            if isinstance(original_level, int) and effective_level < original_level:
                logger.setLevel(effective_level)

            try:
                depth = _call_stack.push(func.__name__)
                prefix = _get_tree_prefix(depth)
                cont_prefix = _get_continuation_prefix(depth)
                start_time = time.time()

                entry_handler = None
                mermaid_recorder = None
                mermaid_file_path = None

                if is_entry and _current_entry is None:
                    _current_entry = func.__name__
                    log_file = os.path.join(_LOG_DIR, f"{func.__name__}.log")
                    entry_handler = logging.FileHandler(log_file, encoding=_config["encoding"])
                    entry_handler.setFormatter(
                        logging.Formatter(_config["format"], datefmt=_config["time_format"])
                    )
                    logger.addHandler(entry_handler)

                    if enable_mermaid:
                        mermaid_dir = os.path.join(_LOG_DIR, _config.get("mermaid_dir", "mermaid"))
                        mermaid_max_size = _config.get("mermaid_max_size_mb", 10)
                        mermaid_recorder = MermaidRecorder(func.__name__, mermaid_dir, mermaid_max_size)
                        set_current_recorder(mermaid_recorder)

                if message:
                    logger.log(effective_level, f"{prefix}{func.__name__} - 【{message}】开始执行")
                else:
                    logger.log(effective_level, f"{prefix}{func.__name__} - 【开始执行】")

                node_id = None
                current_recorder = get_current_recorder()
                if current_recorder:
                    node_id = current_recorder.add_node(func.__name__, "success")

                if print_args:
                    if args_handler is not None:
                        try:
                            custom_args = args_handler(args, kwargs)
                            logger.log(effective_level, f"{cont_prefix}{func.__name__} - 【入参】{custom_args}")
                        except Exception as handler_error:
                            logger.warning(f"{cont_prefix}{func.__name__} - 【自定义输入处理异常】{type(handler_error).__name__}: {str(handler_error)}")
                            multiline_args = format_args_multiline(args, kwargs)
                            logger.log(effective_level, f"{cont_prefix}{func.__name__} - {multiline_args}")
                    else:
                        multiline_args = format_args_multiline(args, kwargs)
                        logger.log(effective_level, f"{cont_prefix}{func.__name__} - {multiline_args}")

                return {
                    "effective_level": effective_level,
                    "original_level": original_level,
                    "cont_prefix": cont_prefix,
                    "start_time": start_time,
                    "entry_handler": entry_handler,
                    "mermaid_recorder": mermaid_recorder,
                    "mermaid_file_path": mermaid_file_path,
                    "has_error": False,
                    "last_error": None,
                    "node_id": node_id,
                }
            except Exception:
                if isinstance(original_level, int):
                    logger.setLevel(original_level)
                raise

        def _handle_success(state: dict, result: Any) -> None:
            if print_result:
                parsed_result = parse_obj(result)
                logger.log(state["effective_level"], f"{state['cont_prefix']}{func.__name__} - 【出参】{parsed_result}")

            if result_handler is not None:
                try:
                    custom_output = result_handler(result)
                    logger.log(state["effective_level"], f"{state['cont_prefix']}{func.__name__} - 【自定义输出】{custom_output}")
                except Exception as handler_error:
                    logger.warning(f"{state['cont_prefix']}{func.__name__} - 【自定义输出异常】{type(handler_error).__name__}: {str(handler_error)}")

        def _handle_exception(state: dict, error: Exception) -> None:
            state["has_error"] = True
            state["last_error"] = error

            logger.error(f"{state['cont_prefix']}{func.__name__} - 【异常】{type(error).__name__}: {str(error)}", exc_info=True)

            if state["node_id"]:
                current_recorder = get_current_recorder()
                if current_recorder:
                    current_recorder.mark_error(state["node_id"])

        def _finalize_call(state: dict, args: tuple, kwargs: dict) -> None:
            global _current_entry

            if print_duration:
                duration = round((time.time() - state["start_time"]) * 1000, 2)
                logger.log(state["effective_level"], f"{state['cont_prefix']}{func.__name__} - 【执行完成】耗时：{duration}ms")

            _call_stack.pop()

            current_recorder = get_current_recorder()
            if current_recorder:
                current_recorder.pop_parent()

            entry_handler = state["entry_handler"]
            mermaid_recorder = state["mermaid_recorder"]

            if is_entry and entry_handler is not None and _current_entry == func.__name__:
                logger.removeHandler(entry_handler)
                entry_handler.close()
                _current_entry = None

                if enable_mermaid and mermaid_recorder:
                    should_save = False
                    if force_mermaid:
                        should_save = True
                    elif state["effective_level"] == logging.DEBUG:
                        should_save = True
                    elif state["has_error"]:
                        should_save = True

                    if should_save:
                        state["mermaid_file_path"] = mermaid_recorder.save_to_file()

                    if state["has_error"] and state["last_error"] is not None:
                        _write_error_context(
                            entry_func=func.__name__,
                            call_chain=_call_stack.get_trace().copy(),
                            args=args,
                            kwargs=kwargs,
                            error=state["last_error"],
                            mermaid_path=state["mermaid_file_path"],
                        )

                    set_current_recorder(None)
                    _call_stack.clear_trace()

                elif state["has_error"] and state["last_error"] is not None:
                    _write_error_context(
                        entry_func=func.__name__,
                        call_chain=_call_stack.get_trace().copy(),
                        args=args,
                        kwargs=kwargs,
                        error=state["last_error"],
                        mermaid_path=None,
                    )
                    _call_stack.clear_trace()

                else:
                    _call_stack.clear_trace()

            original_level = state["original_level"]
            if isinstance(original_level, int):
                logger.setLevel(original_level)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            state = _prepare_call(args, kwargs)
            try:
                result = await func(*args, **kwargs)
                _handle_success(state, result)
                return result
            except Exception as e:
                _handle_exception(state, e)
                raise
            finally:
                _finalize_call(state, args, kwargs)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            state = _prepare_call(args, kwargs)
            try:
                result = func(*args, **kwargs)
                _handle_success(state, result)
                return result
            except Exception as e:
                _handle_exception(state, e)
                raise
            finally:
                _finalize_call(state, args, kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


# 导出
__all__ = ["log", "parse_obj", "logger", "_call_stack"]
