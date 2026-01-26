from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict
import logging
from contextlib import asynccontextmanager
import time

# ------------------- 配置与日志初始化 -------------------
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stream_chat_api")

# API 核心配置
FIXED_API_KEY = "app-Dkzi2px4Gg8F7vaUdn22Z3VL"
FIXED_BASE_URL = "http://172.16.11.60/v1"
DIFY_ENDPOINT = "/chat-messages"
DIFY_TIMEOUT = 30.0  # 超时时间，单位：秒

# FastAPI 服务配置
APP_NAME = "Streaming Chat FastAPI"
APP_VERSION = "1.0.0"
FIXED_PORT = 11029
MAX_RETRY_ATTEMPTS = 2  # 最大重试次数
RETRY_DELAY = 1.0  # 重试延迟，单位：秒

# CORS配置 - 生产环境应替换为具体域名
ALLOWED_ORIGINS = ["*"]  # 开发环境配置


# ------------------- FastAPI 应用初始化 -------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，可用于初始化和清理资源"""
    logger.info("应用启动中...")
    # 初始化异步HTTP客户端
    app.state.http_client = httpx.AsyncClient(timeout=DIFY_TIMEOUT)
    yield
    # 关闭异步HTTP客户端
    await app.state.http_client.aclose()
    logger.info("应用已关闭")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="基于 FastAPI 封装的流式聊天接口，保留打字机效果，端口：11029",
    lifespan=lifespan
)

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------- 请求参数模型 -------------------
class ChatInput(BaseModel):
    """请求体参数模型：仅包含前端需传递的输入"""
    text_input: str  # 用户输入文本
    user_id: Optional[str] = "fastapi_client_user"  # 可选用户标识


# ------------------- 工具函数 -------------------
async def create_dify_payload(text_input: str, user_id: str) -> Dict:
    """创建 API请求体"""
    return {
        "query": text_input,
        "inputs": {},
        "response_mode": "streaming",
        "user": user_id,
        "conversation_id": "",
        "auto_generate_name": True,
        "files": []
    }


async def get_dify_headers() -> Dict:
    """获取 API请求头"""
    return {
        "Authorization": f"Bearer {FIXED_API_KEY}",
        "Content-Type": "application/json"
    }


