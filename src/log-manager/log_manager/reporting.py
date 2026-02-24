from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import LogManagerConfig
from .storage import EventStorage


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _func_name(class_name: str, func_name: str) -> str:
    if class_name:
        return f"{class_name}.{func_name}"
    return func_name


@dataclass
class SpanNode:
    span_id: str
    parent_span_id: str | None
    trace_id: str
    func: str
    duration_ms: float | None = None
    status: str = "unknown"
    error_type: str | None = None
    error_msg: str | None = None
    mem_delta_rss_kb: int | None = None
    children: list[str] = field(default_factory=list)


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fp:
        for line in fp:
            text = line.strip()
            if not text:
                continue
            try:
                events.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    return events


def _retain_reports(directory: Path, retention: int) -> None:
    reports = sorted(directory.glob("report-*.txt"))
    while len(reports) > retention:
        reports[0].unlink(missing_ok=True)
        reports.pop(0)


class ReportGenerator:
    def __init__(self, storage: EventStorage, config: LogManagerConfig) -> None:
        self.storage = storage
        self.config = config

    def generate(self, session_id: str) -> None:
        for entry_file in self.storage.iter_entry_event_files(session_id):
            self._generate_entry_report(session_id, entry_file)
        self._generate_global_summary(session_id)

    def _generate_entry_report(self, session_id: str, entry_file: Path) -> None:
        events = sorted(_load_events(entry_file), key=lambda x: x.get("ts_mono_ns", 0))
        if not events:
            return
        entry_id = entry_file.name.replace(".events.jsonl", "")

        traces: dict[str, dict[str, SpanNode]] = {}
        markers_by_trace: dict[str, list[str]] = {}
        errors: list[dict[str, Any]] = []
        mem_nodes: list[tuple[str, int]] = []

        for event in events:
            trace_id = event.get("trace_id") or "unknown"
            spans = traces.setdefault(trace_id, {})
            event_type = event.get("event")
            func = _func_name(event.get("class_name", ""), event.get("func_name", "unknown"))
            span_id = event.get("span_id")
            parent_span_id = event.get("parent_span_id")

            if event_type == "marker":
                marker = event.get("marker_name", "未命名关键点")
                markers_by_trace.setdefault(trace_id, []).append(marker)
                continue

            if event_type == "call_enter" and span_id:
                spans[span_id] = SpanNode(
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    trace_id=trace_id,
                    func=func,
                )

            if event_type == "call_exit" and span_id:
                node = spans.setdefault(
                    span_id,
                    SpanNode(span_id=span_id, parent_span_id=parent_span_id, trace_id=trace_id, func=func),
                )
                node.duration_ms = event.get("duration_ms")
                node.status = event.get("status", "unknown")
                delta = event.get("mem_delta_rss_kb")
                if isinstance(delta, int):
                    node.mem_delta_rss_kb = delta
                    mem_nodes.append((node.func, delta))

            if event_type == "error":
                errors.append(event)
                if span_id:
                    node = spans.setdefault(
                        span_id,
                        SpanNode(span_id=span_id, parent_span_id=parent_span_id, trace_id=trace_id, func=func),
                    )
                    node.error_type = event.get("error_type")
                    node.error_msg = event.get("error_msg")
                    node.status = "error"

        for trace_spans in traces.values():
            for span in trace_spans.values():
                if span.parent_span_id and span.parent_span_id in trace_spans:
                    trace_spans[span.parent_span_id].children.append(span.span_id)

        lines: list[str] = []
        lines.append("log-manager 增量报告")
        lines.append(f"会话ID: {session_id}")
        lines.append(f"入口ID: {entry_id}")
        lines.append(f"快照时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"分析窗口: 累计事件 {len(events)} 条")
        lines.append(f"模式: {self.config.mode}")
        lines.append("")

        lines.append("【错误摘要】")
        if not errors:
            lines.append("无错误。")
        else:
            for idx, err in enumerate(errors[:5], start=1):
                func = _func_name(err.get("class_name", ""), err.get("func_name", "unknown"))
                lines.append(
                    f"{idx}. {err.get('error_type', 'UnknownError')} - {func}: {err.get('error_msg', '')}".strip()
                )
        lines.append("")

        lines.append("【函数调用链】")
        for trace_id, trace_spans in traces.items():
            roots = [s for s in trace_spans.values() if not s.parent_span_id or s.parent_span_id not in trace_spans]
            if not roots:
                continue
            lines.append(f"Trace: {trace_id}")
            for root in roots:
                self._append_tree(lines, trace_spans, root, prefix="")
            lines.append("")

        lines.append("【错误路径链】")
        error_path_emitted = False
        for trace_id, trace_spans in traces.items():
            for node in trace_spans.values():
                if node.error_type:
                    path = self._error_path(trace_spans, node)
                    lines.append(" -> ".join(path))
                    lines.append(f"异常: {node.error_type}({node.error_msg or ''})")
                    markers = markers_by_trace.get(trace_id, [])
                    if markers:
                        lines.append(f"上下文: 最近关键点={markers[-1]}")
                    error_path_emitted = True
                    break
            if error_path_emitted:
                break
        if not error_path_emitted:
            lines.append("无错误路径。")
        lines.append("")

        lines.append("【调用链内存Top】")
        if self.config.report.chain_memory_enabled and mem_nodes:
            top = sorted(mem_nodes, key=lambda item: item[1], reverse=True)[:5]
            for idx, (func, delta) in enumerate(top, start=1):
                lines.append(f"{idx}. {func} 内存变化={delta:+}KB")
        else:
            lines.append("未启用或无数据。")

        report_dir = self.storage.session_report_dir(session_id) / "entries" / entry_id
        self._write_report(report_dir, lines)

    def _append_tree(self, lines: list[str], span_map: dict[str, SpanNode], node: SpanNode, prefix: str) -> None:
        status = node.status.upper()
        duration = f"{node.duration_ms:.1f}ms" if isinstance(node.duration_ms, (float, int)) else "N/A"
        mem = ""
        if self.config.report.chain_memory_enabled and isinstance(node.mem_delta_rss_kb, int):
            mem = f", 内存变化={node.mem_delta_rss_kb:+}KB"
        err = f", ERROR: {node.error_type}" if node.error_type else ""
        lines.append(f"{prefix}{node.func} [状态={status}, 耗时={duration}{mem}{err}]")
        for child_id in node.children:
            child = span_map[child_id]
            self._append_tree(lines, span_map, child, prefix + "  ")

    def _error_path(self, span_map: dict[str, SpanNode], error_node: SpanNode) -> list[str]:
        path = [error_node.func]
        current = error_node
        while current.parent_span_id and current.parent_span_id in span_map:
            current = span_map[current.parent_span_id]
            path.append(current.func)
        path.reverse()
        return path

    def _generate_global_summary(self, session_id: str) -> None:
        error_counts: dict[str, int] = {}
        mem_by_pid: dict[int, list[int]] = {}
        for entry_file in self.storage.iter_entry_event_files(session_id):
            for event in _load_events(entry_file):
                if event.get("event") == "error":
                    key = f"{event.get('error_type', 'UnknownError')}@{_func_name(event.get('class_name', ''), event.get('func_name', 'unknown'))}"
                    error_counts[key] = error_counts.get(key, 0) + 1
                if event.get("event") == "process_mem":
                    pid = int(event.get("pid", 0))
                    rss = int(event.get("rss_kb", 0))
                    mem_by_pid.setdefault(pid, []).append(rss)
        for event in _load_events(self.storage.global_events_path(session_id)):
            if event.get("event") == "error":
                key = f"{event.get('error_type', 'UnknownError')}@{_func_name(event.get('class_name', ''), event.get('func_name', 'unknown'))}"
                error_counts[key] = error_counts.get(key, 0) + 1
            if event.get("event") == "process_mem":
                pid = int(event.get("pid", 0))
                rss = int(event.get("rss_kb", 0))
                mem_by_pid.setdefault(pid, []).append(rss)

        lines: list[str] = []
        lines.append("log-manager 全局错误汇总")
        lines.append(f"会话ID: {session_id}")
        lines.append(f"快照时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("【错误聚合】")
        if not error_counts:
            lines.append("无错误。")
        else:
            for idx, (key, count) in enumerate(sorted(error_counts.items(), key=lambda item: item[1], reverse=True), start=1):
                lines.append(f"{idx}. {key} 次数={count}")
        lines.append("")
        lines.append("【进程内存概览】")
        if not mem_by_pid:
            lines.append("无内存采样数据。")
        else:
            for pid, samples in sorted(mem_by_pid.items()):
                lines.append(f"PID {pid}: 当前RSS={samples[-1]}KB 峰值RSS={max(samples)}KB 窗口变化={samples[-1]-samples[0]:+}KB")

        report_dir = self.storage.session_report_dir(session_id) / "global-error-summary"
        self._write_report(report_dir, lines)

    def _write_report(self, report_dir: Path, lines: list[str]) -> None:
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"report-{_now_stamp()}.txt"
        with open(report_file, "w", encoding="utf-8") as fp:
            fp.write("\n".join(lines).rstrip() + "\n")
        shutil.copyfile(report_file, report_dir / "latest.txt")
        _retain_reports(report_dir, self.config.report.retention)
