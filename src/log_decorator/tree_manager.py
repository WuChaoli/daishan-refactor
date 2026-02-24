"""树状日志管理器。"""

from __future__ import annotations

import threading
from typing import List, Optional


class TreeLogManager:
    """负责树状前缀与结构化多行内容渲染。"""

    def __init__(self):
        self._local = threading.local()

    @property
    def call_stack(self):
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def push(self, func_name: str) -> int:
        self.call_stack.append(func_name)
        if hasattr(self._local, "trace"):
            self._local.trace.append(func_name)
        return len(self.call_stack) - 1

    def pop(self) -> Optional[str]:
        if not self.call_stack:
            return None
        return self.call_stack.pop()

    def depth(self) -> int:
        return len(self.call_stack)

    def start_trace(self):
        self._local.trace = []

    def get_trace(self) -> List[str]:
        if not hasattr(self._local, "trace"):
            return []
        return self._local.trace

    def clear_trace(self):
        if hasattr(self._local, "trace"):
            del self._local.trace

    def reset_trace_from_stack(self):
        self._local.trace = self.call_stack.copy()

    def clear_stack(self):
        if hasattr(self._local, "stack"):
            self._local.stack.clear()

    def get_tree_prefix(self, depth: int, is_last: bool = False) -> str:
        if depth == 0:
            return ""
        prefix_parts = ["│  " for _ in range(depth - 1)]
        prefix_parts.append("└─ " if is_last else "├─ ")
        return "".join(prefix_parts)

    def get_continuation_prefix(self, depth: int) -> str:
        if depth == 0:
            return ""
        return "│  " * depth

    def format_section(self, title: str, pairs: list[tuple[str, object]], cont_prefix: str) -> str:
        lines = [f"{cont_prefix}{title}"]
        for key, value in pairs:
            lines.append(f"{cont_prefix}│  - {key}: {value}")
        return "\n".join(lines)


tree_manager = TreeLogManager()
