"""DaiShanSQL terminal log text helpers."""

from __future__ import annotations

import json
from typing import Any


DEFAULT_MAX_LOG_LENGTH = 120


def format_daishan_log_text(content: Any, max_length: int = DEFAULT_MAX_LOG_LENGTH) -> str:
    """Format content as a single-line preview for terminal logging."""
    if isinstance(content, str):
        text = content
    else:
        try:
            text = json.dumps(content, ensure_ascii=False, default=str)
        except Exception:
            text = repr(content)

    single_line = " ".join(text.split())
    if max_length <= 3:
        return single_line[:max_length]
    if len(single_line) > max_length:
        return f"{single_line[:max_length - 3]}..."
    return single_line
