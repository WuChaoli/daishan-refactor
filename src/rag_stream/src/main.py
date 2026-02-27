from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from log_manager import LogManagerConfig, configure, entry_trace, marker

from rag_stream.config.settings import settings
from rag_stream.routes.chat_routes import router
from rag_stream.services.intent_service import IntentService
from rag_stream.utils.ragflow_client import RagflowClient

# 全局服务实例
ragflow_client = None
intent_service = None
base_dir = Path(__file__).resolve().parents[1]

# 初始化 log-manager
cfg = LogManagerConfig()
cfg.base_dir = base_dir / ".log-manager"
cfg.session_id = f"rag_stream_{int(datetime.now().timestamp())}"
cfg.parameter_whitelist = ("user_id", "session_id", "category", "chat_id")
cfg.enable_background_threads = True
cfg.report.trigger_timer_s = 60
cfg.report.immediate_on_error = True
runtime = configure(cfg)

# 加载 rag_stream 的 .env 文件（包含 DIFY 配置）
rag_stream_env_path = base_dir / ".env"
if rag_stream_env_path.exists():
    load_dotenv(rag_stream_env_path)
    marker("环境变量加载", {"path": str(rag_stream_env_path), "source": "rag_stream"})
else:
    marker("环境变量加载", {"path": str(rag_stream_env_path), "exists": False}, level="WARNING")

# 加载 DaiShanSQL 的 .env 文件（包含 OPENAI_API_KEY 等配置）
daishan_env_path = base_dir.parent / "DaiShanSQL" / "DaiShanSQL" / ".env"
if daishan_env_path.exists():
    load_dotenv(daishan_env_path)
    marker("环境变量加载", {"path": str(daishan_env_path), "source": "DaiShanSQL"})
else:
    marker("环境变量加载", {"path": str(daishan_env_path), "exists": False}, level="WARNING")


@asynccontextmanager
@entry_trace("app-lifespan")
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global ragflow_client, intent_service

    marker("服务启动开始", {"version": "1.0.0"})

    try:
        marker("配置加载完成", {})
        marker("日志系统初始化完成", {"system": "log-manager"})

        # 初始化 RAGFlow 客户端
        ragflow_client = RagflowClient(settings.ragflow, settings.intent)

        # 测试 RAGFlow 连接
        connection_ok = ragflow_client.test_connection()
        marker("RAGFlow连接测试", {"success": connection_ok})
        if not connection_ok:
            marker("RAGFlow连接测试失败", {"mode": "降级运行"}, level="WARNING")

        # 初始化意图识别服务
        intent_service = IntentService(ragflow_client)
        app.state.ragflow_client = ragflow_client
        app.state.intent_service = intent_service
        marker("意图识别服务初始化完成", {})

        marker("服务启动成功", {"host": settings.server.host, "port": settings.server.port})
        yield
    except Exception as exc:
        marker("服务启动失败", {"error": str(exc)}, level="ERROR")
        raise
    finally:
        marker("服务关闭开始", {})
        runtime.shutdown()


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

static_dir = base_dir / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/chat-test.html")


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.server.host, port=settings.server.port)
