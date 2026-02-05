from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.config.settings import settings
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatDeleteRequest,
    SessionRequest,
    SessionResponse,
    PeopleDispatchRequest,
    SourceDispatchRequest,
)
from src.services.dify_service import should_use_dify, stream_dify_chatflow_response
from src.services.personnel_dispatch_service import handle_personnel_dispatch
from src.services.rag_service import get_or_create_session, stream_chat_response
from src.services.source_dispath_srvice import handle_source_dispatch
from src.utils.session_manager import session_manager
from src.services.log_manager import LogManager
from src.services.ragflow_client import RagflowClient
from src.services.intent_service import IntentService

# 直接初始化意图识别服务所需的组件
log_manager = LogManager(settings.logging)
ragflow_client = RagflowClient(settings.ragflow, settings.intent, log_manager)
intent_service = IntentService(log_manager, ragflow_client)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/chat/{category}", response_model=ChatResponse)
async def chat_with_category(
    category: str,
    request: ChatRequest,
):
    """通用聊天接口，根据类别选择对应的chat_id"""
    user_id = request.user_id or None
    if category not in settings.ragflow.chat_ids:
        raise HTTPException(status_code=400, detail=f"不支持的类别: {category}")

    chat_id = settings.ragflow.chat_ids[category]
    logger.debug("chat_id: %s", chat_id)

    session_id = await get_or_create_session(chat_id, category, user_id)
    logger.debug("session_id: %s", session_id)

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
async def chat_general(request: ChatRequest):
    """
    通用问答接口 - 使用意图识别路由
    """
    user_id = request.user_id or "anonymous"

    # process_query 现在直接返回字典
    result_dict = await intent_service.process_query(request.question, user_id)

    # 提取 type 字段判断如何处理
    result_type = result_dict.get("type")
    logger.debug("result_type: %s", result_type)

    if result_type == 1:
        data = result_dict.get("data", {})
        sql_result = data.get("sql_result", "")
        kb_name = data.get("kb_name", "")

        if sql_result:
            # 将 sql_result 转换为字符串
            sql_result_str = str(sql_result)

            # 创建新的 request 对象
            updated_request = ChatRequest(
                question=f"{request.question}\n\n{sql_result_str}",
                user_id=request.user_id,
            )

            logger.debug("kb_name: %s", kb_name)
            return await chat_with_category(kb_name, updated_request)
        
    elif result_type == 2:
        # type=2: 提取 data.sql_result，转换成字符串，与 request.question 拼接
        data = result_dict.get("data", {})
        sql_result = data.get("sql_result", "")

        if sql_result:
            # 将 sql_result 转换为字符串
            sql_result_str = str(sql_result)

            # 创建新的 request 对象
            updated_request = ChatRequest(
                question=f"{request.question}\n\n{sql_result_str}",
                user_id=request.user_id,
            )

            # 调用 chat_with_category("通用", request)
            return await chat_with_category("通用", updated_request)


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
        raise HTTPException(status_code=400, detail="voiceText 不能为空")

    user_id = None  # 可以从请求头或其他地方获取

    result = await handle_personnel_dispatch(
        voice_text=request.voiceText,
        log_manager=log_manager,
        user_id=user_id
    )

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
    result = await handle_source_dispatch(request, log_manager)
    return result

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
        "data": {"categories": list(settings.ragflow.chat_ids.keys()), "chat_ids": settings.ragflow.chat_ids},
    }
