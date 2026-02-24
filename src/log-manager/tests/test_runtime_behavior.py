from __future__ import annotations

import time

from log_manager import entry_trace, marker, trace
from log_manager.console import format_terminal_line


def test_event_threshold_trigger_generates_report(runtime_factory):
    runtime = runtime_factory(trigger_event_count=3)

    @entry_trace("threshold-entry")
    def work():
        marker("checkpoint", {"value": 1})

    work()
    session = runtime.context.session_id
    latest = runtime.storage.session_report_dir(session) / "entries"
    # threshold should have triggered automatically
    assert list(latest.glob("*/latest.txt"))


def test_timer_or_idle_trigger_generates_report(runtime_factory):
    runtime = runtime_factory(threads=True, trigger_event_count=1000, trigger_timer_s=1, trigger_idle_s=1)

    @trace
    def ping():
        return True

    ping()
    time.sleep(1.6)
    session = runtime.context.session_id
    latest = runtime.storage.session_report_dir(session) / "global-error-summary" / "latest.txt"
    assert latest.exists()


def test_memory_events_and_span_deltas(runtime_factory, read_jsonl):
    runtime = runtime_factory(threads=True, sampling_interval_ms=100)

    @trace
    def allocate():
        payload = [i for i in range(1000)]
        return len(payload)

    allocate()
    time.sleep(0.3)
    session = runtime.context.session_id
    events = read_jsonl(runtime.storage.global_events_path(session))
    assert any(ev.get("event") == "process_mem" and "rss_kb" in ev for ev in events)
    assert any(ev.get("event") == "call_exit" and "mem_delta_rss_kb" in ev for ev in events)


def test_terminal_format_contract():
    line = format_terminal_line("INFO", "OrderService.create_order", "开始执行：创建订单")
    assert line.startswith("[")
    assert "] [INFO " in line
    assert "[OrderService.create_order]" in line
