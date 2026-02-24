from __future__ import annotations

import os
from typing import Optional


_psutil_error: Optional[Exception] = None
try:
    import psutil  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency path
    psutil = None
    _psutil_error = exc


def get_rss_kb() -> int:
    if psutil is not None:
        return int(psutil.Process(os.getpid()).memory_info().rss / 1024)

    statm_path = "/proc/self/statm"
    if os.path.exists(statm_path):
        with open(statm_path, "r", encoding="utf-8") as fp:
            parts = fp.read().strip().split()
        if len(parts) >= 2:
            pages = int(parts[1])
            page_size = os.sysconf("SC_PAGE_SIZE")
            return int((pages * page_size) / 1024)
    return 0
