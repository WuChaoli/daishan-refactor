"""
猜你想问功能 - 单元测试

测试guess_questions_service模块的各个处理函数
"""
import pytest
from src.rag_stream.src.services.guess_questions_service import (
    process_type1,
    process_type2,
    process_other_types
)


class TestProcessType1:
    """测试类别1处理函数"""

    def test_process_type1_returns_fixed_questions(self):
        """测试用例1.1: 正常返回固定问题"""
        intent_result = {
            "type": 1,
            "query": "附近有哪些应急避难所？",
            "results": [],
            "similarity": 0.85,
            "database": "岱山-指令集"
        }

        result = process_type1(intent_result)

        # 验证返回列表长度为3
        assert len(result) == 3

        # 验证每个元素包含guess_your_question字段
        for item in result:
            assert "guess_your_question" in item
            assert isinstance(item["guess_your_question"], str)
            assert len(item["guess_your_question"]) > 0

    def test_process_type1_question_content(self):
        """测试用例1.2: 固定问题内容验证"""
        intent_result = {
            "type": 1,
            "query": "附近有哪些应急避难所？",
            "results": [],
            "similarity": 0.85,
            "database": "岱山-指令集"
        }

        result = process_type1(intent_result)

        # 验证固定问题内容
        assert result[0]["guess_your_question"] == "如何查询应急资源？"
        assert result[1]["guess_your_question"] == "如何调度救援队伍？"
        assert result[2]["guess_your_question"] == "如何查看事故信息？"


class TestProcessType2:
    """测试类别2处理函数"""

    def test_process_type2_extracts_2_to_4(self):
        """测试用例2.1: 正常提取第2-4个结果"""
        intent_result = {
            "type": 2,
            "query": "岱山有多少家化工企业？",
            "results": [
                {"question": "问题1", "similarity": 0.95},
                {"question": "问题2", "similarity": 0.90},
                {"question": "问题3", "similarity": 0.85},
                {"question": "问题4", "similarity": 0.80},
                {"question": "问题5", "similarity": 0.75}
            ],
            "similarity": 0.95,
            "database": "岱山-数据库问题"
        }

        result = process_type2(intent_result)

        # 验证返回列表长度为3
        assert len(result) == 3

        # 验证提取的是索引1、2、3的元素（第2-4个）
        assert result[0]["guess_your_question"] == "问题2"
        assert result[1]["guess_your_question"] == "问题3"
        assert result[2]["guess_your_question"] == "问题4"

    def test_process_type2_with_3_results(self):
        """测试用例2.2: 结果只有3个元素"""
        intent_result = {
            "type": 2,
            "results": [
                {"question": "问题1", "similarity": 0.95},
                {"question": "问题2", "similarity": 0.90},
                {"question": "问题3", "similarity": 0.85}
            ]
        }

        result = process_type2(intent_result)

        # 验证返回列表长度为2
        assert len(result) == 2

        # 验证提取索引1、2的元素
        assert result[0]["guess_your_question"] == "问题2"
        assert result[1]["guess_your_question"] == "问题3"

    def test_process_type2_with_2_results(self):
        """测试用例2.3: 结果只有2个元素"""
        intent_result = {
            "type": 2,
            "results": [
                {"question": "问题1", "similarity": 0.95},
                {"question": "问题2", "similarity": 0.90}
            ]
        }

        result = process_type2(intent_result)

        # 验证返回列表长度为1
        assert len(result) == 1

        # 验证提取索引1的元素
        assert result[0]["guess_your_question"] == "问题2"

    def test_process_type2_with_1_result(self):
        """测试用例2.4: 结果只有1个元素"""
        intent_result = {
            "type": 2,
            "results": [
                {"question": "问题1", "similarity": 0.95}
            ]
        }

        result = process_type2(intent_result)

        # 验证返回空列表
        assert len(result) == 0
        assert result == []

    def test_process_type2_with_empty_results(self):
        """测试用例2.5: 结果为空列表"""
        intent_result = {
            "type": 2,
            "results": []
        }

        result = process_type2(intent_result)

        # 验证返回空列表
        assert len(result) == 0
        assert result == []


class TestProcessOtherTypes:
    """测试其他类别处理函数"""

    def test_process_type0_returns_empty(self):
        """测试用例3.1: type=0返回空列表"""
        intent_result = {
            "type": 0,
            "query": "测试问题",
            "results": [],
            "similarity": 0.0,
            "database": ""
        }

        result = process_other_types(intent_result)

        # 验证返回空列表
        assert len(result) == 0
        assert result == []

    def test_process_unknown_type_returns_empty(self):
        """测试用例3.2: 未知type返回空列表"""
        intent_result = {
            "type": 99,
            "query": "测试问题",
            "results": [],
            "similarity": 0.0,
            "database": ""
        }

        result = process_other_types(intent_result)

        # 验证返回空列表
        assert len(result) == 0
        assert result == []