# ------------------- 核心生成器函数 -------------------
async def dify_async_stream_generator(
    text_input: str,
    user_id: str,
    http_client: httpx.AsyncClient
) -> AsyncGenerator[str, None]:
    """异步生成器：处理 API流式响应并生成标准SSE格式输出"""
    try:
        # 构建请求参数
        headers = await get_dify_headers()
        payload = await create_dify_payload(text_input, user_id)
        url = f"{FIXED_BASE_URL}{DIFY_ENDPOINT}"
        
        logger.info(f"向API发送请求: {url}, 用户ID: {user_id}")
        start_time = time.time()  # 记录开始时间
        first_output_sent = False  # 标记是否已发送第一个输出
        # 发送流式请求（带重试机制）
        retry_count = 0
        while retry_count <= MAX_RETRY_ATTEMPTS:
            try:
                async with http_client.stream(
                    "POST", 
                    url, 
                    headers=headers, 
                    json=payload
                ) as response:
                    # 检查HTTP状态码
                    if response.status_code != 200:
                        error_detail = await response.text()
                        error_msg = (f" API请求失败，状态码: {response.status_code}, "
                                    f"响应: {error_detail[:200]}")
                        logger.error(error_msg)
                        # 发送错误事件
                        yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                        break
                    
                    # 发送开始事件
                    yield f"event: start\ndata: {json.dumps({'message': '开始流式输出'}, ensure_ascii=False)}\n\n"
                    
                    # 解析SSE流式数据
                    message_id = 0
                    async for line in response.aiter_lines():
                        if not first_output_sent and (time.time() - start_time > 15):
                            timeout_data = {
                                "code": 1,
                                "message": "当前网络异常，请稍后再试。",
                                "data": {
                                        "answer": "当前网络异常，请稍后再试。",
                                        "flag": 1,
                                        "wordId": message_id,
                                        "end": 0
                                    }
                            }
                            yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\n\n"
                            timeout_data1 = {
                                "code": 1,
                                "data": {
                                        "answer": "",
                                        "flag": 0,
                                        "wordId": message_id+1,
                                        "end": 1
                                    }
                                    }
                            yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\n\n"
                            return
                        if not line or not line.startswith("data: "):
                            continue
                            
                        data_str = line.lstrip("data: ").strip()
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError as e:
                            warn_msg = (f"解析流式数据失败: {str(e)}, "
                                       f"原始数据: {data_str[:100]}")
                            logger.warning(warn_msg)
                            yield f"event: warning\ndata: {json.dumps({'warning': warn_msg}, ensure_ascii=False)}\n\n"
                            continue
                            
                        event_type = data.get("event")
                        if event_type == "message":
                            answer_chunk = data.get("answer", "")
                            if answer_chunk:
                                # 优化打字机效果：批量处理字符，减少yield次数
                                if not first_output_sent:
                                    first_output_sent = True

                                if not first_output_sent and time.time() - start_time > 15:
                                    timeout_data = {
                                        "code": 1,
                                        "message": "当前网络异常，请稍后再试。",
                                        "data": {
                                                "answer": "当前网络异常，请稍后再试。",
                                                "flag": 1,
                                                "wordId": message_id,
                                                "end": 0
                                            }
                                    }
                                    yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\n\n"
                                    timeout_data1 = {
                                        "code": 1,
                                        "data": {
                                                "answer": "",
                                                "flag": 0,
                                                "wordId": message_id+1,
                                                "end": 1
                                            }
                                    }
                                    yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\n\n"
                                    return
                                chunk_size = 3  # 每次输出3个字符
                                for i in range(0, len(answer_chunk), chunk_size):
                                    chunk = answer_chunk[i:i+chunk_size]
                                    message_id += 1
                                    # 发送消息片段事件
                                    yield f"id: {message_id}\nevent: message\ndata: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
                                    await asyncio.sleep(0.02)  # 调整延迟时间
                                    
                        elif event_type == "message_end":
                            # 发送完成事件
                            yield f"event: complete\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\n\n"
                            logger.info(f"流式输出完成，用户ID: {user_id}")
                            break
                            
                        elif event_type == "error":
                            error_msg = (f"API流式处理错误: {data.get('message', '未知错误')} "
                                       f"(task_id: {data.get('task_id')})")
                            logger.error(error_msg)
                            yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                            break
                    
                    # 发送结束事件
                    yield f"event: end\ndata: [DONE]\n\n"
                    
                    # 如果成功处理，跳出重试循环
                    break
                    
            except httpx.TimeoutException:
                retry_count += 1
                if retry_count > MAX_RETRY_ATTEMPTS:
                    error_msg = f"请求超时，已重试{MAX_RETRY_ATTEMPTS}次仍失败"
                    logger.error(error_msg)
                    yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                    break
                logger.warning(f"请求超时，正在进行第{retry_count}次重试...")
                await asyncio.sleep(RETRY_DELAY * retry_count)  # 指数退避
                
            except httpx.RequestError as e:
                error_msg = f"请求发生错误: {str(e)[:150]}"
                logger.error(error_msg)
                yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                break
    
    except Exception as e:
        error_msg = f"处理请求时发生异常: {str(e)[:150]}"
        logger.exception(error_msg)  # 记录完整异常堆栈
        yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"


# ------------------- 核心接口 -------------------
@app.post(
    "/api/stream-chat",
    summary="流式聊天接口（标准SSE格式）",
    description="接收text_input，返回标准SSE格式的流式输出，支持事件类型：start, message, complete, error, warning, end",
    response_class=StreamingResponse
)
async def stream_chat(input_data: ChatInput, request: Request):
    """
    示例请求体：
    {
        "text_input": "请介绍贵公司",
        "user_id": "user_001"  // 可选，默认 fastapi_client_user
    }
    
    SSE事件格式：
    - event: start - 开始流式输出
    - event: message - 消息内容片段 (data: {"content": "文本片段", "type": "chunk"})
    - event: complete - 流式输出完成
    - event: error - 错误信息
    - event: warning - 警告信息
    - event: end - 流结束 (data: [DONE])
    """
    # 校验输入
    if not input_data.text_input.strip():
        raise HTTPException(status_code=400, detail="text_input 字段不能为空")
    
    # 从应用状态获取HTTP客户端
    http_client = request.app.state.http_client
    
    # 返回流式响应
    return StreamingResponse(
        content=dify_async_stream_generator(
            text_input=input_data.text_input.strip(),
            user_id=input_data.user_id.strip(),
            http_client=http_client
        ),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


# ------------------- 健康检查接口 -------------------
@app.get("/health", summary="服务健康检查")
async def health_check():
    """检查服务是否正常运行"""
    return {"status": "healthy", "service": APP_NAME, "version": APP_VERSION}


# ------------------- 启动服务 -------------------
if __name__ == "__main__":
    import uvicorn
    logger.info(f"FastAPI 服务启动中... 端口: {FIXED_PORT}")
    logger.info(f"接口文档地址: http://localhost:{FIXED_PORT}/docs")
    
    uvicorn.run(
        app="__main__:app",
        host="0.0.0.0",
        port=FIXED_PORT,
        reload=False,
        workers=1  # 流式处理建议单进程
    )
    