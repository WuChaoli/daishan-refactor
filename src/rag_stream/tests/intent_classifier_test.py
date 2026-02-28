"""意图分类降级路径单元测试。"""

from unittest.mock import Mock, patch

import pytest

from src.utils.intent_classifier import (
    ClassificationResult,
    IntentClassifier,
)
from src.config.settings import IntentClassificationConfig


class TestDegradationPaths:
    """降级路径测试。"""

    @pytest.fixture
    def config(self):
        """测试配置。"""
        return IntentClassificationConfig(
            enabled=True,
            api_key="test_key",
            base_url="http://test.com/v1",
            model="test-model",
            timeout=1,
            temperature=0.0,
            confidence_threshold=0.5,
        )

    @pytest.fixture
    def classifier(self, config):
        """测试分类器。"""
        return IntentClassifier(config)

    def test_timeout_degradation(self, classifier):
        """测试超时降级。"""
        query = "测试查询"

        # Mock 永久阻塞
        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()

            def blocking_call(*args, **kwargs):
                import time

                time.sleep(10)  # 阻塞 10 秒

            mock_client.chat.completions.create = blocking_call
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True
            assert result.type_id == 0
            assert result.confidence == 0.0
            assert result.raw_response == ""

    def test_api_error_degradation(self, classifier):
        """测试 API 错误降级。"""
        query = "测试查询"

        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()

            # 模拟 API 异常
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True
            assert result.type_id == 0
            assert result.confidence == 0.0

    def test_invalid_json_degradation(self, classifier):
        """测试无效 JSON 降级。"""
        query = "测试查询"

        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_message = Mock()

            # 返回非 JSON 文本
            mock_message.content = "这不是 JSON 格式"
            mock_response.choices = [Mock(message=mock_message)]
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True
            assert result.type_id == 0
            assert result.confidence == 0.0

    def test_invalid_type_id_degradation(self, classifier):
        """测试无效 type_id 降级。"""
        query = "测试查询"

        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_message = Mock()

            # 返回无效 type_id
            mock_message.content = '{"type": 99, "confidence": 0.8}'
            mock_response.choices = [Mock(message=mock_message)]
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True
            assert result.type_id == 0

    def test_invalid_confidence_degradation(self, classifier):
        """测试无效 confidence 降级。"""
        query = "测试查询"

        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_message = Mock()

            # 返回无效 confidence
            mock_message.content = '{"type": 1, "confidence": 1.5}'
            mock_response.choices = [Mock(message=mock_message)]
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True
            assert result.type_id == 0

    def test_empty_response_degradation(self, classifier):
        """测试空响应降级。"""
        query = "测试查询"

        with patch.object(classifier, "_get_client") as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()

            # 返回空响应
            mock_response.choices = []
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = classifier.classify(query)

            # 验证降级
            assert result.degraded is True

    def test_disabled_feature_degradation(self, config):
        """测试功能禁用降级。"""
        config.enabled = False
        classifier = IntentClassifier(config)

        result = classifier.classify("测试查询")

        # 验证降级
        assert result.degraded is True
        assert result.type_id == 0

    def test_invalid_input_degradation(self, classifier):
        """测试无效输入降级。"""
        # 测试非字符串输入
        result1 = classifier.classify(123)
        assert result1.degraded is True

        # 测试空字符串
        result2 = classifier.classify("")
        assert result2.degraded is True

        # 测试空白字符串
        result3 = classifier.classify("   ")
        assert result3.degraded is True
