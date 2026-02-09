"""
综合测试 handle_source_dispatch 函数
整合所有测试用例，生成详细的测试报告
"""
import asyncio
import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.schemas import SourceDispatchRequest
from src.services.source_dispath_srvice import handle_source_dispatch
from src.services.log_manager import LogManager
from src.config.settings import settings
from DaiShanSQL import Server


class ComprehensiveTestRunner:
    """综合测试运行器"""

    def __init__(self):
        self.log_manager = LogManager(settings.logging)
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def log_test_output(self, message: str):
        """记录测试输出"""
        print(message)

    async def test_accident_query(self, test_id: str, accident_id: str) -> Dict[str, Any]:
        """测试事故ID查询"""
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output(f"测试用例: {test_id}")
        self.log_test_output(f"事故ID查询: {accident_id}")
        self.log_test_output(f"{'='*80}")

        result = {
            "test_id": test_id,
            "category": "基础功能测试",
            "test_type": "事故ID查询",
            "accident_id": accident_id,
            "success": False,
            "error": None,
            "output": None
        }

        try:
            sql = f"""
            SELECT ID, ACCIDENT_NAME, TO_CHAR(COORDINATE) AS COORDINATE,
                   HAZARDOUS_CHEMICALS, ACCIDENT_OVERVIEW
            FROM IPARK_AE_ACCIDENT_EVENT
            WHERE ID = {accident_id}
            """

            server = Server()
            query_result = server.QueryBySQL(sql)

            if isinstance(query_result, dict):
                data_list = query_result.get('data', [])
                if data_list and len(data_list) > 0:
                    row = data_list[0]
                    result["success"] = True
                    result["output"] = {
                        "accident_name": row.get('ACCIDENT_NAME'),
                        "coordinate": row.get('COORDINATE'),
                        "hazardous_chemicals": row.get('HAZARDOUS_CHEMICALS')
                    }
                    self.log_test_output(f"✓ 成功查询到事故数据")
                    self.log_test_output(f"  事故名称: {row.get('ACCIDENT_NAME')}")
                else:
                    result["error"] = f"未找到事故ID为 {accident_id} 的数据"
                    self.log_test_output(f"✗ {result['error']}")
            else:
                result["error"] = "查询结果格式异常"
                self.log_test_output(f"✗ {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            self.log_test_output(f"✗ 测试失败: {e}")

        return result

    async def test_source_dispatch(
        self,
        test_id: str,
        category: str,
        accident_id: str,
        source_type: str,
        voice_text: str,
        test_name: str = None
    ) -> Dict[str, Any]:
        """测试资源调度"""
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output(f"测试用例: {test_id}")
        if test_name:
            self.log_test_output(f"测试名称: {test_name}")
        self.log_test_output(f"{'='*80}")
        self.log_test_output(f"事故ID: {accident_id}")
        self.log_test_output(f"资源类型: {source_type}")
        self.log_test_output(f"语音文本: {voice_text}")
        self.log_test_output(f"{'-'*80}")

        result = {
            "test_id": test_id,
            "category": category,
            "test_name": test_name or f"{source_type} - {voice_text[:20]}",
            "accident_id": accident_id,
            "source_type": source_type,
            "voice_text": voice_text,
            "success": False,
            "error": None,
            "output": None,
            "result_count": 0
        }

        try:
            request = SourceDispatchRequest(
                accidentId=accident_id,
                sourceType=source_type,
                voiceText=voice_text
            )

            dispatch_result = await handle_source_dispatch(request, self.log_manager)

            if dispatch_result:
                result["success"] = True
                result["output"] = dispatch_result
                result["result_count"] = len(dispatch_result) if isinstance(dispatch_result, list) else 1
                self.log_test_output(f"\n✓ 测试成功，返回 {result['result_count']} 条结果")
                self.log_test_output(f"结果: {json.dumps(dispatch_result, ensure_ascii=False, indent=2)}")
            else:
                result["error"] = "未返回结果"
                self.log_test_output(f"\n✗ 测试失败: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            self.log_test_output(f"\n✗ 测试失败: {e}")
            self.log_test_output(traceback.format_exc())

        return result

    async def run_all_tests(self):
        """运行所有测试用例"""
        self.start_time = datetime.now()
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output(f"开始综合测试 handle_source_dispatch")
        self.log_test_output(f"测试开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_test_output(f"{'='*80}")

        # 1. 基础功能测试 - 事故ID查询
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("第一部分: 基础功能测试 - 事故ID查询")
        self.log_test_output(f"{'='*80}")

        accident_query_tests = [
            ("TC-001", "5896694001464688"),
            ("TC-002", "5844749472101664"),
            ("TC-003", "999999"),
        ]

        for test_id, accident_id in accident_query_tests:
            result = await self.test_accident_query(test_id, accident_id)
            self.test_results.append(result)
            await asyncio.sleep(0.5)

        # 2. 资源类型测试（查询意图）
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("第二部分: 资源类型测试（查询意图）")
        self.log_test_output(f"{'='*80}")

        # 使用有效的事故ID
        valid_accident_id = "5896694001464688"

        resource_type_tests = [
            # 应急物资
            ("TC-101", "emergencySupplies", "需要调度应急物资到事故现场"),
            ("TC-102", "emergencySupplies", "需要防护装备和防毒面具"),
            # 救援队伍
            ("TC-201", "rescueTeam", "需要调度救援队伍支援"),
            ("TC-202", "rescueTeam", "调度消防队到现场"),
            # 应急专家
            ("TC-301", "emergencyExpert", "需要应急专家指导"),
            ("TC-302", "emergencyExpert", "需要化工专家支援"),
            # 消防设施
            ("TC-401", "fireFightingFacilities", "最近的消防设施在哪里"),
            ("TC-402", "fireFightingFacilities", "最近的污水处理厂在哪里"),
            # 避难场所
            ("TC-501", "shelter", "附近的避难场所位置"),
            ("TC-502", "shelter", "附近的避难场所"),
            # 医疗机构
            ("TC-601", "medicalInstitution", "需要医疗机构支援"),
            ("TC-602", "medicalInstitution", "最近的医院在哪里"),
            # 救援机构
            ("TC-701", "rescueOrganization", "需要救援机构协助"),
            ("TC-702", "rescueOrganization", "调度救援机构"),
            # 防护目标
            ("TC-801", "protectionTarget", "查询防护目标信息"),
            ("TC-802", "protectionTarget", "周边有哪些重点防护目标"),
        ]

        for test_id, source_type, voice_text in resource_type_tests:
            result = await self.test_source_dispatch(
                test_id=test_id,
                category="资源类型测试（查询意图）",
                accident_id=valid_accident_id,
                source_type=source_type,
                voice_text=voice_text
            )
            self.test_results.append(result)
            await asyncio.sleep(1)

        # 3. 资源意图测试（固体资源指令）
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("第三部分: 资源意图测试（固体资源指令）")
        self.log_test_output(f"{'='*80}")

        resource_intent_tests = [
            ("TC-901", "emergencySupplies", "我需要酒精棉，请帮我查询有哪些酒精棉物资", "查询酒精棉物资"),
            ("TC-902", "emergencySupplies", "测试企业物资1还有库存吗", "查询测试企业物资1"),
            ("TC-903", "emergencyExpert", "请联系张三专家", "查询张三专家"),
            ("TC-904", "emergencyExpert", "刘演翔专家的联系方式是什么", "查询刘演翔专家"),
            ("TC-905", "rescueTeam", "世倍尔救援队在哪里", "查询世倍尔救援队"),
            ("TC-906", "medicalInstitution", "岱山县第一人民医院的位置", "查询岱山县第一人民医院"),
            ("TC-907", "medicalInstitution", "岱西卫生院能接收伤员吗", "查询岱西卫生院"),
            ("TC-908", "fireFightingFacilities", "调度消防车、救护车到现场", "调度消防车救护车"),
        ]

        for test_id, source_type, voice_text, test_name in resource_intent_tests:
            result = await self.test_source_dispatch(
                test_id=test_id,
                category="资源意图测试（固体资源指令）",
                accident_id=valid_accident_id,
                source_type=source_type,
                voice_text=voice_text,
                test_name=test_name
            )
            self.test_results.append(result)
            await asyncio.sleep(1)

        # 4. 意图识别准确性测试
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("第四部分: 意图识别准确性测试")
        self.log_test_output(f"{'='*80}")

        intent_accuracy_tests = [
            # 查询意图 - 应该返回列表
            ("TC-1101", "emergencySupplies", "附近有哪些应急物资", "查询意图-应急物资列表"),
            ("TC-1102", "rescueTeam", "有哪些救援队伍可以调度", "查询意图-救援队伍列表"),
            ("TC-1103", "emergencyExpert", "有哪些专家可以联系", "查询意图-专家列表"),
            ("TC-1104", "medicalInstitution", "附近有哪些医院", "查询意图-医院列表"),
            ("TC-1105", "shelter", "附近有哪些避难场所", "查询意图-避难场所列表"),

            # 固体资源指令 - 应该返回具体资源
            ("TC-1201", "emergencySupplies", "调度酒精棉到现场", "固体指令-调度酒精棉"),
            ("TC-1202", "emergencySupplies", "需要测试企业物资1", "固体指令-指定物资名称"),
            ("TC-1203", "emergencyExpert", "联系张三专家", "固体指令-指定专家姓名"),
            ("TC-1204", "rescueTeam", "调度世倍尔救援队", "固体指令-指定救援队名称"),
            ("TC-1205", "medicalInstitution", "联系岱山县第一人民医院", "固体指令-指定医院名称"),

            # 混合意图 - 包含查询和指令
            ("TC-1301", "emergencySupplies", "有哪些防护装备，调度防毒面具", "混合意图-查询+指令"),
            ("TC-1302", "rescueTeam", "查询救援队伍，调度消防队", "混合意图-查询+指令"),

            # 模糊意图 - 需要智能判断
            ("TC-1401", "emergencySupplies", "需要物资支援", "模糊意图-通用物资"),
            ("TC-1402", "rescueTeam", "需要人员支援", "模糊意图-通用人员"),
            ("TC-1403", "emergencyExpert", "需要专业指导", "模糊意图-通用专家"),
        ]

        for test_id, source_type, voice_text, test_name in intent_accuracy_tests:
            result = await self.test_source_dispatch(
                test_id=test_id,
                category="意图识别准确性测试",
                accident_id=valid_accident_id,
                source_type=source_type,
                voice_text=voice_text,
                test_name=test_name
            )
            self.test_results.append(result)
            await asyncio.sleep(1)

        # 5. 边界条件测试
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("第五部分: 边界条件测试")
        self.log_test_output(f"{'='*80}")

        boundary_tests = [
            ("TC-1501", "", "emergencySupplies", "需要应急物资", "空事故ID"),
            ("TC-1502", "abc", "emergencySupplies", "需要应急物资", "无效事故ID"),
            ("TC-1503", valid_accident_id, "invalidType", "需要资源", "不存在的资源类型"),
            ("TC-1504", valid_accident_id, "emergencySupplies", "", "空语音文本"),
        ]

        for test_id, accident_id, source_type, voice_text, test_name in boundary_tests:
            result = await self.test_source_dispatch(
                test_id=test_id,
                category="边界条件测试",
                accident_id=accident_id,
                source_type=source_type,
                voice_text=voice_text,
                test_name=test_name
            )
            self.test_results.append(result)
            await asyncio.sleep(0.5)

        self.end_time = datetime.now()

        # 生成测试报告
        self.generate_reports()

    def generate_reports(self):
        """生成测试报告"""
        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("测试总结")
        self.log_test_output(f"{'='*80}")

        # 统计数据
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success"))
        failed_tests = total_tests - successful_tests

        duration = (self.end_time - self.start_time).total_seconds()

        self.log_test_output(f"\n测试结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_test_output(f"测试总耗时: {duration:.2f} 秒")
        self.log_test_output(f"\n总测试数: {total_tests}")
        self.log_test_output(f"成功: {successful_tests}")
        self.log_test_output(f"失败: {failed_tests}")
        self.log_test_output(f"成功率: {successful_tests / total_tests * 100:.1f}%")

        # 按分类统计
        self.log_test_output(f"\n按分类统计:")
        categories = {}
        for result in self.test_results:
            category = result.get("category", "未分类")
            if category not in categories:
                categories[category] = {"total": 0, "success": 0, "failed": 0}
            categories[category]["total"] += 1
            if result.get("success"):
                categories[category]["success"] += 1
            else:
                categories[category]["failed"] += 1

        for category, stats in categories.items():
            success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            self.log_test_output(f"  {category}:")
            self.log_test_output(f"    总数: {stats['total']}, 成功: {stats['success']}, 失败: {stats['failed']}, 成功率: {success_rate:.1f}%")

        # 保存详细结果到JSON文件
        result_file = Path(__file__).parent / "test_source_dispatch_comprehensive_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "test_summary": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "duration_seconds": duration,
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": successful_tests / total_tests * 100 if total_tests > 0 else 0,
                    "categories": categories
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)

        self.log_test_output(f"\n详细测试结果已保存到: {result_file}")

        # 提取失败用例
        failed_results = [r for r in self.test_results if not r.get("success")]
        if failed_results:
            failed_file = Path(__file__).parent / "test_source_dispatch_failed_cases.json"
            with open(failed_file, "w", encoding="utf-8") as f:
                json.dump(failed_results, f, ensure_ascii=False, indent=2)
            self.log_test_output(f"失败用例已保存到: {failed_file}")

        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("测试完成")
        self.log_test_output(f"{'='*80}")


async def main():
    """主函数"""
    runner = ComprehensiveTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
