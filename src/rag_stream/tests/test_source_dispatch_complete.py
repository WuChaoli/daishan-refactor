"""
完整测试资源调度功能 - source_dispatch 函数
测试不同的 accidentId 和 sourceType 组合
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.schemas import SourceDispatchRequest
from src.services.source_dispath_srvice import handle_source_dispatch
# LogManager removed - using log-manager
# settings import removed


class TestSourceDispatch:
    """资源调度测试类"""

    def __init__(self):
        self.test_results = []
        self.test_results = []

    async def test_accident_id_query(self, accident_id: str):
        """
        测试事故ID查询

        Args:
            accident_id: 事故ID
        """
        print("\n" + "=" * 80)
        print(f"测试事故ID查询: {accident_id}")
        print("=" * 80)

        # 导入 Server 类
        from DaiShanSQL import Server

        # 构建 SQL 查询
        sql = f"""
        SELECT ID, ACCIDENT_NAME, TO_CHAR(COORDINATE) AS COORDINATE,
               HAZARDOUS_CHEMICALS, ACCIDENT_OVERVIEW
        FROM IPARK_AE_ACCIDENT_EVENT
        WHERE ID = {accident_id}
        """

        print(f"执行 SQL: {sql.strip()}")

        try:
            server = Server()
            result = server.QueryBySQL(sql)

            print("\n查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # 验证结果
            if isinstance(result, dict):
                data_list = result.get('data', [])
                if data_list and len(data_list) > 0:
                    print(f"\n✓ 成功查询到事故数据")
                    row = data_list[0]
                    print(f"  事故名称: {row.get('ACCIDENT_NAME')}")
                    print(f"  坐标: {row.get('COORDINATE')}")
                    print(f"  危化品: {row.get('HAZARDOUS_CHEMICALS')}")
                    return True
                else:
                    print(f"\n✗ 未找到事故ID为 {accident_id} 的数据")
                    return False
            else:
                print(f"\n✗ 查询结果格式异常")
                return False

        except Exception as e:
            print(f"\n✗ 查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_source_dispatch_by_type(
        self,
        accident_id: str,
        source_type: str,
        voice_text: str
    ):
        """
        测试指定资源类型的调度

        Args:
            accident_id: 事故ID
            source_type: 资源类型
            voice_text: 语音文本
        """
        print("\n" + "=" * 80)
        print(f"测试资源调度: {source_type}")
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
                    # 如果是列表，尝试将每个元素转换为字典
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
                    # 尝试转换为字典
                    if hasattr(result, 'model_dump'):
                        serializable_result = result.model_dump()
                    elif hasattr(result, 'dict'):
                        serializable_result = result.dict()
                    else:
                        serializable_result = str(result)

            print(json.dumps(serializable_result, ensure_ascii=False, indent=2))

            # 记录测试结果
            test_result = {
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
        print("开始完整测试 source_dispatch 函数")
        print("=" * 80)

        # 测试用的事故ID（从测试文件中获取）
        test_accident_ids = [
            "5896694001464688",  # 从 test_query_by_sql.py 中获取
            "5844749472101664",  # 从 test_source_dispatch.py 中获取
        ]

        # 1. 测试事故ID查询
        print("\n" + "=" * 80)
        print("第一步: 测试事故ID查询")
        print("=" * 80)

        for accident_id in test_accident_ids:
            await self.test_accident_id_query(accident_id)

        # 2. 测试不同资源类型的调度
        print("\n" + "=" * 80)
        print("第二步: 测试不同资源类型的调度")
        print("=" * 80)

        # 使用第一个有效的事故ID
        accident_id = test_accident_ids[0]

        # 测试场景列表
        test_scenarios = [
            {
                "source_type": "emergencySupplies",
                "voice_text": "需要调度应急物资到事故现场"
            },
            {
                "source_type": "rescueTeam",
                "voice_text": "需要调度救援队伍支援"
            },
            {
                "source_type": "emergencyExpert",
                "voice_text": "需要应急专家指导"
            },
            {
                "source_type": "fireFightingFacilities",
                "voice_text": "最近的消防设施在哪里"
            },
            {
                "source_type": "shelter",
                "voice_text": "附近的避难场所位置"
            },
            {
                "source_type": "medicalInstitution",
                "voice_text": "需要医疗机构支援"
            },
            {
                "source_type": "rescueOrganization",
                "voice_text": "需要救援机构协助"
            },
            {
                "source_type": "protectionTarget",
                "voice_text": "查询防护目标信息"
            }
        ]

        # 执行测试
        for scenario in test_scenarios:
            await self.test_source_dispatch_by_type(
                accident_id=accident_id,
                source_type=scenario["source_type"],
                voice_text=scenario["voice_text"]
            )

        # 3. 输出测试总结
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
        result_file = Path(__file__).parent / "test_source_dispatch_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {result_file}")
        print("=" * 80)


async def main():
    """主函数"""
    tester = TestSourceDispatch()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
