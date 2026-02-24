"""日志装饰器模块。"""

import functools
import inspect
import logging as py_logging
import os
import traceback
import threading
import time
from typing import Any, Callable, List, Optional

from .config import load_config
from .mermaid import MermaidRecorder, get_current_recorder, set_current_recorder
from .parser import parse_obj, render_log_value, sanitize_sensitive_data
from .tree_manager import tree_manager

# 加载配置
_config = load_config()

# 获取项目根目录
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PROJECT_ROOT)

# 日志目录
_LOG_DIR = os.path.join(_PROJECT_ROOT, _config["log_dir"])


class AlignedMultilineFormatter(py_logging.Formatter):
    """多行日志格式化器：续行按消息起始列对齐。"""

    def format(self, record):
        formatted = super().format(record)
        if "\n" not in formatted:
            return formatted

        lines = formatted.splitlines()
        first_line = lines[0]

        message_text = record.getMessage()
        message_first_line = message_text.splitlines()[0] if message_text else ""

        align_index = first_line.find(message_first_line) if message_first_line else -1
        if align_index < 0:
            return formatted

        indent = " " * align_index
        aligned_rest = [f"{indent}{line}" for line in lines[1:]]
        return "\n".join([first_line, *aligned_rest])


def _build_formatter() -> AlignedMultilineFormatter:
    return AlignedMultilineFormatter(_config["format"], datefmt=_config["time_format"])


# 初始化全局日志
logger = py_logging.getLogger("custom_logger")
logger.setLevel(getattr(py_logging, _config["level"]))
logger.handlers.clear()

# 全局日志处理器
global_log_file = os.path.join(_LOG_DIR, _config["global_log_file"])
global_handler = py_logging.FileHandler(global_log_file, encoding=_config["encoding"])
global_handler.setFormatter(_build_formatter())
logger.addHandler(global_handler)

# 控制台处理器
if _config["console_enabled"]:
    console_handler = py_logging.StreamHandler()
    console_handler.setFormatter(_build_formatter())
    logger.addHandler(console_handler)

_entry_local = threading.local()

_FUNCTION_ICON_MAP = {"log": "🔵", "entry": "🟢", "end": "🟣"}
_ARGS_SECTION_ICON = "🧩"
_RETURNS_SECTION_ICON = "🧪"
_WARNING_ICON = "⚠"
_ERROR_ICON = "✖"


def _get_current_entry() -> Optional[str]:
    return getattr(_entry_local, "current_entry", None)


def _set_current_entry(entry_func: Optional[str]) -> None:
    _entry_local.current_entry = entry_func


def _load_icon_theme() -> None:
    """从配置加载图标主题。"""
    global _FUNCTION_ICON_MAP, _ARGS_SECTION_ICON, _RETURNS_SECTION_ICON

    default_function_icons = {"log": "🔵", "entry": "🟢", "end": "🟣"}
    default_section_icons = {"args": "🧩", "returns": "🧪"}

    themes = _config.get("icon_themes")
    if not isinstance(themes, dict):
        themes = {}

    selected_theme = str(_config.get("icon_theme", "default"))
    theme = themes.get(selected_theme)
    if not isinstance(theme, dict):
        theme = themes.get("default") if isinstance(themes.get("default"), dict) else {}

    function_icons = theme.get("function") if isinstance(theme.get("function"), dict) else {}
    section_icons = theme.get("section") if isinstance(theme.get("section"), dict) else {}

    _FUNCTION_ICON_MAP = {
        "log": str(function_icons.get("log", default_function_icons["log"])),
        "entry": str(function_icons.get("entry", default_function_icons["entry"])),
        "end": str(function_icons.get("end", default_function_icons["end"])),
    }
    _ARGS_SECTION_ICON = str(section_icons.get("args", default_section_icons["args"]))
    _RETURNS_SECTION_ICON = str(section_icons.get("returns", default_section_icons["returns"]))


def _extract_error_location(error: Exception) -> str:
    """提取异常最后一帧代码位置。"""
    traceback_items = traceback.extract_tb(error.__traceback__)
    if not traceback_items:
        return "unknown"

    last_frame = traceback_items[-1]
    return f"{last_frame.filename}:{last_frame.lineno} in {last_frame.name}"


