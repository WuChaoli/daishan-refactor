"""
岱山意图识别服务 - 主入口
"""

import os
import sys
import time
import httpx
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径，以便导入 SDK 包
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import ConfigManager
from src.ragflow_client import RagflowClient
from src.api.routes import router
from log_decorator import log, logger

# 加载环境变量 - 使用绝对路径确保正确加载
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)


# ============================================================
# 应用生命周期管理
# ============================================================

@log()
@asynccontextmanager
async def lifespan(app: FastAPI):
    """统一的应用生命周期管理"""

    # ========== 启动阶段 ==========
    logger.info("=" * 60)
    logger.info("岱山意图识别服务启动中...")
    logger.info("=" * 60)

    try:
        # 1. 加载配置
        # 使用绝对路径，确保无论从哪个目录启动都能找到配置文件
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        config_manager = ConfigManager(config_path)
        config = config_manager.get_config()
        app.state.config_manager = config_manager

        if config is None:
            logger.error("✗ 配置加载失败: config is None")
            raise ValueError("Config not initialized")

        logger.info("✓ 配置加载成功")

        # 2. 初始化 httpx.AsyncClient（用于流式聊天）
        dify_timeout = config.stream_chat_timeout if hasattr(config, 'stream_chat_timeout') else 30.0
        app.state.http_client = httpx.AsyncClient(timeout=dify_timeout)
        logger.info("✓ HTTP 客户端初始化完成")

        # 3. 初始化 RAGFlow 客户端
        try:
            ragflow_client = RagflowClient(config)
            app.state.ragflow_client = ragflow_client

            # 测试 RAGFlow 连接
            if ragflow_client.test_connection():
                logger.info("✓ RAGFlow 连接测试成功")
            else:
                logger.warning("⚠ RAGFlow 连接测试失败，服务将降级运行")
        except Exception as e:
            logger.warning(f"⚠ RAGFlow 客户端初始化失败: {e}")
            logger.warning("  服务将在降级模式下运行")
            app.state.ragflow_client = None

        # 4. 初始化 Dify Chat 客户端（SQL 结果格式化）
        try:
            from dify_sdk import DifyClient

            sql_formatter_key = os.getenv("DIFY_CHAT_SQL_FORMATTER_KEY")
            if not sql_formatter_key:
                raise ValueError("环境变量 DIFY_CHAT_SQL_FORMATTER_KEY 未设置")

            dify_base_url = os.getenv("DIFY_BASE_RUL", "http://172.16.11.60/v1")
            dify_chat_client = DifyClient(
                api_key=sql_formatter_key,
                base_url=dify_base_url
            )
            app.state.dify_chat_client = dify_chat_client
            logger.info("✓ Dify Chat 客户端初始化完成 (SQL 结果格式化)")
        except Exception as e:
            logger.warning(f"⚠ Dify Chat 初始化失败: {e}")
            logger.warning("  服务将在降级模式下运行 (Type 2 handler 返回原始结果)")
            app.state.dify_chat_client = None

        # 5. 初始化三个知识库 Chat 客户端（Type 1 handler 使用）
        try:
            from dify_sdk import DifyClient

            dify_base_url = os.getenv("DIFY_BASE_RUL", "http://172.16.11.60/v1")

            park_kb_key = os.getenv("DIFY_CHAT_PARK_KB_KEY")
            enterprise_kb_key = os.getenv("DIFY_CHAT_ENTERPRISE_KB_KEY")
            safety_kb_key = os.getenv("DIFY_CHAT_SAFETY_KB_KEY")

            if not all([park_kb_key, enterprise_kb_key, safety_kb_key]):
                missing = []
                if not park_kb_key:
                    missing.append("DIFY_CHAT_PARK_KB_KEY")
                if not enterprise_kb_key:
                    missing.append("DIFY_CHAT_ENTERPRISE_KB_KEY")
                if not safety_kb_key:
                    missing.append("DIFY_CHAT_SAFETY_KB_KEY")
                raise ValueError(f"环境变量未设置: {', '.join(missing)}")

            app.state.park_kb_client = DifyClient(
                api_key=park_kb_key,
                base_url=dify_base_url
            )
            app.state.enterprise_kb_client = DifyClient(
                api_key=enterprise_kb_key,
                base_url=dify_base_url
            )
            app.state.safety_kb_client = DifyClient(
                api_key=safety_kb_key,
                base_url=dify_base_url
            )

            logger.info("✓ 三个知识库 Chat 客户端初始化完成")
            logger.info("  - 园区知识库 Chat: 已就绪")
            logger.info("  - 企业知识库 Chat: 已就绪")
            logger.info("  - 安全信息知识库 Chat: 已就绪")

        except Exception as e:
            logger.warning(f"⚠ 知识库 Chat 客户端初始化失败: {e}")
            logger.warning("  Type 1 handler 将无法使用 Dify Chat 功能")
            app.state.park_kb_client = None
            app.state.enterprise_kb_client = None
            app.state.safety_kb_client = None

        # 6. 初始化 Type 0 语义问答 Dify Chat 客户端
        try:
            from dify_sdk import DifyClient

            type0_semantic_key = os.getenv("DIFY_CHAT_TYPE0_SEMANTIC_KEY")
            if not type0_semantic_key:
                raise ValueError("环境变量 DIFY_CHAT_TYPE0_SEMANTIC_KEY 未设置")

            dify_base_url = os.getenv("DIFY_BASE_RUL", "http://172.16.11.60/v1")
            app.state.type0_semantic_client = DifyClient(
                api_key=type0_semantic_key,
                base_url=dify_base_url
            )
            logger.info("✓ Type 0 语义问答 Chat 客户端初始化完成")
        except Exception as e:
            logger.warning(f"⚠ Type 0 语义问答 Chat 客户端初始化失败: {e}")
            logger.warning("  Type 0 handler 将无法使用 Dify Chat 功能")
            app.state.type0_semantic_client = None

        # 7. 记录启动时间
        app.state.start_time = time.time()

        logger.info("=" * 60)
        logger.info("✓ 服务启动成功!")
        logger.info(f"  监听地址: {config.server_host}:{config.server_port}")
        logger.info(f"  API 文档: http://{config.server_host}:{config.server_port}/docs")
        logger.info("=" * 60)

        yield

    except Exception as e:
        logger.error(f"✗ 服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # ========== 关闭阶段 ==========
        logger.info("\n服务关闭中...")

        # 关闭 httpx.AsyncClient
        if hasattr(app.state, 'http_client'):
            await app.state.http_client.aclose()

        # 记录运行时长
        if hasattr(app.state, 'start_time'):
            runtime = time.time() - app.state.start_time
            logger.info(f"服务运行时长: {runtime:.2f} 秒")

        logger.info("服务已关闭")


# ============================================================
# 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="岱山意图识别服务",
    description="基于 RAGFlow 的用户指令意图识别 REST API，集成流式聊天功能",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


# ============================================================
# 启动服务
# ============================================================

if __name__ == "__main__":
    import uvicorn
    import sys

    # 从配置读取端口（使用绝对路径）
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        config_manager = ConfigManager(config_path)
        config = config_manager.get_config()
        port = config.server_port
        host = config.server_host
    except Exception as e:
        logger.error(f"✗ 配置加载失败: {e}")
        logger.error("服务启动中止，请检查配置文件")
        sys.exit(1)

    logger.info(f"FastAPI 服务启动中... 端口: {port}")
    logger.info(f"接口文档地址: http://localhost:{port}/docs")

    uvicorn.run(
        app=app,
        host=host,
        port=port,
        reload=False,
        workers=1
    )
