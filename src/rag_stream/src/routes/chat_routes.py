from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from rag_stream.utils.log_manager_import import entry_trace, marker

from rag_stream.config.settings import settings
from rag_stream.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatDeleteRequest,
    SessionRequest,
    SessionResponse,
    PeopleDispatchRequest,
    SourceDispatchRequest,
    GuessQuestionsRequest,
)
from rag_stream.services.dify_service import should_use_dify, stream_dify_chatflow_response
from rag_stream.services.chat_general_service import handle_chat_general
from rag_stream.services.personnel_dispatch_service import handle_personnel_dispatch
from rag_stream.services.rag_service import get_or_create_session, stream_chat_response
from rag_stream.services.source_dispath_srvice import handle_source_dispatch
from rag_stream.utils.session_manager import session_manager
router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


@router.post("/api/chat/{category}", response_model=ChatResponse)
@entry_trace("chat-category")
async def chat_with_category(
    category: str,
    request: ChatRequest,
):
    """通用聊天接口，根据类别选择对应的chat_id"""
    user_id = request.user_id or None
    marker("分类聊天请求", {"category": category, "has_user_id": bool(user_id), "question_len": len(request.question)})
    if category not in settings.ragflow.chat_ids:
        marker("分类聊天请求拒绝", {"unsupported_category": category}, level="WARNING")
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    chat_id = settings.ragflow.chat_ids[category]
    marker("chat_id获取", {"chat_id": chat_id})

    session_id = await get_or_create_session(chat_id, category, user_id)
    marker("会话就绪", {"category": category, "chat_id": chat_id, "session_id": session_id})

    marker("分类聊天流式响应启动", {"category": category, "session_id": session_id})

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
    marker("Dify流式会话开始", {"has_user_id": bool(user_id)})
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


async def dict_to_stream_generator(result_dict: dict):
    """
    将字典结果转换为 SSE 流式生成器

    Args:
        result_dict: 包含 type 和 data 的字典

    Yields:
        SSE 格式的事件字符串
    """
    import json
    import asyncio

    # 发送开始事件
    yield f"event: start\ndata: {json.dumps({'message': '开始流式输出'}, ensure_ascii=False)}\n\n"

    # 转换为 JSON 字符串并分块输出
    result_str = json.dumps(result_dict, ensure_ascii=False)
    chunk_size = 3
    message_id = 0
    for i in range(0, len(result_str), chunk_size):
        chunk = result_str[i : i + chunk_size]
        message_id += 1
        yield f"id: {message_id}\nevent: message\ndata: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)

    # 发送完成事件
    yield f"event: complete\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\n\n"

    # 发送结束事件
    yield f"event: end\ndata: [DONE]\n\n"


@router.post("/api/general", response_model=ChatResponse)
@entry_trace("chat-general")
async def chat_general(request: ChatRequest, http_request: Request):
    """
    通用问答接口 - 使用意图识别路由
    """
    intent_service = getattr(http_request.app.state, "intent_service", None)
    if intent_service is None:
        marker("通用问答路由失败", {"reason": "intent_service未初始化"}, level="ERROR")
        raise HTTPException(status_code=500, detail="intent_service 未初始化")

    marker("通用问答路由开始", {"question_len": len(request.question), "has_user_id": bool(request.user_id)})

    response = await handle_chat_general(
        request=request,
        intent_service=intent_service,
        chat_with_category=chat_with_category,
    )
    marker("通用问答路由完成", {})
    return response


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

@router.post("/api/stop", status_code=200)
async def stop_session(request: ChatDeleteRequest):
    """暂停/删除会话"""
    marker("会话停止请求", {"has_session_id": bool(request.session_id), "has_user_id": bool(request.user_id)})
    if request.session_id:
        # 按 session_id 删除
        if request.session_id not in session_manager.sessions:
            raise HTTPException(status_code=404, detail="会话不存在")
        session_manager.cleanup_expired_session(request.session_id)
    elif request.user_id:
        # 按 user_id 删除用户所有会话
        session_manager.cleanup_user_sessions(request.user_id)
    else:
        raise HTTPException(status_code=400, detail="session_id 或 user_id 不能为空")

    return "暂停成功"


