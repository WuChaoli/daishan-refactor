"""测试应急资源SQL查询和实体类加载"""
import json
import os
import sys
from enum import Enum
from typing import Dict, List, Any, Type, Optional
import requests
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent

from rag_stream.models.emergency_entities import (
    EmergencySupply,
    RescueTeam,
    EmergencyExpert,
    FireFightingFacility,
    Shelter,
    MedicalInstitution,
    RescueOrganization,
    ProtectionTarget
)
from DaiShanSQL import Server


class BusinessArea(Enum):
    """业务领域枚举"""
    DISASTER_RESCUE = "1"  # 灾害事故救援
    HAZMAT_RESCUE = "2"  # 危化品泄漏救援
    TRAFFIC_RESCUE = "3"  # 交通事故救援
    WATER_RESCUE = "4"  # 水上救援
    MOUNTAIN_RESCUE = "5"  # 山地救援
    PUBLIC_HEALTH_RESCUE = "6"  # 公共卫生事件救援
    OTHER_RESCUE = "7"  # 其他领域


class EmergencyResourceTester:
    """应急资源SQL查询和实体类加载测试器"""

    def __init__(self):
        # 创建DaiShanSQL Server实例
        self.server = Server()

        # 加载SQL模板配置
        mapping_file = project_root / "rag_stream/src/utils/source_type_mapping.json"
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.sql_mapping = json.load(f)

        # 实体类映射
        self.entity_mapping = {
            "emergencySupplies": EmergencySupply,
            "rescueTeam": RescueTeam,
            "emergencyExpert": EmergencyExpert,
            "fireFightingFacilities": FireFightingFacility,
            "shelter": Shelter,
            "medicalInstitution": MedicalInstitution,
            "rescueOrganization": RescueOrganization,
            "protectionTarget": ProtectionTarget
        }

        # 实体类工厂方法映射（用于有位置字段的实体）
        self.entity_factory_mapping = {
            "fireFightingFacilities": ("from_db_row", ["id", "name", "latitude_longitude"]),
            "shelter": ("from_db_row", ["id", "shelter_name", "lon_and_lat"]),
            "medicalInstitution": ("from_db_row", ["id", "institution_name", "local_pos"]),
            "rescueOrganization": ("from_db_row", ["id", "institution_name", "local_pos"]),
            "protectionTarget": ("from_db_row", ["id", "target_name", "local_pos"])
        }

    def execute_sql(self, sql: str) -> Optional[List[Dict[str, Any]]]:
        """执行SQL查询"""
        try:
            result = self.server.QueryBySQL(sql)
            if isinstance(result, dict) and result.get('code') == 200:
                return result.get('data', [])
            elif isinstance(result, list):
                return result
            else:
                print(f"查询失败: {result}")
                return None
        except Exception as e:
            print(f"执行SQL异常: {e}")
            return None

    def load_to_entity(self, resource_type: str, row: Dict[str, Any]) -> Optional[Any]:
        """将数据库行加载到实体类"""
        entity_class = self.entity_mapping.get(resource_type)
        if not entity_class:
            print(f"未找到实体类: {resource_type}")
            return None

        try:
            # 检查是否需要使用工厂方法
            if resource_type in self.entity_factory_mapping:
                factory_method, field_names = self.entity_factory_mapping[resource_type]
                # 提取字段值（大小写不敏感）
                values = []
                for field_name in field_names:
                    # 尝试不同的大小写组合
                    value = row.get(field_name) or row.get(field_name.upper()) or row.get(field_name.lower())
                    # ID字段转换为字符串
                    if field_name.lower() == 'id' and value is not None:
                        value = str(value)
                    values.append(value)
                # 调用工厂方法
                return getattr(entity_class, factory_method)(*values)
            else:
                # 直接实例化（处理字段名大小写和类型转换）
                normalized_row = {}
                for key, value in row.items():
                    key_lower = key.lower()
                    # ID字段转换为字符串
                    if key_lower == 'id' and value is not None:
                        value = str(value)
                    normalized_row[key_lower] = value
                return entity_class(**normalized_row)
        except Exception as e:
            print(f"加载实体失败: {e}, 数据: {row}")
            return None

    def test_resource_type(self, resource_type: str, business_area: Optional[str] = None, number: int = 5) -> Dict[str, Any]:
        """测试单个资源类型的SQL查询和实体加载"""
        print(f"\n{'='*80}")
        print(f"测试资源类型: {resource_type}")
        if business_area:
            print(f"业务领域: {business_area}")
        print(f"{'='*80}")

        # 获取SQL模板
        config = self.sql_mapping.get(resource_type)
        if not config:
            return {"success": False, "error": f"未找到资源类型配置: {resource_type}"}

        sql_template = config.get("sql_template")
        table_name = config.get("table_name")

        # 替换SQL模板参数
        sql = sql_template.format(
            table_name=table_name,
            business_area=business_area or "",
            number=number
        )

        print(f"SQL: {sql}")

        # 执行查询
        rows = self.execute_sql(sql)
        if rows is None:
            return {"success": False, "error": "SQL执行失败"}

        print(f"查询结果: {len(rows)} 条记录")

        # 加载到实体类
        entities = []
        for i, row in enumerate(rows):
            entity = self.load_to_entity(resource_type, row)
            if entity:
                entities.append(entity)
                if i < 3:  # 只打印前3条
                    print(f"  记录 {i+1}: {entity}")

        success_count = len(entities)
        print(f"成功加载: {success_count}/{len(rows)} 条记录")

        return {
            "success": True,
            "resource_type": resource_type,
            "sql": sql,
            "total_rows": len(rows),
            "loaded_entities": success_count,
            "entities": entities
        }

    def test_all_resources(self):
        """测试所有资源类型"""
        print("\n" + "="*80)
        print("开始测试所有应急资源SQL查询和实体加载")
        print("="*80)

        results = []

        # 1. 测试应急物资（无business_area参数）
        result = self.test_resource_type("emergencySupplies", number=5)
        results.append(result)

        # 2. 测试救援队伍（需要business_area参数，测试所有枚举值）
        for area in BusinessArea:
            result = self.test_resource_type("rescueTeam", business_area=area.value, number=3)
            results.append(result)

        # 3. 测试应急专家（需要business_area参数，测试所有枚举值）
        for area in BusinessArea:
            result = self.test_resource_type("emergencyExpert", business_area=area.value, number=3)
            results.append(result)

        # 4. 测试消防设施（无参数，有位置字段）
        result = self.test_resource_type("fireFightingFacilities")
        results.append(result)

        # 5. 测试避难场所（无参数，有位置字段）
        result = self.test_resource_type("shelter")
        results.append(result)

        # 6. 测试医疗机构（有number参数，有位置字段）
        result = self.test_resource_type("medicalInstitution", number=5)
        results.append(result)

        # 7. 测试救援机构（无参数，有位置字段）
        result = self.test_resource_type("rescueOrganization")
        results.append(result)

        # 8. 测试防护目标（无参数，有位置字段）
        result = self.test_resource_type("protectionTarget")
        results.append(result)

        # 统计结果
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)

        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)

        print(f"总测试数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")

        # 打印失败的测试
        failed_tests = [r for r in results if not r.get("success")]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  - {test.get('resource_type', 'Unknown')}: {test.get('error', 'Unknown error')}")

        return results


def main():
    """主测试函数"""
    tester = EmergencyResourceTester()
    results = tester.test_all_resources()

    # 保存测试结果
    output_file = project_root / "rag_stream/tests/test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 将实体对象转换为字典以便JSON序列化
        serializable_results = []
        for result in results:
            if result.get("entities"):
                result["entities"] = [e.dict() if hasattr(e, 'dict') else str(e) for e in result["entities"]]
            serializable_results.append(result)
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)

    print(f"\n测试结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
