from __future__ import annotations

import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径
# session_manager.py 在: project_root/src/rag_stream/src/utils/
# 需要向上5级到达项目根目录
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
src_root = os.path.join(project_root, "src")
if src_root not in sys.path:
    sys.path.insert(0, src_root)

try:
    from log_manager import trace, marker
except ImportError:
    # 测试环境降级: 使用空的装饰器
    def trace(func):
        return func

    def marker(name: str, data: dict = None, level: str = "INFO"):
        pass


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, Dict[str, str]] = {}
        self.session_expires: Dict[str, datetime] = {}

    @trace
    def create_session(
        self, chat_id: str, session_name: str, user_id: Optional[str] = None, category: str = ""
    ) -> str:
        session_id = str(uuid.uuid4())
        expire_time = datetime.now() + timedelta(hours=24)  # 默认24小时过期

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

        marker("会话创建成功", {"session_id": session_id, "category": category, "has_user_id": bool(user_id)})

        return session_id

    @trace
    def get_user_session(self, user_id: str, category: str) -> Optional[str]:
        if user_id in self.user_sessions and category in self.user_sessions[user_id]:
            session_id = self.user_sessions[user_id][category]
            if session_id in self.session_expires and self.session_expires[session_id] > datetime.now():
                marker("会话命中", {"user_id": user_id, "category": category, "session_id": session_id})
                return session_id
            marker("会话过期清理触发", {"user_id": user_id, "category": category, "session_id": session_id})
            self.cleanup_expired_session(session_id)
        else:
            marker("会话未命中", {"user_id": user_id, "category": category})
        return None

    @trace
    def update_session_activity(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
            self.sessions[session_id]["message_count"] += 1
            self.session_expires[session_id] = datetime.now() + timedelta(hours=24)  # 默认24小时过期
            marker("会话活跃度更新", {"session_id": session_id, "message_count": self.sessions[session_id]['message_count']})
        else:
            marker("会话活跃度更新失败", {"session_id": session_id}, level="WARNING")

    @trace
    def cleanup_expired_session(self, session_id: str):
        if session_id in self.sessions:
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

            marker("会话清理完成", {"session_id": session_id, "user_id": user_id, "category": category})
        else:
            marker("跳过会话清理", {"session_id": session_id})

    @trace
    def cleanup_all_expired_sessions(self):
        expired_sessions = []
        for session_id, expire_time in self.session_expires.items():
            if expire_time <= datetime.now():
                expired_sessions.append(session_id)

        marker("会话批量清理扫描", {"expired_count": len(expired_sessions)})
        for session_id in expired_sessions:
            self.cleanup_expired_session(session_id)

    @trace
    def get_user_sessions_info(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.user_sessions:
            marker("用户会话查询为空", {"user_id": user_id})
            return {}

        user_sessions_info = {}
        for category, session_id in self.user_sessions[user_id].items():
            if session_id in self.sessions:
                user_sessions_info[category] = {
                    "session_id": session_id,
                    "name": self.sessions[session_id]["name"],
                    "create_time": self.sessions[session_id]["create_time"],
                    "last_activity": self.sessions[session_id]["last_activity"],
                    "message_count": self.sessions[session_id]["message_count"],
                }

        marker("用户会话查询完成", {"user_id": user_id, "session_count": len(user_sessions_info)})
        return user_sessions_info

    @trace
    def cleanup_user_sessions(self, user_id: str) -> int:
        """删除指定用户的所有会话,返回删除的会话数量"""
        if user_id not in self.user_sessions:
            return 0

        session_ids = list(self.user_sessions[user_id].values())
        count = 0
        for session_id in session_ids:
            if session_id in self.sessions:
                self.cleanup_expired_session(session_id)
                count += 1

        marker("用户会话批量清理完成", {"user_id": user_id, "cleaned_count": count})

        return count


session_manager = SessionManager()