def _get_function_icon(decorator_kind: str) -> str:
    return _FUNCTION_ICON_MAP.get(decorator_kind, _FUNCTION_ICON_MAP["log"])


def _warn_text(message: str) -> str:
    return f"{_WARNING_ICON} {message}"


_load_icon_theme()


def _get_error_log_file() -> str:
    """获取错误日志文件路径。"""
    return os.path.join(_LOG_DIR, "error.log")


def _build_exception_chain(exc: Exception) -> List[str]:
    """构建异常链文本列表。"""
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
    """写入错误上下文到 error.log。"""
    os.makedirs(_LOG_DIR, exist_ok=True)

    timestamp = time.strftime(_config["time_format"], time.localtime())
    sanitized_args = sanitize_sensitive_data(parse_obj(args, compact=False))
    sanitized_kwargs = sanitize_sensitive_data(parse_obj(kwargs, compact=False))
    error_location = _extract_error_location(error)

    lines = [
        f"[{timestamp}] 入口函数: {entry_func}",
        f"错误摘要: {type(error).__name__}: {error}",
        f"错误位置: {error_location}",
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


def _resolve_log_level(log_level: Optional[Any]) -> int:
    """解析日志级别。"""
    if log_level is None:
        return getattr(py_logging, _config["level"])

    if callable(log_level):
        try:
            log_level = log_level()
        except Exception as e:
            logger.warning(_warn_text(f"日志级别lambda执行失败: {e}，使用全局级别"))
            return getattr(py_logging, _config["level"])

    if isinstance(log_level, str):
        level_upper = log_level.upper()
        if hasattr(py_logging, level_upper):
            return getattr(py_logging, level_upper)
        logger.warning(_warn_text(f"无效的日志级别: {log_level}，使用全局级别"))
        return getattr(py_logging, _config["level"])

    logger.warning(_warn_text(f"不支持的日志级别类型: {type(log_level)}，使用全局级别"))
    return getattr(py_logging, _config["level"])


def _build_named_arguments(func: Callable, args: tuple, kwargs: dict) -> dict:
    """根据函数签名构建参数名 -> 参数值映射。"""
    try:
        signature = inspect.signature(func)
        bound = signature.bind_partial(*args, **kwargs)
    except Exception:
        fallback: dict[str, Any] = {}
        for index, value in enumerate(args):
            fallback[f"args[{index}]"] = value
        fallback.update(kwargs)
        return fallback

    named_args: dict[str, Any] = {}
    for name, value in bound.arguments.items():
        if name in {"self", "cls"}:
            continue
        named_args[name] = value
    return named_args


def _normalize_items(data: Any, default_key: str = "value") -> list[tuple[str, Any]]:
    """将任意数据转为树状输出的键值列表。"""
    if isinstance(data, dict):
        return [(str(key), render_log_value(value)) for key, value in data.items()]
    return [(default_key, render_log_value(data))]


def _truncate_log_text(value: Any, max_len: int) -> str:
    """按最大字符长度截断日志文本。"""
    text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}... [已截断]"


def _emit_section(
    *,
    level: int,
    cont_prefix: str,
    label: str,
    items: list[tuple[str, Any]],
    is_last_section: bool,
) -> None:
    """输出一个树状分组（如 args / returns）。"""
    section_branch = "└─" if is_last_section else "├─"
    logger.log(level, f"{cont_prefix}{section_branch} {label}")

    child_prefix = f"{cont_prefix}{'   ' if is_last_section else '│  '}"
    if not items:
        logger.log(level, f"{child_prefix}└─ (empty)")
        return

    for index, (key, value) in enumerate(items):
        branch = "└─" if index == len(items) - 1 else "├─"
        logger.log(level, f"{child_prefix}{branch} {key}: {value}")


def _runtime_log(level_name: str, message: Any) -> None:
    """在函数执行中追加日志并维持树状结构。"""
    level = py_logging.DEBUG if level_name == "DEBUF" else getattr(py_logging, level_name)

    text = str(message)
    depth = tree_manager.depth()

    if depth == 0:
        logger.warning(_warn_text("运行日志警告: 当前不在 @log 函数上下文，按根节点记录"))
        logger.log(level, f"运行日志: {text}")
        return

    cont_prefix = tree_manager.get_continuation_prefix(depth)
    logger.log(level, f"{cont_prefix}├─ 运行日志: {text}")


