from __future__ import annotations

import os
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def short_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass(slots=True, frozen=True)
class EntryScope:
    entry_id: str
    name: str
    trace_id: str
    parent_entry_id: str | None


@dataclass(slots=True, frozen=True)
class SpanScope:
    span_id: str
    parent_span_id: str | None
    trace_id: str
    class_name: str
    func_name: str
    entry_id: str | None
    started_ns: int
    mem_enter_rss_kb: int | None


_entry_stack: ContextVar[tuple[EntryScope, ...]] = ContextVar("entry_stack", default=())
_span_stack: ContextVar[tuple[SpanScope, ...]] = ContextVar("span_stack", default=())


class RuntimeContext:
    def __init__(self, session_id: str | None = None) -> None:
        self._session_id = session_id
        self._run_id = f"run_pid{os.getpid()}_{uuid.uuid4().hex[:6]}"

    @property
    def session_id(self) -> str:
        if self._session_id is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._session_id = f"sess_{ts}_{uuid.uuid4().hex[:6]}"
        return self._session_id

    @property
    def run_id(self) -> str:
        return self._run_id

    def new_trace_id(self) -> str:
        return short_id("tr")

    def new_span_id(self) -> str:
        return short_id("sp")

    def new_entry_id(self) -> str:
        return short_id("entry")

    def push_entry(self, name: str) -> EntryScope:
        stack = _entry_stack.get()
        entry = EntryScope(
            entry_id=self.new_entry_id(),
            name=name,
            trace_id=self.new_trace_id(),
            parent_entry_id=stack[-1].entry_id if stack else None,
        )
        _entry_stack.set((*stack, entry))
        return entry

    def pop_entry(self) -> EntryScope | None:
        stack = _entry_stack.get()
        if not stack:
            return None
        _entry_stack.set(stack[:-1])
        return stack[-1]

    def current_entry(self) -> EntryScope | None:
        stack = _entry_stack.get()
        return stack[-1] if stack else None

    def push_span(
        self,
        trace_id: str,
        class_name: str,
        func_name: str,
        entry_id: str | None,
        mem_enter_rss_kb: int | None,
    ) -> SpanScope:
        stack = _span_stack.get()
        span = SpanScope(
            span_id=self.new_span_id(),
            parent_span_id=stack[-1].span_id if stack else None,
            trace_id=trace_id,
            class_name=class_name,
            func_name=func_name,
            entry_id=entry_id,
            started_ns=time.monotonic_ns(),
            mem_enter_rss_kb=mem_enter_rss_kb,
        )
        _span_stack.set((*stack, span))
        return span

    def pop_span(self) -> SpanScope | None:
        stack = _span_stack.get()
        if not stack:
            return None
        _span_stack.set(stack[:-1])
        return stack[-1]

    def current_span(self) -> SpanScope | None:
        stack = _span_stack.get()
        return stack[-1] if stack else None

    def reset(self) -> None:
        _entry_stack.set(())
        _span_stack.set(())