@router.post("/api/sessions/{category}", response_model=SessionResponse)
async def create_category_session(category: str, request: SessionRequest):
    if category not in settings.ragflow.chat_ids:
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    chat_id = settings.ragflow.chat_ids[category]
    session_id = await get_or_create_session(chat_id, category, request.user_id)
    marker("创建会话成功", {"category": category, "session_id": session_id})

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
    marker("用户会话查询", {"user_id": user_id, "session_count": len(user_sessions)})

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

    marker("会话详情查询", {"session_id": session_id})

    return {"code": 0, "message": "获取成功", "data": session_manager.sessions[session_id]}


@router.get("/api/sessions")
async def get_all_sessions() -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    marker("全量会话查询", {"total": len(session_manager.sessions)})
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
    marker("删除会话成功", {"session_id": session_id})
    return {"code": 0, "message": "会话删除成功", "data": None}


@router.post("/ipark-ae/personnel-dispatch")
async def people_dispatch(request: PeopleDispatchRequest) -> Dict[str, Any]:
    """
    人员调度接口

    接收事故信息和语音文本，调用 Dify 人员调度 Chat 应用，
    返回人员ID列表（JSON格式）。

    Args:
        request: 包含 accidentId 和 voiceText 的请求体

    Returns:
        Dict[str, Any]: 包含人员调度结果的字典

    Raises:
        HTTPException: 当 voiceText 为空时
    """
    if not request.voiceText:
        marker("人员调度请求拒绝", {"accident_id": request.accidentId, "reason": "voice_text为空"}, level="WARNING")
        raise HTTPException(status_code=400, detail="voiceText 不能为空")

    marker("人员调度开始", {"accident_id": request.accidentId, "voice_len": len(request.voiceText)})

    user_id = None  # 可以从请求头或其他地方获取

    result = await handle_personnel_dispatch(
        voice_text=request.voiceText,
        user_id=user_id
    )

    if isinstance(result, dict):
        data = result.get("data")
        data_count = len(data) if isinstance(data, list) else 0
        marker("人员调度完成", {"accident_id": request.accidentId, "code": result.get("code"), "data_count": data_count})
    else:
        marker("人员调度完成", {"accident_id": request.accidentId, "result_type": type(result).__name__})

    return result

@router.post("/ipark-ae/source-dispatch")
async def source_dispatch(request: SourceDispatchRequest):
    """
    资源调度接口

    接收事故信息、资源类型和语音文本，处理资源调度请求。

    Args:
        request: 包含 accidentId、sourceType 和 voiceText 的请求体

    Returns:
        List[Dict[str, str]]: 资源列表
    """
    marker("资源调度开始", {"accident_id": request.accidentId, "source_type": request.sourceType, "has_voice_text": bool(request.voiceText)})
    result = await handle_source_dispatch(request)
    marker("资源调度完成", {"accident_id": request.accidentId, "source_type": request.sourceType, "result_count": len(result)})
    return result

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    session_manager.cleanup_all_expired_sessions()
    active_sessions = len(session_manager.sessions)
    active_users = len(session_manager.user_sessions)
    marker("健康检查", {"active_sessions": active_sessions, "active_users": active_users})
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": active_sessions,
        "active_users": active_users,
    }


@router.get("/api/categories")
async def get_categories() -> Dict[str, Any]:
    return {
        "code": 0,
        "message": "获取成功",
        "data": {"categories": list(settings.ragflow.chat_ids.keys()), "chat_ids": settings.ragflow.chat_ids},
    }


@router.post("/api/guess-questions")
async def guess_questions(request: GuessQuestionsRequest, http_request: Request) -> List[Dict[str, str]]:
    """
    猜你想问接口

    根据用户问题进行意图识别，返回推荐问题列表

    Args:
        request: 包含用户问题的请求

    Returns:
        推荐问题列表
    """
    from rag_stream.services.guess_questions_service import handle_guess_questions

    intent_service = getattr(http_request.app.state, "intent_service", None)
    if intent_service is None:
        raise HTTPException(status_code=500, detail="intent_service 未初始化")

    marker("猜你想问开始", {"question_len": len(request.question)})

    return await handle_guess_questions(request.question, intent_service)
