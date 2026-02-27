"""
测试资源调度功能 - resource 意图识别
测试当 voiceText 明确指向具体资源时的流程
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目路径到 sys.path

from rag_stream.models.schemas import SourceDispatchRequest
from rag_stream.services.source_dispath_srvice import handle_source_dispatch
# LogManager removed - using log-manager
# settings import removed


class TestSourceDispatchResource:
    """资源调度测试类 - resource 意图"""

    def __init__(self):
        self.test_results = []
        self.test_results = []

    async def test_resource_intent(
        self,
        accident_id: str,
        source_type: str,
        voice_text: str,
        test_name: str
    ):
        """
        测试 resource 意图的资源调度

        Args:
            accident_id: 事故ID
            source_type: 资源类型
            voice_text: 语音文本（明确指向具体资源）
            test_name: 测试用例名称
        """
        print("\n" + "=" * 80)
        print(f"测试用例: {test_name}")
        print("=" * 80)

        # 创建请求
        request = SourceDispatchRequest(
            accidentId=accident_id,
            sourceType=source_type,
            voiceText=voice_text
        )

        print(f"事故ID: {request.accidentId}")
        print(f"资源类型: {request.sourceType}")
        print(f"语音文本: {request.voiceText}")
        print("-" * 80)

        try:
            # 调用服务函数
            result = await handle_source_dispatch(request)

            print("\n处理结果:")

            # 将结果转换为可序列化的格式
            serializable_result = None
            if result:
                if isinstance(result, list):
                    serializable_result = []
                    for item in result:
                        if hasattr(item, 'model_dump'):
                            serializable_result.append(item.model_dump())
                        elif hasattr(item, 'dict'):
                            serializable_result.append(item.dict())
                        else:
                            serializable_result.append(str(item))
                elif isinstance(result, dict):
                    serializable_result = result
                else:
                    if hasattr(result, 'model_dump'):
                        serializable_result = result.model_dump()
                    elif hasattr(result, 'dict'):
                        serializable_result = result.dict()
                    else:
                        serializable_result = str(result)

            print(json.dumps(serializable_result, ensure_ascii=False, indent=2))

            # 记录测试结果
            test_result = {
                "test_name": test_name,
                "accident_id": accident_id,
                "source_type": source_type,
                "voice_text": voice_text,
                "success": result is not None and len(result) > 0 if isinstance(result, (list, dict)) else result is not None,
                "result": serializable_result,
                "result_count": len(result) if isinstance(result, (list, dict)) else 1 if result else 0
            }
            self.test_results.append(test_result)

            if result:
                result_count = len(result) if isinstance(result, (list, dict)) else 1
                print(f"\n✓ 测试成功，返回 {result_count} 条结果")
                return True
            else:
                print(f"\n✗ 测试失败，未返回结果")
                return False

        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

            test_result = {
                "test_name": test_name,
                "accident_id": accident_id,
                "source_type": source_type,
                "voice_text": voice_text,
                "success": False,
                "error": str(e)
            }
            self.test_results.append(test_result)
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始测试 resource 意图识别")
        print("=" * 80)

        # 测试用的事故ID
        accident_id = "5896694001464688"

        # 测试场景列表 - 明确指向具体资源
        test_scenarios = [
            {
                "test_name": "查询酒精棉物资",
                "source_type": "emergencySupplies",
                "voice_text": "我需要酒精棉，请帮我查询有哪些酒精棉物资"
            },
            {
                "test_name": "查询测试企业物资1",
                "source_type": "emergencySupplies",
                "voice_text": "测试企业物资1还有库存吗"
            },
            {
                "test_name": "查询张三专家",
                "source_type": "emergencyExpert",
                "voice_text": "请联系张三专家"
            },
            {
                "test_name": "查询刘演翔专家",
                "source_type": "emergencyExpert",
                "voice_text": "刘演翔专家的联系方式是什么"
            },
            {
                "test_name": "查询世倍尔救援队",
                "source_type": "rescueTeam",
                "voice_text": "世倍尔救援队在哪里"
            },
            {
                "test_name": "查询岱山县第一人民医院",
                "source_type": "medicalInstitution",
                "voice_text": "岱山县第一人民医院的位置"
            },
            {
                "test_name": "查询岱西卫生院",
                "source_type": "medicalInstitution",
                "voice_text": "岱西卫生院能接收伤员吗"
            },
            {
                "test_name": "查询消防设施",
                "source_type": "fireFightingFacilities",
                "voice_text": "最近的消防设施在哪"
            },
            {
                "test_name": "查询避难场所",
                "source_type": "shelter",
                "voice_text": "附近有避难场所吗"
            },
            {
                "test_name": "查询救援机构",
                "source_type": "rescueOrganization",
                "voice_text": "救援机构的联系电话"
            }
        ]

        # 执行测试
        for scenario in test_scenarios:
            await self.test_resource_intent(
                accident_id=accident_id,
                source_type=scenario["source_type"],
                voice_text=scenario["voice_text"],
                test_name=scenario["test_name"]
            )

        # 输出测试总结
        self.print_test_summary()

    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success"))
        failed_tests = total_tests - successful_tests

        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {successful_tests / total_tests * 100:.1f}%")

        # 保存测试结果到文件
        result_file = Path(__file__).parent / "test_source_dispatch_resource_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {result_file}")
        print("=" * 80)


async def main():
    """主函数"""
    tester = TestSourceDispatchResource()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
