from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.config.settings import settings
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionRequest,
    SessionResponse,
)
from src.services.dify_service import should_use_dify, stream_dify_chatflow_response
from src.services.rag_service import get_or_create_session, stream_chat_response
from src.utils.session_manager import session_manager

router = APIRouter()


@router.post("/api/chat/{category}", response_model=ChatResponse)
async def chat_with_category(
    category: str,
    request: ChatRequest,
):
    """通用聊天接口，根据类别选择对应的chat_id"""
    user_id = request.user_id or None
    if category not in settings.CHAT_IDS:
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    chat_id = settings.CHAT_IDS[category]

    session_id = await get_or_create_session(chat_id, category, user_id)

    return StreamingResponse(
        stream_chat_response(chat_id, request.question, session_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


async def chat_with_dify(request: ChatRequest):
    user_id = request.user_id or None
    return StreamingResponse(
        stream_dify_chatflow_response(
            query=request.question,
            session_id=user_id,
            user_id=user_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.post("/api/laws", response_model=ChatResponse)
async def chat_laws(request: ChatRequest):
    return await chat_with_category("法律法规", request)


@router.post("/api/standards", response_model=ChatResponse)
async def chat_standards(request: ChatRequest):
    return await chat_with_category("标准规范", request)


@router.post("/api/emergency", response_model=ChatResponse)
async def chat_emergency(request: ChatRequest):
    return await chat_with_category("应急知识", request)


@router.post("/api/accidents", response_model=ChatResponse)
async def chat_accidents(request: ChatRequest):
    return await chat_with_category("事故案例", request)


@router.post("/api/msds", response_model=ChatResponse)
async def chat_msds(request: ChatRequest):
    return await chat_with_category("MSDS", request)


@router.post("/api/policies", response_model=ChatResponse)
async def chat_policies(request: ChatRequest):
    return await chat_with_category("标准政策", request)


@router.post("/api/general", response_model=ChatResponse)
async def chat_general(request: ChatRequest):
    if should_use_dify(request.question):
        return await chat_with_dify(request)
    return await chat_with_category("通用", request)


@router.post("/api/warn", response_model=ChatResponse)
async def chat_warn(request: ChatRequest):
    return await chat_with_category("重大危险源预警", request)


@router.post("/api/safesituation", response_model=ChatResponse)
async def chat_safesituation(request: ChatRequest):
    return await chat_with_category("当日安全态势", request)


@router.post("/api/prevent", response_model=ChatResponse)
async def chat_prevent(request: ChatRequest):
    return await chat_with_category("双重预防机制效果", request)


@router.post("/api/park", response_model=ChatResponse)
async def chat_park(request: ChatRequest):
    return await chat_with_category("园区开停车", request)


@router.post("/api/special", response_model=ChatResponse)
async def chat_special(request: ChatRequest):
    return await chat_with_category("园区特殊作业态势", request)


@router.post("/api/firmsituation", response_model=ChatResponse)
async def chat_firmsituation(request: ChatRequest):
    return await chat_with_category("园区企业态势", request)


@router.post("/api/sessions/{category}", response_model=SessionResponse)
async def create_category_session(category: str, request: SessionRequest):
    if category not in settings.CHAT_IDS:
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    chat_id = settings.CHAT_IDS[category]
    session_id = await get_or_create_session(chat_id, category, request.user_id)

    return SessionResponse(
        code=0,
        message="会话创建成功",
        data={
            "session_id": session_id,
            "category": category,
            "name": request.name,
            "user_id": request.user_id,
        },
    )


@router.get("/api/user/{user_id}/sessions")
async def get_user_sessions(user_id: str) -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    user_sessions = session_manager.get_user_sessions_info(user_id)

    return {
        "code": 0,
        "message": "获取成功",
        "data": {"user_id": user_id, "sessions": user_sessions},
    }


@router.get("/api/sessions/{session_id}")
async def get_session_info(session_id: str) -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"code": 0, "message": "获取成功", "data": session_manager.sessions[session_id]}


@router.get("/api/sessions")
async def get_all_sessions() -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    return {
        "code": 0,
        "message": "获取成功",
        "data": list(session_manager.sessions.values()),
    }


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    session_manager.cleanup_expired_session(session_id)
    return {"code": 0, "message": "会话删除成功", "data": None}


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(session_manager.sessions),
        "active_users": len(session_manager.user_sessions),
    }


@router.get("/api/categories")
async def get_categories() -> Dict[str, Any]:
    return {
        "code": 0,
        "message": "获取成功",
        "data": {"categories": list(settings.CHAT_IDS.keys()), "chat_ids": settings.CHAT_IDS},
    }
