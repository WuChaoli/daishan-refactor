from __future__ import annotations

from pathlib import Path

from log_manager import entry_trace, marker, trace


def test_nested_entry_routes_to_innermost(runtime_factory, read_jsonl):
    runtime = runtime_factory()

    @trace
    def inner_leaf():
        marker("inner-point", {"value": 1})

    @entry_trace("inner-entry")
    def inner():
        inner_leaf()

    @entry_trace("outer-entry")
    def outer():
        inner()

    outer()
    runtime.flush_reports(reason="test")

    session = runtime.context.session_id
    run_root = runtime.storage.session_run_dir(session)
    entry_files = sorted((run_root / "entries").glob("*.events.jsonl"))
    assert len(entry_files) == 2

    files_by_presence = {path: read_jsonl(path) for path in entry_files}
    inner_file = next(
        path for path, events in files_by_presence.items()
        if any(ev.get("func_name") == "inner_leaf" and ev.get("event") == "call_enter" for ev in events)
    )
    outer_file = next(path for path in entry_files if path != inner_file)

    assert any(ev.get("func_name") == "inner_leaf" and ev.get("event") == "call_enter" for ev in files_by_presence[inner_file])
    assert not any(ev.get("func_name") == "inner_leaf" and ev.get("event") == "call_enter" for ev in files_by_presence[outer_file])


def test_trace_without_entry_uses_global_stream(runtime_factory, read_jsonl):
    runtime = runtime_factory()

    @trace
    def load_config():
        return True

    load_config()
    session = runtime.context.session_id
    global_events = read_jsonl(runtime.storage.global_events_path(session))
    assert any(ev.get("func_name") == "load_config" and ev.get("event") == "call_enter" for ev in global_events)
    entries_dir = runtime.storage.session_run_dir(session) / "entries"
    if entries_dir.exists():
        assert list(entries_dir.glob("*.events.jsonl")) == []
