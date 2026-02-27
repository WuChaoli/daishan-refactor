"""测试 /api/general 聊天接口的测试文件"""
import json
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest
from fastapi.testclient import TestClient

# 导入 app 和路由函数
from rag_stream.main import app
from rag_stream.services.dify_service import should_use_dify


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestShouldUseDify:
    """测试 should_use_dify 函数"""

    def test_introduce_park(self):
        """测试'介绍园区'相关问题"""
        assert should_use_dify("介绍园区")
        assert should_use_dify("园区介绍")
        assert should_use_dify("介绍一下园区")
        assert should_use_dify("介绍一下化工园区")
        assert should_use_dify("园区情况怎么样")

    def test_park_safety_status(self):
        """测试园区安全状况相关问题"""
        assert should_use_dify("园区安全状况")
        assert should_use_dify("园区是否安全")
        assert should_use_dify("园区安全介绍")
        assert should_use_dify("介绍园区安全状况")

    def test_introduce_company(self):
        """测试企业介绍相关问题"""
        assert should_use_dify("介绍企业")
        assert should_use_dify("介绍公司")
        assert should_use_dify("企业介绍")
        assert should_use_dify("介绍一下浙江世倍尔新材料有限公司")

    def test_general_questions_not_match(self):
        """测试不匹配的通用问题"""
        assert not should_use_dify("你好")
        assert not should_use_dify("天气怎么样")
        assert not should_use_dify("怎么使用这个系统")
        assert not should_use_dify("法律法规查询")


class TestChatGeneralEndpointValidation:
    """测试 /api/general 端点的请求验证"""

    def test_post_api_general_missing_question(self, client):
        """测试缺少 question 字段的请求"""
        response = client.post(
            "/api/general",
            json={
                "user_id": "test_user_001",
                "stream": True,
            },
        )

        # Pydantic 验证应该失败
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data

    def test_post_api_general_empty_question(self, client):
        """测试空 question 的请求"""
        response = client.post(
            "/api/general",
            json={
                "question": "",
                "user_id": "test_user_001",
                "stream": True,
            },
        )

        # Pydantic 验证应该失败（min_length=1）
        assert response.status_code == 422

    def test_post_api_general_valid_with_user_id(self, client):
        """测试带 user_id 的有效请求 - 验证请求格式"""
        response = client.post(
            "/api/general",
            json={
                "question": "你好",
                "user_id": "test_user_123",
                "stream": True,
            },
        )

        # 请求格式应该通过验证（即使实际处理可能会失败）
        # 422 表示验证错误，200 表示成功，500 表示内部错误
        # 这里我们只确保不是请求格式错误
        assert response.status_code in [200, 500]

    def test_post_api_general_valid_without_user_id(self, client):
        """测试不带 user_id 的有效请求"""
        response = client.post(
            "/api/general",
            json={
                "question": "你好",
                "stream": True,
            },
        )

        # user_id 是可选的，所以应该通过验证
        assert response.status_code in [200, 500]

    def test_post_api_general_valid_with_session_id(self, client):
        """测试带 session_id 的有效请求"""
        response = client.post(
            "/api/general",
            json={
                "question": "你好",
                "session_id": "existing_session_123",
                "user_id": "test_user_001",
                "stream": True,
            },
        )

        # session_id 是可选的
        assert response.status_code in [200, 500]

    def test_post_api_general_valid_stream_false(self, client):
        """测试 stream=False 的有效请求"""
        response = client.post(
            "/api/general",
            json={
                "question": "你好",
                "user_id": "test_user_001",
                "stream": False,
            },
        )

        # stream 字段是可选的，默认为 True
        assert response.status_code in [200, 500]