def _complete_entry(
    *,
    entry_name: str,
    entry_handler: Optional[py_logging.Handler],
    mermaid_recorder: Optional[MermaidRecorder],
    enable_mermaid: bool,
    force_mermaid: bool,
    effective_level: int,
    has_error: bool,
    last_error: Optional[Exception],
    args: tuple,
    kwargs: dict,
) -> None:
    mermaid_file_path = None

    if entry_handler is not None:
        logger.removeHandler(entry_handler)
        entry_handler.close()

    if enable_mermaid and mermaid_recorder:
        should_save = False
        if force_mermaid:
            should_save = True
        elif effective_level == py_logging.DEBUG:
            should_save = True
        elif has_error:
            should_save = True

        if should_save:
            mermaid_file_path = mermaid_recorder.save_to_file()

    if has_error and last_error is not None:
        _write_error_context(
            entry_func=entry_name,
            call_chain=tree_manager.get_trace().copy(),
            args=args,
            kwargs=kwargs,
            error=last_error,
            mermaid_path=mermaid_file_path,
        )

    set_current_recorder(None)
    _set_current_entry(None)
    tree_manager.clear_trace()


def _write_non_entry_error_context(args: tuple, kwargs: dict, error: Exception) -> None:
    """为非入口函数异常写入 error.log。"""
    current_entry = _get_current_entry() or "<non-entry>"
    call_chain = tree_manager.get_trace().copy()
    if not call_chain:
        call_chain = [current_entry]

    _write_error_context(
        entry_func=current_entry,
        call_chain=call_chain,
        args=args,
        kwargs=kwargs,
        error=error,
        mermaid_path=None,
    )


def _reset_current_branch() -> None:
    tree_manager.reset_trace_from_stack()


def _build_entry_log_path(func: Callable) -> str:
    """构建入口日志路径：logs/entries/{module_file}.{func}.log。"""
    entry_dir = os.path.join(_LOG_DIR, _config.get("entry_log_dir", "entries"))
    os.makedirs(entry_dir, exist_ok=True)

    module_file = "unknown"
    module = inspect.getmodule(func)
    module_path = getattr(module, "__file__", None)
    if module_path:
        module_file = os.path.splitext(os.path.basename(module_path))[0]

    entry_filename = f"{module_file}.{func.__name__}.log"
    return os.path.join(entry_dir, entry_filename)


class RuntimeLogging:
    """供业务侧使用的运行时日志接口。"""

    @staticmethod
    def DEBUF(message: Any) -> None:
        _runtime_log("DEBUF", message)

    @staticmethod
    def INFO(message: Any) -> None:
        _runtime_log("INFO", message)

    @staticmethod
    def WARNING(message: Any) -> None:
        _runtime_log("WARNING", message)

    @staticmethod
    def ERROR(message: Any) -> None:
        _runtime_log("ERROR", message)


