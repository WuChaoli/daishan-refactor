from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class MemoryConfig:
    process_enabled: bool = True
    span_enabled: bool = True
    sampling_interval_ms: int = 1000


@dataclass(slots=True)
class ReportConfig:
    chain_memory_enabled: bool = True
    retention: int = 20
    language: str = "zh"
    trigger_timer_s: int = 60
    trigger_event_count: int = 5000
    trigger_idle_s: int = 10
    immediate_on_error: bool = True


@dataclass(slots=True)
class ConsoleConfig:
    show_memory_delta: bool = True
    enable_output: bool = True


@dataclass(slots=True)
class LogManagerConfig:
    mode: str = "lite"
    base_dir: Path = Path(".log-manager")
    session_id: str | None = None
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    console: ConsoleConfig = field(default_factory=ConsoleConfig)
    parameter_whitelist: Sequence[str] = field(default_factory=tuple)
    enable_background_threads: bool = True

    def apply_mode_defaults(self) -> None:
        if self.mode == "enhanced":
            self.memory.sampling_interval_ms = min(self.memory.sampling_interval_ms, 200)
        elif self.mode == "lite":
            self.memory.sampling_interval_ms = max(self.memory.sampling_interval_ms, 1000)
        else:
            raise ValueError("mode must be either 'lite' or 'enhanced'")
