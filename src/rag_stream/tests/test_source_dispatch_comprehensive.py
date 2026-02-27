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

from rag_stream.models.schemas import SourceDispatchRequest
from rag_stream.services.source_dispath_srvice import handle_source_dispatch
from DaiShanSQL import Server


class ComprehensiveTestRunner:
    """综合测试运行器"""

    def __init__(self):
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

            dispatch_result = await handle_source_dispatch(request)

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
        if total_tests > 0:
            self.log_test_output(f"成功率: {successful_tests / total_tests * 100:.1f}%")

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
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)

        self.log_test_output(f"\n详细测试结果已保存到: {result_file}")

        self.log_test_output(f"\n{'='*80}")
        self.log_test_output("测试完成")
        self.log_test_output(f"{'='*80}")


async def main():
    """主函数"""
    runner = ComprehensiveTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
