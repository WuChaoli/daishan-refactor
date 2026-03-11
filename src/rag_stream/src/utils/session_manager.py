from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, Dict[str, str]] = {}
        self.session_expires: Dict[str, datetime] = {}

    def create_session(
        self,
        chat_id: str,
        session_name: str,
        user_id: Optional[str] = None,
        category: str = "",
    ) -> str:
        session_id = str(uuid.uuid4())
        expire_time = datetime.now() + timedelta(hours=24)

        session_info = {
            "id": session_id,
            "chat_id": chat_id,
            "name": session_name,
            "user_id": user_id,
            "category": category,
            "create_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
        }

        self.sessions[session_id] = session_info
        self.session_expires[session_id] = expire_time

        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id][category] = session_id

        return session_id

    def get_user_session(self, user_id: str, category: str) -> Optional[str]:
        if user_id in self.user_sessions and category in self.user_sessions[user_id]:
            session_id = self.user_sessions[user_id][category]
            if (
                session_id in self.session_expires
                and self.session_expires[session_id] > datetime.now()
            ):
                return session_id
            self.cleanup_expired_session(session_id)
        return None

    def update_session_activity(self, session_id: str) -> None:
        if session_id not in self.sessions:
            return
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
        self.sessions[session_id]["message_count"] += 1
        self.session_expires[session_id] = datetime.now() + timedelta(hours=24)

    def cleanup_expired_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            return

        user_id = self.sessions[session_id].get("user_id")
        category = self.sessions[session_id].get("category")

        if user_id and category and user_id in self.user_sessions:
            if category in self.user_sessions[user_id]:
                del self.user_sessions[user_id][category]
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

        del self.sessions[session_id]
        if session_id in self.session_expires:
            del self.session_expires[session_id]

    def cleanup_all_expired_sessions(self) -> None:
        expired_sessions: list[str] = []
        for session_id, expire_time in self.session_expires.items():
            if expire_time <= datetime.now():
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            self.cleanup_expired_session(session_id)

    def get_user_sessions_info(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.user_sessions:
            return {}

        user_sessions_info: Dict[str, Any] = {}
        for category, session_id in self.user_sessions[user_id].items():
            if session_id in self.sessions:
                user_sessions_info[category] = {
                    "session_id": session_id,
                    "name": self.sessions[session_id]["name"],
                    "create_time": self.sessions[session_id]["create_time"],
                    "last_activity": self.sessions[session_id]["last_activity"],
                    "message_count": self.sessions[session_id]["message_count"],
                }
        return user_sessions_info

    def cleanup_user_sessions(self, user_id: str) -> int:
        if user_id not in self.user_sessions:
            return 0

        session_ids = list(self.user_sessions[user_id].values())
        count = 0
        for session_id in session_ids:
            if session_id in self.sessions:
                self.cleanup_expired_session(session_id)
                count += 1

        return count


session_manager = SessionManager()
