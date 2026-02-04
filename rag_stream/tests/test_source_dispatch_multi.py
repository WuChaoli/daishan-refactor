"""
多场景资源调度测试
测试不同资源类型和语音文本的组合
"""
import asyncio
import sys
import os

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.schemas import SourceDispatchRequest, SourceType
from src.services.source_dispath_srvice import handle_source_dispatch
from src.services.log_manager import LogManager
from src.config.settings import settings


# 测试用例配置
TEST_CASES = [
    {
        "name": "消防设施 - 查询污水处理厂",
        "accident_id": "5844749472101664",
        "source_type": SourceType.消防设施,
        "voice_text": "最近的污水处理厂在哪里"
    },
    {
        "name": "救援队伍 - 调度消防队",
        "accident_id": "5844749472101664",
        "source_type": SourceType.救援队伍,
        "voice_text": "调度消防队到现场"
    },
    {
        "name": "应急专家 - 需要化工专家",
        "accident_id": "5844749472101664",
        "source_type": SourceType.应急专家,
        "voice_text": "需要化工专家支援"
    },
    {
        "name": "医疗机构 - 查找最近医院",
        "accident_id": "5844749472101664",
        "source_type": SourceType.医疗机构,
        "voice_text": "最近的医院在哪里"
    },
    {
        "name": "避难场所 - 疏散点位置",
        "accident_id": "5844749472101664",
        "source_type": SourceType.避难场所,
        "voice_text": "附近的避难场所"
    },
    {
        "name": "应急物资 - 防护装备",
        "accident_id": "5844749472101664",
        "source_type": SourceType.应急物资,
        "voice_text": "需要防护装备和防毒面具"
    },
    {
        "name": "救援机构 - 调度救援力量",
        "accident_id": "5844749472101664",
        "source_type": SourceType.救援机构,
        "voice_text": "调度救援机构"
    },
    {
        "name": "防护目标 - 周边重点目标",
        "accident_id": "5844749472101664",
        "source_type": SourceType.防护目标,
        "voice_text": "周边有哪些重点防护目标"
    }
]


async def run_single_test(test_case: dict, log_manager: LogManager):
    """运行单个测试用例"""
    print("\n" + "=" * 80)
    print(f"测试: {test_case['name']}")
    print("=" * 80)
    print(f"事故ID: {test_case['accident_id']}")
    print(f"资源类型: {test_case['source_type']}")
    print(f"语音文本: {test_case['voice_text']}")
    print("-" * 80)

    # 创建请求
    request = SourceDispatchRequest(
        accidentId=test_case['accident_id'],
        sourceType=test_case['source_type'],
        voiceText=test_case['voice_text']
    )

    try:
        # 调用服务函数
        result = await handle_source_dispatch(request, log_manager)

        print(f"\n✅ 测试成功")
        print(f"返回类型: {type(result)}")
        print(f"结果数量: {len(result)}")

        if result:
            print("\n资源列表:")
            for idx, resource in enumerate(result, 1):
                print(f"  资源 {idx}: {resource}")
        else:
            print("\n⚠️  未找到资源或处理失败")

        return True, len(result)

    except Exception as e:
        print(f"\n❌ 测试失败")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def run_all_tests():
    """运行所有测试用例"""
    log_manager = LogManager(settings.logging)

    print("\n" + "=" * 80)
    print("开始多场景资源调度测试")
    print(f"测试用例数量: {len(TEST_CASES)}")
    print("=" * 80)

    results = []
    for test_case in TEST_CASES:
        success, count = await run_single_test(test_case, log_manager)
        results.append({
            "name": test_case['name'],
            "success": success,
            "count": count
        })
        # 每个测试之间暂停一下
        await asyncio.sleep(1)

    # 打印汇总结果
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)

    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)

    print(f"\n总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count / total_count * 100:.1f}%")

    print("\n详细结果:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name']}: {result['count']} 个资源")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
