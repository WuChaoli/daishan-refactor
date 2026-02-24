from __future__ import annotations

from datetime import datetime, timezone


LEVEL_WIDTH = 5


def format_terminal_line(level: str, function_name: str, message: str, when: datetime | None = None) -> str:
    ts = when or datetime.now(timezone.utc)
    ts_text = ts.astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{ts_text}] [{level.upper():<{LEVEL_WIDTH}}] [{function_name}] {message}"
