"""
测试资源调度功能
"""
import asyncio
import sys
import os
import pytest

# 添加项目路径到 sys.path
# 添加 rag_stream 目录（用于导入 src 包）

from rag_stream.models.schemas import SourceDispatchRequest
from rag_stream.services.source_dispath_srvice import handle_source_dispatch


@pytest.mark.asyncio
async def test_source_dispatch():
    """测试资源调度功能"""

    # 创建测试请求
    request = SourceDispatchRequest(
        accidentId="5844749472101664",
        sourceType="fireFightingFacilities",
        voiceText="最近的污水处理厂在哪里"
    )

    print("=" * 60)
    print("测试资源调度功能")
    print("=" * 60)
    print(f"事故ID: {request.accidentId}")
    print(f"资源类型: {request.sourceType}")
    print(f"语音文本: {request.voiceText}")
    print("-" * 60)

    try:
        # 调用服务函数
        result = await handle_source_dispatch(request)

        print("\n处理结果:")
        print(f"返回类型: {type(result)}")
        print(f"结果数量: {len(result)}")

        if result:
            print("\n资源列表:")
            for idx, resource in enumerate(result, 1):
                print(f"\n资源 {idx}:")
                for key, value in resource.items():
                    print(f"  {key}: {value}")
        else:
            print("\n未找到资源或处理失败")

        print("=" * 60)
        print("测试完成")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def test_solid_resource_instruction():
    """测试固体资源指令功能（通过handle_source_dispatch）"""

    # 创建测试请求,使用会触发resource意图的语音文本
    request = SourceDispatchRequest(
        accidentId="5844749472101664",
        sourceType="fireFightingFacilities",
        voiceText="调度消防车、救护车到现场"
    )

    print("=" * 60)
    print("测试固体资源指令功能")
    print("=" * 60)
    print(f"事故ID: {request.accidentId}")
    print(f"资源类型: {request.sourceType}")
    print(f"语音文本: {request.voiceText}")
    print("-" * 60)

    try:
        result = await handle_source_dispatch(request)

        print("\n处理结果:")
        print(f"结果: {result}")

        print("=" * 60)
        print("测试完成")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "solid":
        asyncio.run(test_solid_resource_instruction())
    else:
        asyncio.run(test_source_dispatch())