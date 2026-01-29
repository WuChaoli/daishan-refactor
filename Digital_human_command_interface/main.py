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
from src.log_manager import LogManager
from src.ragflow_client import RagflowClient
from src.api.routes import router

# 加载环境变量 - 使用绝对路径确保正确加载
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)


# ============================================================
# 应用生命周期管理
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """统一的应用生命周期管理"""

    # ========== 启动阶段 ==========
    print("=" * 60)
    print("岱山意图识别服务启动中...")
    print("=" * 60)

    try:
        # 1. 加载配置
        # 使用绝对路径，确保无论从哪个目录启动都能找到配置文件
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        config_manager = ConfigManager(config_path)
        config = config_manager.get_config()
        app.state.config_manager = config_manager

        if config is None:
            print("✗ 配置加载失败: config is None")
            raise ValueError("Config not initialized")

        print("✓ 配置加载成功")

        # 2. 初始化日志管理器
        log_manager = LogManager(config)
        app.state.log_manager = log_manager
        print("✓ 日志系统初始化完成")

        # 3. 初始化 httpx.AsyncClient（用于流式聊天）
        dify_timeout = config.stream_chat_timeout if hasattr(config, 'stream_chat_timeout') else 30.0
        app.state.http_client = httpx.AsyncClient(timeout=dify_timeout)
        print("✓ HTTP 客户端初始化完成")

        # 4. 初始化 RAGFlow 客户端
        try:
            ragflow_client = RagflowClient(config, log_manager)
            app.state.ragflow_client = ragflow_client

            # 测试 RAGFlow 连接
            if ragflow_client.test_connection():
                print("✓ RAGFlow 连接测试成功")
            else:
                print("⚠ RAGFlow 连接测试失败，服务将降级运行")
        except Exception as e:
            print(f"⚠ RAGFlow 客户端初始化失败: {e}")
            print("  服务将在降级模式下运行")
            app.state.ragflow_client = None

        # 5. 初始化 Dify Chat 客户端（SQL 结果格式化）
        try:
            from dify_sdk import DifyClient

            dify_chat_client = DifyClient.from_config(
                name="sql_result_formatter",
                app_type="chat",
                environment="default",
                config_path=config_path  # 显式传递配置文件路径
            )
            app.state.dify_chat_client = dify_chat_client
            print("✓ Dify Chat 客户端初始化完成 (SQL 结果格式化)")
        except Exception as e:
            print(f"⚠ Dify Chat 初始化失败: {e}")
            print("  服务将在降级模式下运行 (Type 2 handler 返回原始结果)")
            app.state.dify_chat_client = None

        # 6. 初始化三个知识库 Chat 客户端（Type 1 handler 使用）
        try:
            from dify_sdk import DifyClient

            park_kb_client = DifyClient.from_config(
                name="park_kb_chat",
                app_type="chat",
                environment="default",
                config_path=config_path  # 显式传递配置文件路径
            )
            app.state.park_kb_client = park_kb_client

            enterprise_kb_client = DifyClient.from_config(
                name="enterprise_kb_chat",
                app_type="chat",
                environment="default",
                config_path=config_path  # 显式传递配置文件路径
            )
            app.state.enterprise_kb_client = enterprise_kb_client

            safety_kb_client = DifyClient.from_config(
                name="safety_kb_chat",
                app_type="chat",
                environment="default",
                config_path=config_path  # 显式传递配置文件路径
            )
            app.state.safety_kb_client = safety_kb_client

            print("✓ 三个知识库 Chat 客户端初始化完成")
            print("  - 园区知识库 Chat: 已就绪")
            print("  - 企业知识库 Chat: 已就绪")
            print("  - 安全信息知识库 Chat: 已就绪")

        except Exception as e:
            print(f"⚠ 知识库 Chat 客户端初始化失败: {e}")
            print("  Type 1 handler 将无法使用 Dify Chat 功能")
            app.state.park_kb_client = None
            app.state.enterprise_kb_client = None
            app.state.safety_kb_client = None

        # 7. 初始化 Type 0 语义问答 Dify Chat 客户端
        try:
            from dify_sdk import DifyClient

            type0_semantic_client = DifyClient.from_config(
                name="type0_semantic_chat",
                app_type="chat",
                environment="default",
                config_path=config_path  # 显式传递配置文件路径
            )
            app.state.type0_semantic_client = type0_semantic_client
            print("✓ Type 0 语义问答 Chat 客户端初始化完成")
        except Exception as e:
            print(f"⚠ Type 0 语义问答 Chat 客户端初始化失败: {e}")
            print("  Type 0 handler 将无法使用 Dify Chat 功能")
            app.state.type0_semantic_client = None

        # 8. 记录启动时间
        app.state.start_time = time.time()

        print("=" * 60)
        print("✓ 服务启动成功!")
        print(f"  监听地址: {config.server_host}:{config.server_port}")
        print(f"  API 文档: http://{config.server_host}:{config.server_port}/docs")
        print("=" * 60)

        # 写入全局日志文件
        log_manager.log_info("服务启动成功")
        log_manager.log_info(f"监听地址: {config.server_host}:{config.server_port}")

        # 终端输出（绿色）
        log_manager.log_to_console("INFO", "岱山意图识别服务启动成功")

        yield

    except Exception as e:
        print(f"✗ 服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # ========== 关闭阶段 ==========
        print("\n服务关闭中...")

        # 关闭 httpx.AsyncClient
        if hasattr(app.state, 'http_client'):
            await app.state.http_client.aclose()

        # 记录运行时长
        if hasattr(app.state, 'log_manager') and hasattr(app.state, 'start_time'):
            runtime = time.time() - app.state.start_time
            app.state.log_manager.log_info(f"服务运行时长: {runtime:.2f} 秒")
            app.state.log_manager.log_to_console(
                "INFO", f"服务已关闭，运行时长: {runtime:.2f} 秒"
            )

        print("服务已关闭")


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

    # 从配置读取端口（默认 11028）
    try:
        config_manager = ConfigManager("config.yaml")
        config = config_manager.get_config()
        port = config.server_port if config else 11028
        host = config.server_host if config else "0.0.0.0"
    except Exception:
        port = 11028
        host = "0.0.0.0"

    print(f"FastAPI 服务启动中... 端口: {port}")
    print(f"接口文档地址: http://localhost:{port}/docs")

    uvicorn.run(
        app=app,
        host=host,
        port=port,
        reload=False,
        workers=1
    )
