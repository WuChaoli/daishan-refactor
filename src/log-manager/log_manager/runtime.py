from __future__ import annotations

import atexit
import os
import threading
import time
import traceback
import inspect
from typing import Any, Callable

from .config import LogManagerConfig
from .console import format_terminal_line
from .context import RuntimeContext, utc_now_iso
from .memory import get_rss_kb
from .reporting import ReportGenerator
from .storage import EventStorage


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        text = str(value)
        if len(text) > 200:
            return text[:197] + "..."
        return value
    text = repr(value)
    if len(text) > 200:
        return text[:197] + "..."
    return text


class Runtime:
    def __init__(self, config: LogManagerConfig | None = None) -> None:
        self.config = config or LogManagerConfig()
        self.config.apply_mode_defaults()
        self.context = RuntimeContext(session_id=self.config.session_id)
        self.storage = EventStorage(self.config.base_dir)
        self.reporter = ReportGenerator(self.storage, self.config)
        self._events_since_snapshot = 0
        self._last_event_ns = 0
        self._last_snapshot_ns = time.monotonic_ns()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._scheduler_thread: threading.Thread | None = None
        self._memory_thread: threading.Thread | None = None
        if self.config.enable_background_threads:
            self._start_threads()
        atexit.register(self.shutdown)

    def _start_threads(self) -> None:
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, name="log-manager-scheduler", daemon=True)
        self._scheduler_thread.start()
        if self.config.memory.process_enabled:
            self._memory_thread = threading.Thread(target=self._memory_loop, name="log-manager-memory", daemon=True)
            self._memory_thread.start()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=1.0)
        if self._memory_thread and self._memory_thread.is_alive():
            self._memory_thread.join(timeout=1.0)
        self.flush_reports(reason="shutdown")

    def function_identity(self, fn: Callable[..., Any]) -> tuple[str, str]:
        qualname = getattr(fn, "__qualname__", getattr(fn, "__name__", "unknown"))
        if ".<locals>." in qualname:
            return "", qualname.split(".<locals>.")[-1]
        parts = qualname.split(".")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        return "", parts[-1]

    def _resolve_marker_caller(self) -> tuple[str, str]:
        """Resolve the actual caller (class/function) of marker()."""
        frame = inspect.currentframe()
        # current -> _resolve_marker_caller -> emit_marker -> log_manager.marker -> user caller
        frame = frame.f_back if frame else None
        while frame:
            module_name = frame.f_globals.get("__name__", "")
            func_name = frame.f_code.co_name
            if not module_name.startswith("log_manager") and func_name != "marker":
                cls_name = ""
                self_obj = frame.f_locals.get("self")
                cls_obj = frame.f_locals.get("cls")
                if self_obj is not None:
                    cls_name = self_obj.__class__.__name__
                elif isinstance(cls_obj, type):
                    cls_name = cls_obj.__name__
                return cls_name, func_name
            frame = frame.f_back
        return "", "marker"

    def summarize_args(self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        whitelist = set(self.config.parameter_whitelist)
        if not whitelist:
            return {}
        try:
            bound = inspect.signature(fn).bind_partial(*args, **kwargs)
        except Exception:
            return {}
        result: dict[str, Any] = {}
        for key, value in bound.arguments.items():
            if key in whitelist:
                result[key] = _sanitize_value(value)
        return result

    def _base_event(
        self,
        *,
        level: str,
        event: str,
        class_name: str,
        func_name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        entry_id: str | None,
    ) -> dict[str, Any]:
        return {
            "v": 1,
            "ts_wall": utc_now_iso(),
            "ts_mono_ns": time.monotonic_ns(),
            "session_id": self.context.session_id,
            "run_id": self.context.run_id,
            "pid": os.getpid(),
            "tid": threading.get_ident(),
            "level": level.upper(),
            "event": event,
            "class_name": class_name,
            "func_name": func_name,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "entry_id": entry_id,
        }

    def emit_event(self, event: dict[str, Any], *, entry_id: str | None, console_message: str | None = None) -> None:
        self.storage.append_event(self.context.session_id, event, entry_id=entry_id)
        with self._lock:
            self._events_since_snapshot += 1
            self._last_event_ns = time.monotonic_ns()
        if console_message and self.config.console.enable_output:
            function_name = event.get("func_name", "unknown")
            class_name = event.get("class_name", "")
            if class_name:
                function_name = f"{class_name}.{function_name}"
            print(format_terminal_line(event["level"], function_name, console_message))
        self._maybe_trigger_on_event(event)

    def _maybe_trigger_on_event(self, event: dict[str, Any]) -> None:
        if event.get("event") == "error" and self.config.report.immediate_on_error:
            self.flush_reports(reason="error-trigger")
            return
        should_flush = False
        with self._lock:
            if self._events_since_snapshot >= self.config.report.trigger_event_count:
                should_flush = True
        if should_flush:
            self.flush_reports(reason="event-threshold")

    def flush_reports(self, reason: str = "manual") -> None:
        with self._lock:
            pending = self._events_since_snapshot
            if pending <= 0 and reason not in {"shutdown", "error-trigger"}:
                return
            self._events_since_snapshot = 0
            self._last_snapshot_ns = time.monotonic_ns()
        self.reporter.generate(self.context.session_id)

    def _scheduler_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(0.5)
            now_ns = time.monotonic_ns()
            with self._lock:
                has_pending = self._events_since_snapshot > 0
                since_snapshot_s = (now_ns - self._last_snapshot_ns) / 1_000_000_000
                since_event_s = (now_ns - self._last_event_ns) / 1_000_000_000 if self._last_event_ns else 0
            if not has_pending:
                continue
            if since_snapshot_s >= self.config.report.trigger_timer_s:
                self.flush_reports(reason="timer")
                continue
            if since_event_s >= self.config.report.trigger_idle_s:
                self.flush_reports(reason="idle")

    def _memory_loop(self) -> None:
        interval = max(0.1, self.config.memory.sampling_interval_ms / 1000)
        while not self._stop_event.is_set():
            time.sleep(interval)
            rss = get_rss_kb()
            event = self._base_event(
                level="DEBUG",
                event="process_mem",
                class_name="",
                func_name="",
                trace_id="",
                span_id="",
                parent_span_id=None,
                entry_id=None,
            )
            event["rss_kb"] = rss
            self.emit_event(event, entry_id=None, console_message=None)

    def emit_marker(self, name: str, kv: dict[str, Any] | None = None, level: str = "INFO", message: str | None = None) -> None:
        current_span = self.context.current_span()
        current_entry = self.context.current_entry()
        caller_class_name, caller_func_name = self._resolve_marker_caller()
        class_name = caller_class_name or (current_span.class_name if current_span else "")
        func_name = caller_func_name or (current_span.func_name if current_span else "marker")
        event = self._base_event(
            level=level,
            event="marker",
            class_name=class_name,
            func_name=func_name,
            trace_id=current_span.trace_id if current_span else (current_entry.trace_id if current_entry else self.context.new_trace_id()),
            span_id=current_span.span_id if current_span else "",
            parent_span_id=current_span.parent_span_id if current_span else None,
            entry_id=current_entry.entry_id if current_entry else None,
        )
        event["marker_name"] = name
        event["marker_kv"] = {k: _sanitize_value(v) for k, v in (kv or {}).items()}
        info = message or name
        if kv:
            detail = ", ".join(f"{k}={_sanitize_value(v)}" for k, v in kv.items())
            info = f"{info}, {detail}"
        self.emit_event(event, entry_id=current_entry.entry_id if current_entry else None, console_message=info)

    def _start_call(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        *,
        is_entry: bool,
        entry_name: str | None = None,
    ) -> tuple[dict[str, Any], Any, str, str, str | None, str]:
        class_name, func_name = self.function_identity(fn)
        entry_scope = self.context.current_entry()
        if is_entry:
            entry_scope = self.context.push_entry(entry_name or f"{class_name}.{func_name}".strip("."))
        current_span = self.context.current_span()
        trace_id = entry_scope.trace_id if is_entry else (
            current_span.trace_id if current_span else (entry_scope.trace_id if entry_scope else self.context.new_trace_id())
        )
        mem_enter = get_rss_kb() if self.config.memory.span_enabled else None
        span = self.context.push_span(
            trace_id=trace_id,
            class_name=class_name,
            func_name=func_name,
            entry_id=entry_scope.entry_id if entry_scope else None,
            mem_enter_rss_kb=mem_enter,
        )
        enter_event = self._base_event(
            level="INFO",
            event="call_enter",
            class_name=class_name,
            func_name=func_name,
            trace_id=trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            entry_id=span.entry_id,
        )
        enter_event["args_summary"] = self.summarize_args(fn, args, kwargs)
        enter_event["mem_enter_rss_kb"] = mem_enter
        self.emit_event(enter_event, entry_id=span.entry_id, console_message=None)
        return enter_event, span, class_name, func_name, span.entry_id, trace_id

    def _finish_call(self, *, span: Any, class_name: str, func_name: str, trace_id: str, is_entry: bool, had_error: bool) -> None:
        ended_ns = time.monotonic_ns()
        mem_exit = get_rss_kb() if self.config.memory.span_enabled else None
        delta = (mem_exit - span.mem_enter_rss_kb) if (mem_exit is not None and span.mem_enter_rss_kb is not None) else None
        status = "error" if had_error else "ok"
        exit_event = self._base_event(
            level="WARN" if status == "error" else "INFO",
            event="call_exit",
            class_name=class_name,
            func_name=func_name,
            trace_id=trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            entry_id=span.entry_id,
        )
        exit_event["status"] = status
        exit_event["duration_ms"] = round((ended_ns - span.started_ns) / 1_000_000, 3)
        exit_event["mem_exit_rss_kb"] = mem_exit
        exit_event["mem_delta_rss_kb"] = delta
        self.emit_event(
            exit_event,
            entry_id=span.entry_id,
            console_message=None,
        )
        self.context.pop_span()
        if is_entry:
            self.context.pop_entry()

    def _emit_error(self, *, span: Any, class_name: str, func_name: str, trace_id: str, exc: Exception) -> None:
        error_event = self._base_event(
            level="ERROR",
            event="error",
            class_name=class_name,
            func_name=func_name,
            trace_id=trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            entry_id=span.entry_id,
        )
        error_event["error_type"] = exc.__class__.__name__
        error_event["error_msg"] = str(exc)
        error_event["stack_top"] = traceback.format_exc(limit=3).strip()
        self.emit_event(error_event, entry_id=span.entry_id, console_message=f"错误：{exc.__class__.__name__}（{exc}）")

    def invoke(self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], *, is_entry: bool, entry_name: str | None = None) -> Any:
        _, span, class_name, func_name, _, trace_id = self._start_call(
            fn, args, kwargs, is_entry=is_entry, entry_name=entry_name
        )
        had_error = False
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            had_error = True
            self._emit_error(span=span, class_name=class_name, func_name=func_name, trace_id=trace_id, exc=exc)
            raise
        finally:
            self._finish_call(span=span, class_name=class_name, func_name=func_name, trace_id=trace_id, is_entry=is_entry, had_error=had_error)

    async def invoke_async(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        *,
        is_entry: bool,
        entry_name: str | None = None,
    ) -> Any:
        _, span, class_name, func_name, _, trace_id = self._start_call(
            fn, args, kwargs, is_entry=is_entry, entry_name=entry_name
        )
        had_error = False
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            had_error = True
            self._emit_error(span=span, class_name=class_name, func_name=func_name, trace_id=trace_id, exc=exc)
            raise
        finally:
            self._finish_call(span=span, class_name=class_name, func_name=func_name, trace_id=trace_id, is_entry=is_entry, had_error=had_error)


_runtime_lock = threading.Lock()
_runtime: Runtime | None = None


def get_runtime() -> Runtime:
    global _runtime
    with _runtime_lock:
        if _runtime is None:
            _runtime = Runtime()
        return _runtime


def configure(config: LogManagerConfig | None = None, **kwargs: Any) -> Runtime:
    global _runtime
    with _runtime_lock:
        if _runtime is not None:
            _runtime.shutdown()
        cfg = config or LogManagerConfig()
        for key, value in kwargs.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        _runtime = Runtime(cfg)
        return _runtime
