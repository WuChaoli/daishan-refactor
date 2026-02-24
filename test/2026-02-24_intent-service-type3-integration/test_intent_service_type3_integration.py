"""
IntentService Type3 集成测试

说明:
- 走完整链路: RagflowClient -> IntentService.process_query
- 不使用 mock
- 默认关闭,需显式设置环境变量 RUN_RAGFLOW_INTENT_INTEGRATION=1 后执行
"""

import os
import sys
import asyncio
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_STREAM_ROOT = PROJECT_ROOT / "src" / "rag_stream"
if str(RAG_STREAM_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_STREAM_ROOT))

from src.config.settings import settings
from src.services.intent_service import IntentService
from src.utils.ragflow_client import RagflowClient


TEST_QUERIES = [
    "园区地址在哪",
    "园区位置在哪",
    "园区负责人是谁",
    "园区安全负责人是谁",
    "园区负责人联系方式",
    "园区安全负责人联系方式",
    "园区经历了什么发展历程",
    "园区荣誉有哪些",
    "园区公共管廊长度",
    "园区有多少园区公共视频监控设备",
    "园区园区公共视频分别监控哪些区域",
    "园区有多少企业视频监控设备",
    "园区企业有多少监测指标传感器",
    "园区有哪些企业",
    "园区有几家规上企业",
    "园区有几家国高企业",
    "园区有几家绿色示范企业",
    "园区有几家单项冠军企业",
    "园区有几家专精特新企业",
    "园区今年工业总产值",
    "园区今年规上工业总产值",
    "园区今年亩均产值",
    "园区今年亩均税收",
    "园区规划面积",
    "园区基本信息",
    "园区某月规上工业产值同比增速",
    "园区某月风险走势情况",
    "某企业某月风险走势情况",
    "园区当前的风险分级管控情况",
    "园区近7日的隐患预警统计情况",
    "园区近1月的隐患预警统计情况",
    "园区近3月的隐患预警统计情况",
    "园区上周的双重预防机制运行效果如何",
    "园区隐患排查与整改情况如何",
    "园区实时的作业票预警情况？",
    "园区第三方人员有多少",
    "园区有哪些第三方单位",
    "某企业的详细信息",
    "园区有哪些企业涉及重大危险源",
    "园区有哪些企业涉及重点监管危险化工工艺",
]

EXPECTED_INTENT_TYPE = 3
RUN_FLAG = "RUN_RAGFLOW_INTENT_INTEGRATION"


@pytest.fixture(scope="session")
def intent_service() -> IntentService:
    if os.getenv(RUN_FLAG) != "1":
        pytest.skip(
            f"集成测试默认关闭,请设置 {RUN_FLAG}=1 后重试",
            allow_module_level=True,
        )

    if not settings.ragflow.base_url or not settings.ragflow.api_key:
        pytest.skip("RAGFlow 配置缺失(base_url/api_key)", allow_module_level=True)

    mapped_type = settings.ragflow.database_mapping.get("岱山-指令集-固定问题")
    assert str(mapped_type) == "3", (
        "配置不满足本用例前提: ragflow.database_mapping['岱山-指令集-固定问题'] 必须是 3"
    )

    ragflow_client = RagflowClient(settings.ragflow, settings.intent)
    return IntentService(ragflow_client=ragflow_client)


@pytest.mark.parametrize("query", TEST_QUERIES)
def test_queries_should_all_be_type3(query: str, intent_service: IntentService):
    result = asyncio.run(
        intent_service.process_query(query, user_id="intent-integration-test")
    )

    assert isinstance(result, dict), f"返回结果不是 dict: {result}"
    assert result.get("type") == EXPECTED_INTENT_TYPE, (
        f"问题[{query}] 期望 type={EXPECTED_INTENT_TYPE}, "
        f"实际 type={result.get('type')}, 全量结果={result}"
    )
