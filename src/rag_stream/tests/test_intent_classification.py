"""
意图识别测试 - 测试意图分类的准确性
测试不同场景下意图识别返回 resource 或 requirement 的准确性
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from src.services.prompts import SourceDispatchPrompts
from src.services.dify_client_factory import get_client


class IntentClassificationTester:
    """意图识别测试器"""

    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        self.general_client = None

    def initialize_client(self):
        """初始化Dify客户端"""
        try:
            self.general_client = get_client("GENRAL_CHAT")
            if self.general_client is None:
                raise ValueError("Dify general_chat client 未配置")
            print("✓ Dify客户端初始化成功")
            return True
        except Exception as e:
            print(f"✗ Dify客户端初始化失败: {e}")
            return False

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """
        获取测试用例
        返回包含预期为 resource 和 requirement 的测试用例
        """
        return [
            # ========== 预期返回 resource 的用例 ==========
            {
                "test_id": "RESOURCE_001",
                "category": "明确物品资源",
                "voice_text": "给我酒精棉",
                "expected_intent": "resource",
                "description": "明确请求物品资源-酒精棉"
            },
            {
                "test_id": "RESOURCE_002",
                "category": "明确物品资源",
                "voice_text": "我需要纱布和绷带",
                "expected_intent": "resource",
                "description": "明确请求多个物品资源"
            },
            {
                "test_id": "RESOURCE_003",
                "category": "明确人员资源",
                "voice_text": "找张三专家",
                "expected_intent": "resource",
                "description": "明确请求人员资源-专家"
            },
            {
                "test_id": "RESOURCE_004",
                "category": "明确人员资源",
                "voice_text": "我要李四局长",
                "expected_intent": "resource",
                "description": "明确请求人员资源-领导"
            },
            {
                "test_id": "RESOURCE_005",
                "category": "明确设施资源",
                "voice_text": "找到东区污水处理厂",
                "expected_intent": "resource",
                "description": "明确请求设施资源-具体污水处理厂"
            },
            {
                "test_id": "RESOURCE_006",
                "category": "明确设施资源",
                "voice_text": "我要去东区人民医院",
                "expected_intent": "resource",
                "description": "明确请求设施资源-具体医院名称"
            },
            {
                "test_id": "RESOURCE_007",
                "category": "明确物品资源",
                "voice_text": "给我防护服和口罩",
                "expected_intent": "resource",
                "description": "明确请求防护装备"
            },
            {
                "test_id": "RESOURCE_008",
                "category": "明确人员资源",
                "voice_text": "调派王五救援队",
                "expected_intent": "resource",
                "description": "明确请求救援队伍"
            },
            {
                "test_id": "RESOURCE_009",
                "category": "明确设施资源",
                "voice_text": "联系市中心消防站",
                "expected_intent": "resource",
                "description": "明确请求消防设施"
            },
            {
                "test_id": "RESOURCE_010",
                "category": "明确物品资源",
                "voice_text": "需要灭火器和消防栓",
                "expected_intent": "resource",
                "description": "明确请求消防器材"
            },

            # ========== 预期返回 requirement 的用例 ==========
            {
                "test_id": "REQUIREMENT_001",
                "category": "模糊位置需求",
                "voice_text": "帮我找到最近的消防站",
                "expected_intent": "requirement",
                "description": "模糊需求-最近的消防站"
            },
            {
                "test_id": "REQUIREMENT_002",
                "category": "模糊事故处理",
                "voice_text": "我遇到了火灾",
                "expected_intent": "requirement",
                "description": "模糊需求-火灾事故"
            },
            {
                "test_id": "REQUIREMENT_003",
                "category": "模糊伤害处理",
                "voice_text": "我被化学品腐蚀了怎么办",
                "expected_intent": "requirement",
                "description": "模糊需求-化学品腐蚀"
            },
            {
                "test_id": "REQUIREMENT_004",
                "category": "模糊位置需求",
                "voice_text": "最近的医院在哪里",
                "expected_intent": "requirement",
                "description": "模糊需求-最近的医院"
            },
            {
                "test_id": "REQUIREMENT_005",
                "category": "模糊救援需求",
                "voice_text": "需要救援",
                "expected_intent": "requirement",
                "description": "模糊需求-救援"
            },
            {
                "test_id": "REQUIREMENT_006",
                "category": "模糊位置需求",
                "voice_text": "附近有避难场所吗",
                "expected_intent": "requirement",
                "description": "模糊需求-避难场所"
            },
            {
                "test_id": "REQUIREMENT_007",
                "category": "模糊事故处理",
                "voice_text": "发生了危化品泄漏",
                "expected_intent": "requirement",
                "description": "模糊需求-危化品泄漏"
            },
            {
                "test_id": "REQUIREMENT_008",
                "category": "模糊救援需求",
                "voice_text": "有人受伤了",
                "expected_intent": "requirement",
                "description": "模糊需求-人员受伤"
            },
            {
                "test_id": "REQUIREMENT_009",
                "category": "模糊位置需求",
                "voice_text": "哪里有救援队伍",
                "expected_intent": "requirement",
                "description": "模糊需求-救援队伍位置"
            },
            {
                "test_id": "REQUIREMENT_010",
                "category": "模糊事故处理",
                "voice_text": "发生交通事故了",
                "expected_intent": "requirement",
                "description": "模糊需求-交通事故"
            },
            {
                "test_id": "REQUIREMENT_011",
                "category": "模糊位置需求",
                "voice_text": "找一个最近的避难点",
                "expected_intent": "requirement",
                "description": "模糊需求-最近避难点"
            },
            {
                "test_id": "REQUIREMENT_012",
                "category": "模糊救援需求",
                "voice_text": "需要专业救援人员",
                "expected_intent": "requirement",
                "description": "模糊需求-专业救援人员"
            },
            {
                "test_id": "REQUIREMENT_013",
                "category": "模糊设施需求",
                "voice_text": "我要去XX医院",
                "expected_intent": "requirement",
                "description": "模糊需求-使用占位符的医院"
            },
            {
                "test_id": "REQUIREMENT_014",
                "category": "模糊设施需求",
                "voice_text": "找到XX污水处理厂",
                "expected_intent": "requirement",
                "description": "模糊需求-使用占位符的污水处理厂"
            }
        ]

    async def test_single_intent(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个意图识别"""
        print(f"\n{'='*80}")
        print(f"测试用例: {test_case['test_id']}")
        print(f"分类: {test_case['category']}")
        print(f"语音文本: {test_case['voice_text']}")
        print(f"预期意图: {test_case['expected_intent']}")
        print(f"{'='*80}")

        result = {
            "test_id": test_case["test_id"],
            "category": test_case["category"],
            "voice_text": test_case["voice_text"],
            "expected_intent": test_case["expected_intent"],
            "actual_intent": None,
            "is_correct": False,
            "raw_response": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # 构建意图分类提示词
            prompt = SourceDispatchPrompts.get_intent_classification_prompt(
                test_case["voice_text"]
            )

            # 调用Dify进行意图分类
            dify_response = await asyncio.to_thread(
                self.general_client.run_chat,
                query=prompt,
                user="system",
                inputs={},
                conversation_id=""
            )

            # 提取响应
            answer = dify_response.answer if hasattr(dify_response, 'answer') else str(dify_response)
            result["raw_response"] = answer

            # 清理响应文本
            actual_intent = answer.strip().lower()
            result["actual_intent"] = actual_intent

            # 判断是否正确
            result["is_correct"] = (actual_intent == test_case["expected_intent"].lower())

            if result["is_correct"]:
                print(f"✓ 测试通过")
                print(f"  实际意图: {actual_intent}")
            else:
                print(f"✗ 测试失败")
                print(f"  预期意图: {test_case['expected_intent']}")
                print(f"  实际意图: {actual_intent}")

        except Exception as e:
            result["error"] = str(e)
            print(f"✗ 测试异常: {e}")

        return result

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("开始意图识别测试")
        print("="*80)

        self.start_time = datetime.now()

        # 初始化客户端
        if not self.initialize_client():
            print("客户端初始化失败，测试终止")
            return

        # 获取测试用例
        test_cases = self.get_test_cases()
        print(f"\n共 {len(test_cases)} 个测试用例")

        # 执行测试
        for test_case in test_cases:
            result = await self.test_single_intent(test_case)
            self.test_results.append(result)

        self.end_time = datetime.now()

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("测试报告")
        print("="*80)

        # 统计数据
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["is_correct"])
        failed_tests = total_tests - passed_tests
        accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 按预期意图分类统计
        resource_tests = [r for r in self.test_results if r["expected_intent"] == "resource"]
        requirement_tests = [r for r in self.test_results if r["expected_intent"] == "requirement"]

        resource_passed = sum(1 for r in resource_tests if r["is_correct"])
        requirement_passed = sum(1 for r in requirement_tests if r["is_correct"])

        resource_accuracy = (resource_passed / len(resource_tests) * 100) if resource_tests else 0
        requirement_accuracy = (requirement_passed / len(requirement_tests) * 100) if requirement_tests else 0

        # 打印统计信息
        print(f"\n总体统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过数: {passed_tests}")
        print(f"  失败数: {failed_tests}")
        print(f"  准确率: {accuracy:.2f}%")

        print(f"\nResource 意图测试:")
        print(f"  测试数: {len(resource_tests)}")
        print(f"  通过数: {resource_passed}")
        print(f"  准确率: {resource_accuracy:.2f}%")

        print(f"\nRequirement 意图测试:")
        print(f"  测试数: {len(requirement_tests)}")
        print(f"  通过数: {requirement_passed}")
        print(f"  准确率: {requirement_accuracy:.2f}%")

        # 失败用例详情
        failed_cases = [r for r in self.test_results if not r["is_correct"]]
        if failed_cases:
            print(f"\n失败用例详情:")
            for case in failed_cases:
                print(f"\n  测试ID: {case['test_id']}")
                print(f"  语音文本: {case['voice_text']}")
                print(f"  预期意图: {case['expected_intent']}")
                print(f"  实际意图: {case['actual_intent']}")
                if case.get("error"):
                    print(f"  错误信息: {case['error']}")

        # 保存结果到JSON文件
        output_file = Path(__file__).parent / "test_intent_classification_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "accuracy": accuracy,
                    "resource_accuracy": resource_accuracy,
                    "requirement_accuracy": requirement_accuracy,
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat()
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {output_file}")


async def main():
    """主函数"""
    tester = IntentClassificationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

