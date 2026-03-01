"""FastAPI application main entry point for rag_stream service.

This module creates the FastAPI application with lifecycle management,
including startup initialization and graceful shutdown.
"""

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from log_manager import LogManagerConfig, configure, entry_trace, marker

from rag_stream.config.settings import settings
from rag_stream.lifespan import lifespan as modular_lifespan
from rag_stream.routes.chat_routes import router
from rag_stream.services.intent_service import IntentService
from rag_stream.utils.ragflow_client import RagflowClient

# Global service instances
ragflow_client = None
intent_service = None
base_dir = Path(__file__).resolve().parents[1]

# Initialize log-manager
cfg = LogManagerConfig()
cfg.base_dir = base_dir / ".log-manager"
cfg.session_id = f"rag_stream_{int(datetime.now().timestamp())}"
cfg.parameter_whitelist = ("user_id", "session_id", "category", "chat_id")
cfg.enable_background_threads = True
cfg.report.trigger_timer_s = 60
cfg.report.immediate_on_error = True
runtime = configure(cfg)

# Load rag_stream .env file (contains DIFY configuration)
rag_stream_env_path = base_dir / ".env"
if rag_stream_env_path.exists():
    load_dotenv(rag_stream_env_path)
    marker("环境变量加载", {"path": str(rag_stream_env_path), "source": "rag_stream"})
else:
    marker(
        "环境变量加载",
        {"path": str(rag_stream_env_path), "exists": False},
        level="WARNING",
    )

# Load DaiShanSQL .env file (contains OPENAI_API_KEY etc.)
daishan_env_path = base_dir.parent / "DaiShanSQL" / "DaiShanSQL" / ".env"
if daishan_env_path.exists():
    load_dotenv(daishan_env_path)
    marker("环境变量加载", {"path": str(daishan_env_path), "source": "DaiShanSQL"})
else:
    marker(
        "环境变量加载",
        {"path": str(daishan_env_path), "exists": False},
        level="WARNING",
    )


# Use the modular lifespan context manager from lifespan.py
# This provides standardized startup/shutdown handling with proper logging
# The modular lifespan initializes: HTTP client, database checks, external services
app = FastAPI(
    title="RAG流式回复API",
    description="基于RAG的流式回复服务,支持多个专业领域的问答",
    version="1.0.0",
    lifespan=modular_lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = base_dir / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Root endpoint redirects to chat test page."""
    return RedirectResponse(url="/static/chat-test.html")


# Include chat routes
app.include_router(router)


# Store service references in app.state during startup
# These are set by the service initialization logic
# Note: The modular lifespan handles HTTP client and basic resources
# Service-specific initialization (RAGFlow, IntentService) is done separately
@app.on_event("startup")
@entry_trace("service-init")
async def initialize_services():
    """Initialize service-specific components (RAGFlow, IntentService).

    This runs after the modular lifespan startup and handles service-specific
    initialization that requires the application's business logic.
    """
    global ragflow_client, intent_service

    marker("服务初始化开始", {"version": "1.0.0"})

    try:
        # Initialize RAGFlow client
        ragflow_client = RagflowClient(settings.ragflow, settings.intent)

        # Test RAGFlow connection
        connection_ok = ragflow_client.test_connection()
        marker("RAGFlow连接测试", {"success": connection_ok})
        if not connection_ok:
            marker("RAGFlow连接测试失败", {"mode": "降级运行"}, level="WARNING")

        # Initialize intent service
        intent_service = IntentService(ragflow_client)
        app.state.ragflow_client = ragflow_client
        app.state.intent_service = intent_service
        marker("意图识别服务初始化完成", {})

        marker(
            "服务初始化成功",
            {"host": settings.server.host, "port": settings.server.port},
        )

    except Exception as exc:
        marker("服务初始化失败", {"error": str(exc)}, level="ERROR")
        raise


@app.on_event("shutdown")
async def shutdown_services():
    """Clean up service-specific components.

    This runs before the modular lifespan shutdown and handles
    service-specific cleanup. The modular lifespan handles HTTP client
    and other infrastructure resources.
    """
    marker("服务关闭开始", {})

    try:
        # Shutdown log-manager runtime
        runtime.shutdown()
        marker("服务关闭完成", {})

    except Exception as exc:
        marker("服务关闭错误", {"error": str(exc)}, level="ERROR")
        # Don't re-raise - shutdown should complete


if __name__ == "__main__":
    import uvicorn

    # For local development only
    # In production, use the Dockerfile CMD with proper worker/timeout settings
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
    )
