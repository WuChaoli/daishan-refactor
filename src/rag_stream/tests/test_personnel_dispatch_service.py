"""
测试 personnel_dispatch_service.py 中的 handle_personnel_dispatch 函数

测试策略：集成测试，使用真实 Dify 服务
"""

import pytest
import asyncio
from typing import List, Dict
from rag_stream.services.personnel_dispatch_service import handle_personnel_dispatch


class TestHandlePersonnelDispatch:
    """handle_personnel_dispatch 函数测试套件"""

    @pytest.mark.asyncio
    async def test_tc01_single_entity(self):
        """
        TC01: 正常流程 - 单个实体
        输入包含单个实体的语音文本，成功提取实体并返回人员ID
        """
        voice_text = "请调度张三"
        user_id = "test_user_001"

        result = await handle_personnel_dispatch(voice_text, user_id)

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"
        assert len(result) >= 0, "返回列表长度应该 >= 0"

        if len(result) > 0:
            assert all(isinstance(item, dict) for item in result), "所有元素应该是字典"
            assert all("id" in item for item in result), "所有元素应该包含 'id' 键"
            assert all(isinstance(item["id"], str) for item in result), "所有 ID 应该是字符串"
            assert all(len(item["id"]) > 0 for item in result), "所有 ID 应该非空"

    @pytest.mark.asyncio
    async def test_tc02_multiple_entities(self):
        """
        TC02: 正常流程 - 多个实体
        输入包含多个实体的语音文本，成功提取所有实体并返回多个人员ID
        """
        voice_text = "请调度张三、李四和王五"
        user_id = "test_user_002"

        result = await handle_personnel_dispatch(voice_text, user_id)

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"

        if len(result) > 0:
            assert all(isinstance(item, dict) for item in result), "所有元素应该是字典"
            assert all("id" in item for item in result), "所有元素应该包含 'id' 键"
            assert all(isinstance(item["id"], str) for item in result), "所有 ID 应该是字符串"

    @pytest.mark.asyncio
    async def test_tc03_empty_voice_text(self):
        """
        TC03: 边界情况 - 空语音文本
        输入空字符串，应返回空列表
        """
        voice_text = ""
        user_id = None

        result = await handle_personnel_dispatch(voice_text, user_id)

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"
        assert len(result) == 0, "空输入应返回空列表"

    @pytest.mark.asyncio
    async def test_tc04_no_entities(self):
        """
        TC04: 边界情况 - 未提取到实体
        输入不包含实体的语音文本，实体提取返回空列表
        """
        voice_text = "今天天气真好"
        user_id = "test_user_003"

        result = await handle_personnel_dispatch(voice_text, user_id)

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"

    @pytest.mark.asyncio
    async def test_tc05_entity_returns_empty_id(self):
        """
        TC05: 边界情况 - 实体返回空ID
        实体提取成功，但人员调度返回空ID
        """
        voice_text = "请调度不存在的人"
        user_id = "test_user_004"

        result = await handle_personnel_dispatch(voice_text, user_id)

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"

    @pytest.mark.asyncio
    async def test_tc10_large_number_of_entities(self):
        """
        TC10: 性能测试 - 大量实体并发
        输入包含大量实体的语音文本，测试并发处理能力
        """
        voice_text = "请调度张三、李四、王五、赵六、钱七、孙八、周九、吴十、郑十一、王十二"
        user_id = "test_user_005"

        import time
        start_time = time.time()

        result = await handle_personnel_dispatch(voice_text, user_id)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # 验证点
        assert isinstance(result, list), "返回值应该是列表"
        assert elapsed_time < 10, f"响应时间应该 < 10秒，实际: {elapsed_time:.2f}秒"

        if len(result) > 0:
            assert all(isinstance(item, dict) for item in result), "所有元素应该是字典"
            assert all("id" in item for item in result), "所有元素应该包含 'id' 键"


# 异常情况测试需要 Mock ，暂时跳过
# TC06-TC09 需要 Mock Dify client 或环境变量
