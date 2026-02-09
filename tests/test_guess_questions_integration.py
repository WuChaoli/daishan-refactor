"""
猜你想问功能 - 集成测试

测试API接口与IntentService的集成
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
import sys
from pathlib import Path

# 添加src/rag_stream到路径
rag_stream_path = Path(__file__).parent.parent / "src" / "rag_stream"
if str(rag_stream_path) not in sys.path:
    sys.path.insert(0, str(rag_stream_path))

from main import app

# 配置pytest-asyncio
pytestmark = pytest.mark.asyncio


class TestGuessQuestionsAPI:
    """测试猜你想问API接口"""

    async def test_guess_questions_type1_integration(self):
        """测试用例4.1: 类别1完整流程"""
        # Mock IntentService.process_query() 返回type=1的结果
        mock_intent_result = {
            "type": 1,
            "query": "附近有哪些应急避难所？",
            "results": [],
            "similarity": 0.85,
            "database": "岱山-指令集"
        }

        with patch('src.rag_stream.src.services.intent_service.IntentService.process_query',
                   new_callable=AsyncMock, return_value=mock_intent_result):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/guess-questions",
                    json={"question": "附近有哪些应急避难所？"}
                )

        # 验证HTTP状态码
        assert response.status_code == 200

        # 验证响应格式
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data

        # 验证响应内容
        assert data["code"] == 0
        assert data["message"] == "成功"
        assert len(data["data"]) == 3

    async def test_guess_questions_type2_integration(self):
        """测试用例4.2: 类别2完整流程"""
        # Mock IntentService.process_query() 返回type=2的结果
        mock_intent_result = {
            "type": 2,
            "query": "岱山有多少家化工企业？",
            "results": [
                {"question": "岱山化工企业总数是多少？", "similarity": 0.95},
                {"question": "岱山有多少家危化品企业？", "similarity": 0.90},
                {"question": "岱山化工园区的企业分布情况？", "similarity": 0.85},
                {"question": "岱山重大危险源有哪些？", "similarity": 0.80},
                {"question": "岱山化工企业的安全管理情况？", "similarity": 0.75}
            ],
            "similarity": 0.95,
            "database": "岱山-数据库问题"
        }

        with patch('src.rag_stream.src.services.intent_service.IntentService.process_query',
                   new_callable=AsyncMock, return_value=mock_intent_result):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/guess-questions",
                    json={"question": "岱山有多少家化工企业？"}
                )

        # 验证HTTP状态码
        assert response.status_code == 200

        # 验证响应格式
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 3

        # 验证提取的是第2-4个问题
        assert data["data"][0]["guess_your_question"] == "岱山有多少家危化品企业？"
        assert data["data"][1]["guess_your_question"] == "岱山化工园区的企业分布情况？"
        assert data["data"][2]["guess_your_question"] == "岱山重大危险源有哪些？"

    async def test_guess_questions_empty_question(self):
        """测试用例4.3: 空问题输入"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/guess-questions",
                json={"question": ""}
            )

        # 验证返回错误响应
        data = response.json()
        assert data["code"] == 1
        assert "不能为空" in data["message"]

    async def test_guess_questions_long_question(self):
        """测试用例4.4: 问题过长"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/guess-questions",
                json={"question": "a" * 1001}
            )

        # 验证返回错误响应
        data = response.json()
        assert data["code"] == 1
        assert "长度" in data["message"]

    async def test_guess_questions_intent_service_error(self):
        """测试用例4.5: IntentService调用失败"""
        # Mock IntentService.process_query() 抛出异常
        with patch('src.rag_stream.src.services.intent_service.IntentService.process_query',
                   new_callable=AsyncMock, side_effect=Exception("服务异常")):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/guess-questions",
                    json={"question": "测试问题"}
                )

        # 验证返回错误响应
        data = response.json()
        assert data["code"] == 1
        assert "不可用" in data["message"] or "异常" in data["message"]

    async def test_guess_questions_invalid_data_format(self):
        """测试用例4.6: 数据格式错误"""
        # Mock IntentService.process_query() 返回格式错误的数据
        mock_invalid_result = {
            "type": 2,
            "results": "invalid_format"  # 应该是列表，但返回字符串
        }

        with patch('src.rag_stream.src.services.intent_service.IntentService.process_query',
                   new_callable=AsyncMock, return_value=mock_invalid_result):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/guess-questions",
                    json={"question": "测试问题"}
                )

        # 验证返回错误响应
        data = response.json()
        assert data["code"] == 1
        assert "格式" in data["message"] or "错误" in data["message"]
