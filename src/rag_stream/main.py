import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 添加项目根目录到 Python 路径，以便导入 log_decorator
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_root = os.path.join(project_root, "src")
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from log_decorator import log, log_entry, logger

# 加载 rag_stream 的 .env 文件（包含 DIFY 配置）
rag_stream_env_path = Path(__file__).parent / ".env"
if rag_stream_env_path.exists():
    load_dotenv(rag_stream_env_path)
    logger.info(f"✓ 已加载 rag_stream 环境变量: {rag_stream_env_path}")
else:
    logger.warning(f"⚠ rag_stream .env 文件不存在: {rag_stream_env_path}")

# 加载 DaiShanSQL 的 .env 文件（包含 OPENAI_API_KEY 等配置）
daishan_env_path = Path(__file__).parent.parent / "DaiShanSQL" / "DaiShanSQL" / ".env"
if daishan_env_path.exists():
    load_dotenv(daishan_env_path)
    logger.info(f"✓ 已加载 DaiShanSQL 环境变量: {daishan_env_path}")
else:
    logger.warning(f"⚠ DaiShanSQL .env 文件不存在: {daishan_env_path}")
from fastapi.middleware.cors import CORSMiddleware

from src.routes.chat_routes import router
from src.config.settings import settings
from src.utils.ragflow_client import RagflowClient
from src.services.intent_service import IntentService

# 全局服务实例
ragflow_client = None
intent_service = None


@log()
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global ragflow_client, intent_service

    # 启动时初始化
    logger.info("=" * 60)
    logger.info("RAG 流式回复服务启动中...")
    logger.info("=" * 60)

    try:
        logger.info("✓ 配置加载成功")
        logger.info("✓ 日志系统初始化完成")

        # 初始化 RAGFlow 客户端
        ragflow_client = RagflowClient(settings.ragflow, settings.intent)

        # 测试 RAGFlow 连接
        if ragflow_client.test_connection():
            logger.info("✓ RAGFlow 连接测试成功")
        else:
            logger.warning("⚠ RAGFlow 连接测试失败,服务将降级运行")

        # 初始化意图识别服务
        intent_service = IntentService(ragflow_client)
        app.state.ragflow_client = ragflow_client
        app.state.intent_service = intent_service
        logger.info("✓ 意图识别服务初始化完成")

        logger.info("=" * 60)
        logger.info("✓ 服务启动成功!")
        logger.info("=" * 60)

        yield

    except Exception as e:
        logger.error(f"✗ 服务启动失败: {str(e)}")
        raise


app = FastAPI(
    title="RAG流式回复API",
    description="基于RAG的流式回复服务,支持多个专业领域的问答",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（使用绝对路径）
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 添加根路径重定向
@app.get("/")
@log_entry(enable_mermaid=True)
async def root():
    return RedirectResponse(url="/static/chat-test.html")

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.server.host, port=settings.server.port)
