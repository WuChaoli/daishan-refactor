from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Iterable


class EventStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._lock = threading.Lock()

    def session_run_dir(self, session_id: str) -> Path:
        return self.base_dir / "runs" / session_id

    def session_report_dir(self, session_id: str) -> Path:
        return self.base_dir / "reports" / session_id

    def entry_events_path(self, session_id: str, entry_id: str) -> Path:
        return self.session_run_dir(session_id) / "entries" / f"{entry_id}.events.jsonl"

    def global_events_path(self, session_id: str) -> Path:
        return self.session_run_dir(session_id) / "global.events.jsonl"

    def append_event(self, session_id: str, event: dict, entry_id: str | None) -> Path:
        target = self.entry_events_path(session_id, entry_id) if entry_id else self.global_events_path(session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with open(target, "a", encoding="utf-8") as fp:
                fp.write(payload + "\n")
        return target

    def iter_entry_event_files(self, session_id: str) -> Iterable[Path]:
        root = self.session_run_dir(session_id) / "entries"
        if not root.exists():
            return []
        return sorted(root.glob("*.events.jsonl"))
