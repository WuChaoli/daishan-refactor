from __future__ import annotations

from typing import Any

import yaml

from log_manager import entry_trace, trace


def _iter_call_chain_nodes(node: dict[str, Any]):
    yield node
    for child in node.get("children", []):
        yield from _iter_call_chain_nodes(child)


def test_report_is_yaml_and_contains_call_chain(runtime_factory):
    runtime = runtime_factory()

    @trace
    def child():
        raise RuntimeError("inventory timeout")

    @entry_trace("create-order")
    def parent():
        child()

    try:
        parent()
    except RuntimeError:
        pass

    runtime.flush_reports(reason="test")
    session = runtime.context.session_id
    entry_reports_root = runtime.storage.session_report_dir(session) / "entries"
    report_files = list(entry_reports_root.glob("*/latest.txt"))
    assert report_files
    text = report_files[0].read_text(encoding="utf-8")
    report = yaml.safe_load(text)

    assert {"metadata", "error_summary", "call_chain", "error_path", "chain_memory_top"}.issubset(report)
    assert report["metadata"]["session_id"] == session
    assert report["metadata"]["event_count"] > 0

    call_chain = report["call_chain"]
    assert call_chain
    nodes = []
    for trace_group in call_chain:
        for root in trace_group.get("roots", []):
            nodes.extend(list(_iter_call_chain_nodes(root)))
    assert nodes
    names = {node["function_name"] for node in nodes}
    assert "parent" in names
    assert "child" in names
    assert all("duration_ms" in node for node in nodes)
    assert all("exception" in node for node in nodes)
    assert any(node["exception"] and node["exception"]["type"] == "RuntimeError" for node in nodes)

    assert report["error_path"]["exception"]["type"] == "RuntimeError"
    assert "【函数调用链】" not in text
    assert "【错误路径链】" not in text


def test_report_exception_field_is_null_when_no_error(runtime_factory):
    runtime = runtime_factory()

    @trace
    def child():
        return "ok"

    @entry_trace("create-order")
    def parent():
        return child()

    assert parent() == "ok"
    runtime.flush_reports(reason="test")
    session = runtime.context.session_id
    entry_reports_root = runtime.storage.session_report_dir(session) / "entries"
    report_files = list(entry_reports_root.glob("*/latest.txt"))
    assert report_files
    report = yaml.safe_load(report_files[0].read_text(encoding="utf-8"))

    nodes = []
    for trace_group in report["call_chain"]:
        for root in trace_group.get("roots", []):
            nodes.extend(list(_iter_call_chain_nodes(root)))
    assert nodes
    assert all(node["exception"] is None for node in nodes)
    assert report["error_path"] is None


def test_global_summary_is_file_first(runtime_factory):
    runtime = runtime_factory()

    @entry_trace("entry")
    def ok():
        return 1

    ok()
    runtime.flush_reports(reason="test")
    session = runtime.context.session_id
    latest = runtime.storage.session_report_dir(session) / "global-error-summary" / "latest.txt"
    assert latest.exists()