def log(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None,
    decorator_kind: str = "log",
) -> Callable:
    """日志装饰器。"""

    def decorator(func: Callable) -> Callable:
        def _prepare_call(args: tuple, kwargs: dict) -> dict:
            effective_level = _resolve_log_level(log_level)
            original_level = logger.level

            if isinstance(original_level, int) and effective_level < original_level:
                logger.setLevel(effective_level)

            try:
                depth = tree_manager.push(func.__name__)
                prefix = tree_manager.get_tree_prefix(depth)
                cont_prefix = tree_manager.get_continuation_prefix(depth)
                start_time = time.time()

                entry_handler = None
                mermaid_recorder = None

                function_icon = _get_function_icon(decorator_kind)
                header_text = f"{prefix}{function_icon} {func.__name__}"
                if message:
                    header_text = f"{header_text} · {message}"
                logger.log(effective_level, header_text)

                node_id = None
                current_recorder = get_current_recorder()
                if current_recorder:
                    node_id = current_recorder.add_node(func.__name__, "success")

                if print_args:
                    if args_handler is not None:
                        try:
                            custom_args = args_handler(args, kwargs)
                            args_items = _normalize_items(custom_args)
                        except Exception as handler_error:
                            logger.warning(
                                f"{cont_prefix}├─ {_warn_text('自定义输入处理异常')}: "
                                f"{type(handler_error).__name__}: {str(handler_error)}"
                            )
                            named_args = _build_named_arguments(func, args, kwargs)
                            args_items = [
                                (
                                    name,
                                    _truncate_log_text(
                                        render_log_value(value),
                                        _config.get("args_max_len", 100),
                                    ),
                                )
                                for name, value in named_args.items()
                            ]
                    else:
                        named_args = _build_named_arguments(func, args, kwargs)
                        args_items = [
                            (
                                name,
                                _truncate_log_text(
                                    render_log_value(value),
                                    _config.get("args_max_len", 100),
                                ),
                            )
                            for name, value in named_args.items()
                        ]

                    _emit_section(
                        level=effective_level,
                        cont_prefix=cont_prefix,
                        label=f"{_ARGS_SECTION_ICON} [ args ]",
                        items=args_items,
                        is_last_section=False,
                    )

                return {
                    "effective_level": effective_level,
                    "original_level": original_level,
                    "cont_prefix": cont_prefix,
                    "start_time": start_time,
                    "entry_handler": entry_handler,
                    "mermaid_recorder": mermaid_recorder,
                    "has_error": False,
                    "last_error": None,
                    "node_id": node_id,
                }
            except Exception:
                if isinstance(original_level, int):
                    logger.setLevel(original_level)
                raise

        def _handle_success(state: dict, result: Any) -> None:
            custom_output = None
            if result_handler is not None:
                try:
                    custom_output = result_handler(result)
                except Exception as handler_error:
                    logger.warning(
                        f"{state['cont_prefix']}├─ {_warn_text('自定义输出异常')}: "
                        f"{type(handler_error).__name__}: {str(handler_error)}"
                    )

            if print_result:
                result_items = [
                    (
                        "result",
                        _truncate_log_text(
                            render_log_value(result),
                            _config.get("result_max_len", 100),
                        ),
                    )
                ]
                if custom_output is not None:
                    result_items.append(("custom", render_log_value(custom_output)))

                _emit_section(
                    level=state["effective_level"],
                    cont_prefix=state["cont_prefix"],
                    label=f"{_RETURNS_SECTION_ICON} [ returns ]",
                    items=result_items,
                    is_last_section=not print_duration,
                )
            elif custom_output is not None:
                branch = "└─" if not print_duration else "├─"
                logger.log(
                    state["effective_level"],
                    f"{state['cont_prefix']}{branch} custom: {render_log_value(custom_output)}",
                )

        def _handle_exception(state: dict, error: Exception) -> None:
            state["has_error"] = True
            state["last_error"] = error

            exception_branch = "└─" if not print_duration else "├─"
            logger.error(
                f"{state['cont_prefix']}{exception_branch} {_ERROR_ICON} 异常: "
                f"{type(error).__name__}: {str(error)}"
            )

            if state["node_id"]:
                current_recorder = get_current_recorder()
                if current_recorder:
                    current_recorder.mark_error(state["node_id"])

        def _finalize_call(state: dict, args: tuple, kwargs: dict) -> None:
            if print_duration:
                duration = round((time.time() - state["start_time"]) * 1000, 2)
                logger.log(
                    state["effective_level"],
                    f"{state['cont_prefix']}└─ 耗时: {duration}ms",
                )

            tree_manager.pop()

            current_recorder = get_current_recorder()
            if current_recorder:
                current_recorder.pop_parent()

            entry_handler = state["entry_handler"]
            if entry_handler is not None:
                logger.removeHandler(entry_handler)
                entry_handler.close()

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
                is_entry_root = decorator_kind == "entry" and _get_current_entry() == func.__name__
                if not is_entry_root:
                    _write_non_entry_error_context(args, kwargs, e)
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
                is_entry_root = decorator_kind == "entry" and _get_current_entry() == func.__name__
                if not is_entry_root:
                    _write_non_entry_error_context(args, kwargs, e)
                raise
            finally:
                _finalize_call(state, args, kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def log_entry(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None,
) -> Callable:
    """入口日志装饰器。"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            activated_entry = False
            entry_handler = None
            mermaid_recorder = None

            if _get_current_entry() is None:
                activated_entry = True
                _set_current_entry(func.__name__)
                tree_manager.start_trace()

                log_file = _build_entry_log_path(func)
                entry_handler = py_logging.FileHandler(log_file, encoding=_config["encoding"])
                entry_handler.setFormatter(_build_formatter())
                logger.addHandler(entry_handler)

                if enable_mermaid:
                    mermaid_dir = os.path.join(_LOG_DIR, _config.get("mermaid_dir", "mermaid"))
                    mermaid_max_size = _config.get("mermaid_max_size_mb", 10)
                    mermaid_recorder = MermaidRecorder(func.__name__, mermaid_dir, mermaid_max_size)
                    set_current_recorder(mermaid_recorder)

            core_decorator = log(
                print_args=print_args,
                print_result=print_result,
                print_duration=print_duration,
                message=message,
                args_handler=args_handler,
                result_handler=result_handler,
                enable_mermaid=enable_mermaid,
                force_mermaid=force_mermaid,
                log_level=log_level,
                decorator_kind="entry",
            )
            wrapped = core_decorator(func)

            has_error = False
            last_error = None

            try:
                return wrapped(*args, **kwargs)
            except Exception as error:
                has_error = True
                last_error = error
                raise
            finally:
                if activated_entry:
                    effective_level = _resolve_log_level(log_level)
                    _complete_entry(
                        entry_name=func.__name__,
                        entry_handler=entry_handler,
                        mermaid_recorder=mermaid_recorder,
                        enable_mermaid=enable_mermaid,
                        force_mermaid=force_mermaid,
                        effective_level=effective_level,
                        has_error=has_error,
                        last_error=last_error,
                        args=args,
                        kwargs=kwargs,
                    )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            activated_entry = False
            entry_handler = None
            mermaid_recorder = None

            if _get_current_entry() is None:
                activated_entry = True
                _set_current_entry(func.__name__)
                tree_manager.start_trace()

                log_file = _build_entry_log_path(func)
                entry_handler = py_logging.FileHandler(log_file, encoding=_config["encoding"])
                entry_handler.setFormatter(_build_formatter())
                logger.addHandler(entry_handler)

                if enable_mermaid:
                    mermaid_dir = os.path.join(_LOG_DIR, _config.get("mermaid_dir", "mermaid"))
                    mermaid_max_size = _config.get("mermaid_max_size_mb", 10)
                    mermaid_recorder = MermaidRecorder(func.__name__, mermaid_dir, mermaid_max_size)
                    set_current_recorder(mermaid_recorder)

            core_decorator = log(
                print_args=print_args,
                print_result=print_result,
                print_duration=print_duration,
                message=message,
                args_handler=args_handler,
                result_handler=result_handler,
                enable_mermaid=enable_mermaid,
                force_mermaid=force_mermaid,
                log_level=log_level,
                decorator_kind="entry",
            )
            wrapped = core_decorator(func)

            has_error = False
            last_error = None

            try:
                return await wrapped(*args, **kwargs)
            except Exception as error:
                has_error = True
                last_error = error
                raise
            finally:
                if activated_entry:
                    effective_level = _resolve_log_level(log_level)
                    _complete_entry(
                        entry_name=func.__name__,
                        entry_handler=entry_handler,
                        mermaid_recorder=mermaid_recorder,
                        enable_mermaid=enable_mermaid,
                        force_mermaid=force_mermaid,
                        effective_level=effective_level,
                        has_error=has_error,
                        last_error=last_error,
                        args=args,
                        kwargs=kwargs,
                    )

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def log_end(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None,
) -> Callable:
    """结束当前分支并清理局部调用状态。"""

    base_decorator = log(
        print_args=print_args,
        print_result=print_result,
        print_duration=print_duration,
        message=message,
        args_handler=args_handler,
        result_handler=result_handler,
        enable_mermaid=enable_mermaid,
        force_mermaid=force_mermaid,
        log_level=log_level,
        decorator_kind="end",
    )

    def decorator(func: Callable) -> Callable:
        wrapped = base_decorator(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return wrapped(*args, **kwargs)
            finally:
                if _get_current_entry() is not None:
                    _reset_current_branch()

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await wrapped(*args, **kwargs)
            finally:
                if _get_current_entry() is not None:
                    _reset_current_branch()

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


logging = RuntimeLogging()

# 向后兼容：历史上对外暴露 _call_stack
_call_stack = tree_manager

__all__ = ["log", "log_entry", "log_end", "parse_obj", "logger", "logging", "_call_stack"]