class TestChatGeneralEdgeCases:
    """测试边界情况"""

    def test_very_long_question(self, client):
        """测试非常长的问题"""
        long_question = "这是一个非常长的问题，" * 1000
        response = client.post(
            "/api/general",
            json={
                "question": long_question,
                "user_id": "test_user_001",
            },
        )
        # 应该能接受长问题（验证通过）
        assert response.status_code in [200, 500]

    def test_special_characters_in_question(self, client):
        """测试问题中包含特殊字符"""
        special_questions = [
            "问题包含符号！@#$%^&*()",
            "问题包含中文和 English 混合",
            "问题包含\n换行符",
            "问题包含\t制表符",
        ]

        for question in special_questions:
            response = client.post(
                "/api/general",
                json={
                    "question": question,
                    "user_id": "test_user_001",
                },
            )
            # 特殊字符应该能被正确接受（验证通过）
            assert response.status_code in [200, 500]

    def test_unicode_question(self, client):
        """测试 Unicode 字符"""
        unicode_questions = [
            "Hello 世界 🌍",
            "问题包含表情符号 😊",
            "测试阿拉伯语 مرحبا",
            "测试日语 こんにちは",
        ]

        for question in unicode_questions:
            response = client.post(
                "/api/general",
                json={
                    "question": question,
                    "user_id": "test_user_001",
                },
            )
            assert response.status_code in [200, 500]

    def test_question_with_quotes_and_backslashes(self, client):
        """测试包含引号和反斜杠的问题"""
        special_questions = [
            "测试包含'单引号'的问题",
            '测试包含"双引号"的问题',
            "测试包含\\反斜杠\\的问题",
            "测试包含`反引号`的问题",
        ]

        for question in special_questions:
            response = client.post(
                "/api/general",
                json={
                    "question": question,
                    "user_id": "test_user_001",
                },
            )
            assert response.status_code in [200, 500]


class TestChatGeneralDifyRouting:
    """测试 Dify 路由逻辑"""

    def test_dify_question_routes_to_dify(self):
        """测试匹配 Dify 模式的问题应该路由到 Dify"""
        dify_questions = [
            "介绍园区",
            "园区介绍",
            "介绍一下园区",
            "园区情况",
            "园区信息",
            "介绍企业",
            "介绍公司",
            "企业介绍",
            "介绍园区安全",
            "园区安全状况",
            "园区是否安全",
            "园区安全介绍",
        ]

        for question in dify_questions:
            assert should_use_dify(question), f"问题 '{question}' 应该匹配 Dify"

    def test_rag_question_routes_to_rag(self):
        """测试不匹配 Dify 模式的问题应该路由到 RAG"""
        rag_questions = [
            "你好",
            "天气怎么样",
            "如何使用系统",
            "查询法律法规",
            "标准规范查询",
            "应急知识",
            "事故案例",
            "MSDS查询",
            "标准政策",
        ]

        for question in rag_questions:
            assert not should_use_dify(question), f"问题 '{question}' 不应该匹配 Dify"


class TestChatGeneralRequestHeaders:
    """测试请求头"""

    def test_request_with_custom_headers(self, client):
        """测试带自定义请求头的请求"""
        response = client.post(
            "/api/general",
            json={
                "question": "你好",
                "user_id": "test_user_001",
            },
            headers={
                "X-Custom-Header": "custom_value",
                "X-Request-ID": "12345",
            },
        )
        # 请求头不应该影响验证
        assert response.status_code in [200, 500]


class TestChatGeneralOtherEndpoints:
    """测试其他端点是否正常工作（可选的完整性检查）"""

    def test_health_check_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        # 健康检查应该返回 200
        assert response.status_code == 200

    def test_categories_endpoint(self, client):
        """测试类别端点"""
        response = client.get("/api/categories")
        # 类别端点应该返回 200
        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "categories" in response_data["data"]


# 参数化测试：所有 Dify 问题都应该匹配
@pytest.mark.parametrize(
    "question",
    [
        "介绍园区",
        "园区介绍",
        "介绍一下园区",
        "园区情况",
        "园区信息",
        "介绍企业",
        "介绍公司",
    ],
)
def test_all_dify_questions_match(question):
    """参数化测试：所有 Dify 问题都应该匹配"""
    assert should_use_dify(question)


# 参数化测试：所有 RAG 问题都不应该匹配 Dify
@pytest.mark.parametrize(
    "question",
    [
        "你好",
        "天气怎么样",
        "如何使用系统",
        "查询法律法规",
        "标准规范查询",
    ],
)
def test_all_rag_questions_not_match(question):
    """参数化测试：所有 RAG 问题都不应该匹配 Dify"""
    assert not should_use_dify(question)


# 参数化测试：请求验证
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        # 有效请求
        (
            {"question": "你好", "user_id": "test", "stream": True},
            [200, 500],
        ),
        # 缺少 question
        (
            {"user_id": "test", "stream": True},
            422,
        ),
        # 空 question
        (
            {"question": "", "user_id": "test"},
            422,
        ),
        # 只有 question（其他字段可选）
        (
            {"question": "你好"},
            [200, 500],
        ),
    ],
)
def test_request_validation(client, payload, expected_status):
    """参数化测试：请求验证"""
    response = client.post("/api/general", json=payload)

    if isinstance(expected_status, list):
        assert response.status_code in expected_status
    else:
        assert response.status_code == expected_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
