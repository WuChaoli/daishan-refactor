"""
模拟调用 IntentService.process_query 测试脚本

这个脚本创建最小化的 Mock 对象，直接调用 IntentService.process_query 方法
验证流程是否能通。
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

# 添加 rag_stream 根目录到 sys.path
rag_stream_root = Path(__file__).parents[1]

from rag_stream.services.intent_service import IntentResult, QueryResult
from rag_stream.services.log_manager import LogManager
from rag_stream.services.intent_service import IntentService
from rag_stream.utils.ragflow_client import RetrievalResult
from rag_stream.config.settings import IntentConfig, LoggingConfig, RAGFlowConfig


# ==================== Mock 类 ====================

class MockLogManager:
    """简化的日志管理器，输出到控制台"""

    def __init__(self, config: LoggingConfig):
        self.config = config

        # 创建日志目录结构
        self.log_dir = Path(config.log_dir)
        self._setup_log_directories()

        # 功能级日志器缓存
        self._function_loggers = {}

        # 设置控制台输出
        self._setup_console_handlers()

    def _setup_log_directories(self):
        """创建日志目录结构"""
        directories = [
            self.log_dir / "global",
            self.log_dir / "functions",
            self.log_dir / "archive",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_console_handlers(self):
        """设置控制台输出"""
        self.console_logger = logging.getLogger("test_console")
        self.console_logger.setLevel(logging.DEBUG)

        # 清除现有的 handlers
        self.console_logger.handlers.clear()

        # 创建 handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.console_logger.addHandler(handler)

    def get_function_logger(self, name: str) -> logging.Logger:
        """获取功能级日志器"""
        if name not in self._function_loggers:
            logger = logging.getLogger(f"test_func_{name}")
            logger.setLevel(logging.DEBUG)
            logger.handlers.clear()

            # 添加控制台 handler
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            self._function_loggers[name] = logger

        return self._function_loggers[name]

    def log_info(self, message: str):
        """记录全局 INFO 日志"""
        self.console_logger.info(message)

    def log_error(self, message: str, exc_info: bool = False):
        """记录全局 ERROR 日志"""
        self.console_logger.error(message, exc_info=exc_info)

    def log_function(self, module: str, level: str, message: str, **kwargs):
        """记录功能级日志"""
        logger = self.get_function_logger(module)
        log_func = getattr(logger, level.lower(), logger.info)
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context}"
        log_func(message)


class MockRagflowClient:
    """模拟 RAGFlow 客户端，返回预设的检索结果"""

    def __init__(
        self,
        ragflow_config: RAGFlowConfig,
        intent_config: IntentConfig,
        log_manager: LogManager,
        test_mode: str = "type0",
    ):
        """
        初始化 Mock 客户端

        Args:
            ragflow_config: RAGFlow 配置
            intent_config: 意图判断配置
            log_manager: 日志管理器
            test_mode: 测试模式 ('type0', 'type1', 'type2')
        """
        self.ragflow_config = ragflow_config
        self.intent_config = intent_config
        self.log_manager = log_manager
        self.logger = log_manager.get_function_logger("ragflow_client")
        self.test_mode = test_mode

        self.logger.info(f"MockRagflowClient 初始化成功 (test_mode={test_mode})")

    async def query_all_databases(self, query: str) -> List[RetrievalResult]:
        """
        查询所有知识库并返回合并后的结果

        根据测试模式返回不同的预设结果
        """
        self.logger.info(f"MockRagflowClient.query_all_databases: query='{query[:50]}...'")

        # 根据测试模式返回不同的结果
        if self.test_mode == "type0":
            # 返回低相似度结果，触发 type=0
            return [
                RetrievalResult(
                    database="park",
                    question="公园相关信息",
                    total_similarity=0.3,  # 低于阈值
                    keyword_similarity=0.2,
                    vector_similarity=0.1,
                )
            ]
        elif self.test_mode == "type1":
            # 返回高相似度结果，触发 type=1
            return [
                RetrievalResult(
                    database="park",
                    question="公园开放时间查询",
                    total_similarity=0.8,  # 高于阈值
                    keyword_similarity=0.6,
                    vector_similarity=0.7,
                )
            ]
        elif self.test_mode == "type2":
            # 返回高相似度结果，触发 type=2
            return [
                RetrievalResult(
                    database="sql_db",
                    question="查询用户数量",
                    total_similarity=0.9,  # 高于阈值
                    keyword_similarity=0.8,
                    vector_similarity=0.85,
                )
            ]
        else:
            return []


# ==================== 测试辅助函数 ====================

def create_mock_config(test_mode: str = "type0") -> tuple[LoggingConfig, RAGFlowConfig, IntentConfig]:
    """
    创建模拟配置

    Args:
        test_mode: 测试模式
    """
    (project_root / "test_logs").mkdir(parents=True, exist_ok=True)

    if test_mode == "type0":
        # Type 0 配置：park 映射到 type 0
        database_mapping = {"park": 0}
    elif test_mode == "type1":
        # Type 1 配置：park 映射到 type 1
        database_mapping = {"park": 1}
    elif test_mode == "type2":
        # Type 2 配置：sql_db 映射到 type 2
        database_mapping = {"sql_db": 2}
    else:
        database_mapping = {"park": 0}

    logging_config = LoggingConfig(
        log_dir=str(project_root / "test_logs"),
        max_bytes=10485760,
        backup_count=5,
        total_size_limit=524288000,
    )

    ragflow_config = RAGFlowConfig(
        api_key="mock_api_key",
        base_url="http://mock.ragflow.com",
        database_mapping=database_mapping,
        timeout=30,
        max_retries=3,
    )

    intent_config = IntentConfig(
        similarity_threshold=0.4,
        top_k_per_database=3,
        default_type=0,
    )

    return logging_config, ragflow_config, intent_config


async def run_test_scenario(scenario_name: str, query: str, user_id: str, test_mode: str):
    """
    运行测试场景

    Args:
        scenario_name: 场景名称
        query: 查询文本
        user_id: 用户 ID
        test_mode: 测试模式
    """
    print("\n" + "=" * 80)
    print(f"🧪 测试场景: {scenario_name}")
    print(f"   查询: '{query}'")
    print(f"   用户: {user_id}")
    print(f"   模式: {test_mode}")
    print("=" * 80 + "\n")

    try:
        # 1. 创建配置
        logging_config, ragflow_config, intent_config = create_mock_config(test_mode)
        print("✅ 配置创建成功")
        print(f"   - database_mapping: {ragflow_config.database_mapping}")
        print(f"   - similarity_threshold: {intent_config.similarity_threshold}")
        print(f"   - default_type: {intent_config.default_type}\n")

        # 2. 创建日志管理器
        log_manager = MockLogManager(logging_config)
        print("✅ 日志管理器创建成功\n")

        # 3. 创建 Mock RAGFlow 客户端
        ragflow_client = MockRagflowClient(ragflow_config, intent_config, log_manager, test_mode=test_mode)
        print("✅ MockRagflowClient 创建成功\n")

        # 4. 创建 IntentService
        intent_service = IntentService(log_manager, ragflow_client)
        print("✅ IntentService 创建成功\n")

        # 5. 调用 process_query 并收集流式响应
        print("📡 开始调用 process_query...\n")
        print("-" * 80)

        chunks = []
        async for chunk in intent_service.process_query(query, user_id):
            chunks.append(chunk)
            print(chunk, end="", flush=True)

        print("\n" + "-" * 80)
        print(f"\n✅ process_query 调用成功")
        print(f"   - 接收到 {len(chunks)} 个数据块")

        # 6. 分析响应
        print("\n📊 响应分析:")
        for i, chunk in enumerate(chunks, 1):
            if "event:" in chunk:
                event_line = chunk.split("\n")[0]
                print(f"   Chunk {i}: {event_line}")

        return True, chunks

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


# ==================== 主测试函数 ====================

async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🚀 IntentService.process_query 模拟测试")
    print("=" * 80)

    # 测试场景列表
    scenarios = [
        {
            "name": "场景 1: Type 0 - 语义类查询（无匹配）",
            "query": "你好",
            "user_id": "user_001",
            "mode": "type0",
            "expected": "无效指令#@#@#"
        },
        {
            "name": "场景 2: Type 1 - 明确指令类查询（有知识库标记）",
            "query": "[knowledgebase:park] 查询公园信息",
            "user_id": "user_002",
            "mode": "type1",
            "expected": "Dify Chat 未初始化"  # 因为没有初始化 Dify 客户端
        },
    ]

    results = []

    for scenario in scenarios:
        success, chunks = await run_test_scenario(
            scenario["name"],
            scenario["query"],
            scenario["user_id"],
            scenario["mode"]
        )
        results.append({
            "name": scenario["name"],
            "success": success,
            "chunks": chunks,
            "expected": scenario.get("expected")
        })

    # 测试总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r["success"])

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{i}. {result['name']}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请查看详细日志")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 测试发生未捕获异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
