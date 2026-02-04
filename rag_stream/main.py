import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# 加载 rag_stream 的 .env 文件（包含 DIFY 配置）
rag_stream_env_path = Path(__file__).parent / ".env"
if rag_stream_env_path.exists():
    load_dotenv(rag_stream_env_path)
    logging.info(f"✓ 已加载 rag_stream 环境变量: {rag_stream_env_path}")
else:
    logging.warning(f"⚠ rag_stream .env 文件不存在: {rag_stream_env_path}")

# 加载 DaiShanSQL 的 .env 文件（包含 OPENAI_API_KEY 等配置）
daishan_env_path = Path(__file__).parent.parent / "DaiShanSQL" / "DaiShanSQL" / ".env"
if daishan_env_path.exists():
    load_dotenv(daishan_env_path)
    logging.info(f"✓ 已加载 DaiShanSQL 环境变量: {daishan_env_path}")
else:
    logging.warning(f"⚠ DaiShanSQL .env 文件不存在: {daishan_env_path}")
from fastapi.middleware.cors import CORSMiddleware

from src.routes.chat_routes import router
from src.config.settings import settings
from src.services.log_manager import LogManager
from src.services.ragflow_client import RagflowClient
from src.services.intent_service import IntentService

logging.basicConfig(level=logging.INFO)

# 全局服务实例
log_manager = None
ragflow_client = None
intent_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global log_manager, ragflow_client, intent_service

    # 启动时初始化
    logging.info("=" * 60)
    logging.info("RAG 流式回复服务启动中...")
    logging.info("=" * 60)

    try:
        # 初始化日志管理器
        log_manager = LogManager(settings.logging)
        logging.info("✓ 配置加载成功")
        logging.info("✓ 日志系统初始化完成")

        # 初始化 RAGFlow 客户端
        ragflow_client = RagflowClient(settings.ragflow, settings.intent, log_manager)

        # 测试 RAGFlow 连接
        if ragflow_client.test_connection():
            logging.info("✓ RAGFlow 连接测试成功")
        else:
            logging.warning("⚠ RAGFlow 连接测试失败,服务将降级运行")

        # 初始化意图识别服务
        intent_service = IntentService(log_manager, ragflow_client)
        logging.info("✓ 意图识别服务初始化完成")

        logging.info("=" * 60)
        logging.info("✓ 服务启动成功!")
        logging.info("=" * 60)

        yield

    except Exception as e:
        logging.error(f"✗ 服务启动失败: {str(e)}")
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
async def root():
    return RedirectResponse(url="/static/chat-test.html")

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.server.host, port=settings.server.port)
