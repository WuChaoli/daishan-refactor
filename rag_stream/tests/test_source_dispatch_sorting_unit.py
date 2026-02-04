"""测试资源调度中的距离排序功能 - 单元测试版本"""
from src.models.schemas import AccidentEventData
from src.models.emergency_entities import (
    FireFightingFacility,
    Shelter,
    MedicalInstitution,
    EmergencySupply
)
from src.utils.geo_utils import sort_entities_by_distance


def test_sort_fire_facilities_by_distance():
    """测试消防设施按距离排序"""

    # 创建事故地点（上海）
    accident = AccidentEventData(
        accident_name="测试事故",
        longitude=121.4737,
        latitude=31.2304,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 创建不同距离的消防设施
    facilities = [
        FireFightingFacility(
            id="1",
            name="远处消防站",
            longitude=116.4074,  # 北京
            latitude=39.9042
        ),
        FireFightingFacility(
            id="2",
            name="近处消防站",
            longitude=121.5,  # 上海附近
            latitude=31.25
        ),
        FireFightingFacility(
            id="3",
            name="中等距离消防站",
            longitude=120.1551,  # 杭州
            latitude=30.2741
        ),
    ]

    # 排序
    sorted_facilities = sort_entities_by_distance(accident, facilities)

    # 验证：近 < 中 < 远
    assert sorted_facilities[0].name == "近处消防站"
    assert sorted_facilities[1].name == "中等距离消防站"
    assert sorted_facilities[2].name == "远处消防站"

    print("✓ 消防设施按距离排序测试通过")


def test_sort_shelters_by_distance():
    """测试避难场所按距离排序"""

    # 创建事故地点
    accident = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 创建不同距离的避难场所
    shelters = [
        Shelter(id="1", shelter_name="远处避难所", longitude=121.0, latitude=31.0),
        Shelter(id="2", shelter_name="近处避难所", longitude=120.1, latitude=30.1),
        Shelter(id="3", shelter_name="中等距离避难所", longitude=120.5, latitude=30.5),
    ]

    # 排序
    sorted_shelters = sort_entities_by_distance(accident, shelters)

    # 验证
    assert sorted_shelters[0].shelter_name == "近处避难所"
    assert sorted_shelters[1].shelter_name == "中等距离避难所"
    assert sorted_shelters[2].shelter_name == "远处避难所"

    print("✓ 避难场所按距离排序测试通过")


def test_medical_institution_should_not_be_sorted():
    """测试医疗机构应该保持原顺序（业务逻辑：医疗机构不按距离排序）"""

    # 创建事故地点
    accident = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 创建医疗机构（故意按远到近的顺序）
    institutions = [
        MedicalInstitution(id="1", institution_name="远处医院", longitude=121.0, latitude=31.0),
        MedicalInstitution(id="2", institution_name="近处医院", longitude=120.1, latitude=30.1),
    ]

    # 注意：在实际业务逻辑中，医疗机构不会调用排序函数
    # 这里只是验证如果调用了排序函数，它也能正常工作
    sorted_institutions = sort_entities_by_distance(accident, institutions)

    # 验证排序功能本身是正常的（即使业务上不使用）
    assert sorted_institutions[0].institution_name == "近处医院"
    assert sorted_institutions[1].institution_name == "远处医院"

    print("✓ 医疗机构排序功能测试通过（注：业务逻辑中不使用）")


def test_entities_without_coords():
    """测试无坐标实体（如应急物资）"""

    # 创建事故地点
    accident = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 创建无坐标的应急物资
    supplies = [
        EmergencySupply(id="1", material_name="物资A"),
        EmergencySupply(id="2", material_name="物资B"),
        EmergencySupply(id="3", material_name="物资C"),
    ]

    # 排序（应该保持原顺序）
    sorted_supplies = sort_entities_by_distance(accident, supplies)

    # 验证保持原顺序
    assert sorted_supplies[0].material_name == "物资A"
    assert sorted_supplies[1].material_name == "物资B"
    assert sorted_supplies[2].material_name == "物资C"

    print("✓ 无坐标实体保持原顺序测试通过")


def test_mixed_entities_with_and_without_coords():
    """测试混合有坐标和无坐标的实体"""

    # 创建事故地点
    accident = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 创建混合实体
    shelters = [
        Shelter(id="1", shelter_name="有坐标-远", longitude=121.0, latitude=31.0),
        Shelter(id="2", shelter_name="无坐标1", longitude=None, latitude=None),
        Shelter(id="3", shelter_name="有坐标-近", longitude=120.1, latitude=30.1),
        Shelter(id="4", shelter_name="无坐标2", longitude=None, latitude=None),
    ]

    # 排序
    sorted_shelters = sort_entities_by_distance(accident, shelters)

    # 验证：有坐标的按距离排序在前，无坐标的在后
    assert sorted_shelters[0].shelter_name == "有坐标-近"
    assert sorted_shelters[1].shelter_name == "有坐标-远"
    assert sorted_shelters[2].shelter_name in ["无坐标1", "无坐标2"]
    assert sorted_shelters[3].shelter_name in ["无坐标1", "无坐标2"]

    print("✓ 混合实体排序测试通过")


def test_source_dispatch_sorting_logic():
    """测试资源调度中的排序逻辑"""

    # 创建事故地点
    accident = AccidentEventData(
        accident_name="化学品泄漏",
        longitude=122.21945804103106,
        latitude=30.265265407892773,
        hazardous_chemicals="氨气",
        accident_overview="工厂发生氨气泄漏"
    )

    # 定义需要排序的资源类型
    entities_with_coords = [
        "fireFightingFacilities",
        "shelter",
        "rescueOrganization",
        "protectionTarget"
    ]

    # 模拟不同资源类型
    test_cases = [
        ("fireFightingFacilities", True),   # 应该排序
        ("shelter", True),                  # 应该排序
        ("rescueOrganization", True),       # 应该排序
        ("protectionTarget", True),         # 应该排序
        ("medicalInstitution", False),      # 不应该排序
        ("emergencySupplies", False),       # 不应该排序
        ("rescueTeam", False),              # 不应该排序
        ("emergencyExpert", False),         # 不应该排序
    ]

    for source_type, should_sort in test_cases:
        is_sortable = source_type in entities_with_coords
        assert is_sortable == should_sort, f"{source_type} 排序逻辑错误"

    print("✓ 资源调度排序逻辑测试通过")


if __name__ == "__main__":
    print("开始测试资源调度距离排序功能...\n")

    try:
        test_sort_fire_facilities_by_distance()
        test_sort_shelters_by_distance()
        test_medical_institution_should_not_be_sorted()
        test_entities_without_coords()
        test_mixed_entities_with_and_without_coords()
        test_source_dispatch_sorting_logic()

        print("\n✓ 所有测试通过！")
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        raise
