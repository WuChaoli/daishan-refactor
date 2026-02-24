from __future__ import annotations

from log_manager import entry_trace, trace


def test_report_contains_call_chain_and_error_path(runtime_factory):
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
    assert "【函数调用链】" in text
    assert "【错误路径链】" in text
    assert "parent" in text
    assert "child" in text


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
