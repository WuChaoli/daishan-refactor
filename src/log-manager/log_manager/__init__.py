from __future__ import annotations

from .config import LogManagerConfig
from .decorators import entry_trace, trace
from .runtime import configure, get_runtime


def marker(name: str, kv: dict | None = None, *, level: str = "INFO", message: str | None = None) -> None:
    runtime = get_runtime()
    runtime.emit_marker(name=name, kv=kv, level=level, message=message)


__all__ = [
    "LogManagerConfig",
    "configure",
    "entry_trace",
    "marker",
    "trace",
]
