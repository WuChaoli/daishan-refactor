from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pytest

from log_manager import LogManagerConfig, configure


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as fp:
        for line in fp:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


@pytest.fixture
def runtime_factory(tmp_path: Path):
    runtimes = []

    def _factory(
        *,
        threads: bool = False,
        mode: str = "lite",
        sampling_interval_ms: int | None = None,
        trigger_timer_s: int | None = None,
        trigger_event_count: int | None = None,
        trigger_idle_s: int | None = None,
    ):
        cfg = LogManagerConfig(mode=mode, base_dir=tmp_path / ".log-manager", enable_background_threads=threads)
        cfg.parameter_whitelist = ("value", "order_id", "sku")
        if sampling_interval_ms is not None:
            cfg.memory.sampling_interval_ms = sampling_interval_ms
        if trigger_timer_s is not None:
            cfg.report.trigger_timer_s = trigger_timer_s
        if trigger_event_count is not None:
            cfg.report.trigger_event_count = trigger_event_count
        if trigger_idle_s is not None:
            cfg.report.trigger_idle_s = trigger_idle_s
        runtime = configure(cfg)
        runtimes.append(runtime)
        return runtime

    yield _factory

    for runtime in runtimes:
        runtime.shutdown()


@pytest.fixture
def read_jsonl():
    return _read_jsonl
