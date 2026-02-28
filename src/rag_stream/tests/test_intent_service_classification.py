"""IntentService 分类驱动检索测试

测试分类驱动检索逻辑：
1. 高置信度时过滤 database_mapping
2. 低置信度时保持全量检索（向后兼容）
3. 降级时保持全量检索
4. 分类器禁用时保持全量检索
"""

import dataclasses
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.services.intent_service.base_intent_service import IntentRecognizerSettings
from src.services.intent_service.intent_service import IntentService
from src.utils.intent_classifier import ClassificationResult


class TestIntentServiceClassification:
    """IntentService 分类驱动检索测试类"""

    @pytest.fixture
    def mock_ragflow_client(self):
        """Mock RAGFlow 客户端"""
        return MagicMock()

    @pytest.fixture
    def intent_service(self, mock_ragflow_client):
        """创建 IntentService 实例"""
        service = IntentService(ragflow_client=mock_ragflow_client)
        return service

    @pytest.fixture
    def full_database_mapping(self):
        """完整的 database_mapping"""
        return {
            "岱山-指令集": 1,
            "岱山-数据库问题": 2,
            "岱山-指令集-固定问题": 3,
        }

    def test_high_confidence_filters_database_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 1: 高置信度时过滤 database_mapping 为对应类型"""
        # Arrange: Mock classifier 返回高置信度分类结果
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=1,  # 岱山-指令集
            confidence=0.85,
            raw_response='{"type": 1, "confidence": 0.85}',
            degraded=False,
        )
        intent_service._intent_classifier = mock_classifier

        # Mock settings
        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                # Act
                result = intent_service._load_process_settings(
                    text_input="如何执行岱山指令集"
                )

        # Assert: 只保留 type_id=1 的数据库
        assert result.database_mapping == {"岱山-指令集": 1}
        mock_classifier.classify.assert_called_once_with("如何执行岱山指令集")

    def test_low_confidence_returns_full_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 2: 低置信度时返回完整的 database_mapping"""
        # Arrange: Mock classifier 返回低置信度分类结果
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=1,
            confidence=0.5,  # 低于阈值 0.7
            raw_response='{"type": 1, "confidence": 0.5}',
            degraded=False,
        )
        intent_service._intent_classifier = mock_classifier

        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                with patch(
                    "src.services.intent_service.intent_service.marker"
                ) as mock_marker:
                    # Act
                    result = intent_service._load_process_settings(
                        text_input="如何执行岱山指令集"
                    )

        # Assert: 返回完整的 mapping
        assert result.database_mapping == full_database_mapping
        # 验证 marker 被调用
        mock_marker.assert_called_once()
        call_args = mock_marker.call_args
        assert call_args[0][0] == "classifier.low_confidence_fallback"

    def test_degraded_classification_returns_full_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 3: 降级分类时返回完整的 database_mapping"""
        # Arrange: Mock classifier 返回降级结果
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=0,
            confidence=0.0,
            raw_response="",
            degraded=True,
        )
        intent_service._intent_classifier = mock_classifier

        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                with patch(
                    "src.services.intent_service.intent_service.marker"
                ) as mock_marker:
                    # Act
                    result = intent_service._load_process_settings(
                        text_input="如何执行岱山指令集"
                    )

        # Assert: 返回完整的 mapping
        assert result.database_mapping == full_database_mapping
        # 验证降级 marker 被调用
        mock_marker.assert_called_once()
        call_args = mock_marker.call_args
        assert call_args[0][0] == "classifier.degraded_fallback"

    def test_disabled_classifier_returns_full_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 4: 分类器禁用时返回完整的 database_mapping"""
        # Arrange: 设置分类器为 None
        intent_service._intent_classifier = None

        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )

            # Act
            result = intent_service._load_process_settings(
                text_input="如何执行岱山指令集"
            )

        # Assert: 返回完整的 mapping
        assert result.database_mapping == full_database_mapping

    def test_confidence_threshold_respected(
        self, intent_service, full_database_mapping
    ):
        """Test 5: 置信度等于阈值时应用过滤"""
        # Arrange: Mock classifier 返回恰好等于阈值的置信度
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=2,  # 岱山-数据库问题
            confidence=0.7,  # 等于阈值
            raw_response='{"type": 2, "confidence": 0.7}',
            degraded=False,
        )
        intent_service._intent_classifier = mock_classifier

        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                # Act
                result = intent_service._load_process_settings(
                    text_input="查询企业信息"
                )

        # Assert: 过滤为 type_id=2 的数据库
        assert result.database_mapping == {"岱山-数据库问题": 2}

    def test_type_id_mapping_correctness(
        self, intent_service, full_database_mapping
    ):
        """Test 6: type_id 映射正确性验证"""
        # Arrange: Mock classifier 返回 type_id=3
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=3,  # 岱山-指令集-固定问题
            confidence=0.8,
            raw_response='{"type": 3, "confidence": 0.8}',
            degraded=False,
        )
        intent_service._intent_classifier = mock_classifier

        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                # Act
                result = intent_service._load_process_settings(
                    text_input="固定问题示例"
                )

        # Assert: 过滤为 type_id=3 的数据库
        assert result.database_mapping == {"岱山-指令集-固定问题": 3}

    def test_no_text_input_returns_full_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 7: 无 text_input 时返回完整的 database_mapping（向后兼容）"""
        # Arrange: 有分类器但无 text_input
        mock_classifier = MagicMock()
        intent_service._intent_classifier = mock_classifier

        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )

            # Act: 不传 text_input
            result = intent_service._load_process_settings()

        # Assert: 返回完整的 mapping，不调用 classify
        assert result.database_mapping == full_database_mapping
        mock_classifier.classify.assert_not_called()

    def test_no_matching_database_returns_full_mapping(
        self, intent_service, full_database_mapping
    ):
        """Test 8: 无匹配数据库时返回完整的 database_mapping（防御性编程）"""
        # Arrange: Mock classifier 返回不存在的 type_id
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(
            type_id=99,  # 不存在的数据库类型
            confidence=0.85,
            raw_response='{"type": 99, "confidence": 0.85}',
            degraded=False,
        )
        intent_service._intent_classifier = mock_classifier

        mock_config = MagicMock()
        mock_config.confidence_threshold = 0.7
        with patch.object(
            intent_service, "_load_intent_recognizer_settings"
        ) as mock_load_settings:
            mock_load_settings.return_value = IntentRecognizerSettings(
                database_mapping=full_database_mapping,
                similarity_threshold=0.5,
                top_k=10,
                default_type=0,
            )
            with patch(
                "src.services.intent_service.intent_service.settings"
            ) as mock_settings:
                mock_settings.intent_classification = mock_config

                # Act
                result = intent_service._load_process_settings(
                    text_input="未知类型问题"
                )

        # Assert: 返回完整的 mapping（防御性编程）
        assert result.database_mapping == full_database_mapping
