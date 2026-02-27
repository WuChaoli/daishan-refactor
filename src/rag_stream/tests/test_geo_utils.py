"""地理距离计算工具测试"""
import pytest
from rag_stream.utils.geo_utils import calculate_distance, sort_entities_by_distance
from rag_stream.models.emergency_entities import FireFightingFacility, Shelter


class TestCalculateDistance:
    """测试距离计算函数"""

    def test_calculate_distance_normal(self):
        """测试正常的距离计算"""
        # 上海到北京的大致距离约 1067 公里
        shanghai_lon, shanghai_lat = 121.4737, 31.2304
        beijing_lon, beijing_lat = 116.4074, 39.9042

        distance = calculate_distance(
            shanghai_lon, shanghai_lat,
            beijing_lon, beijing_lat
        )

        assert distance is not None
        assert 1000 < distance < 1200  # 允许一定误差范围

    def test_calculate_distance_same_point(self):
        """测试相同点的距离"""
        lon, lat = 120.0, 30.0
        distance = calculate_distance(lon, lat, lon, lat)

        assert distance is not None
        assert distance < 0.001  # 应该接近 0

    def test_calculate_distance_with_none(self):
        """测试包含 None 的情况"""
        assert calculate_distance(None, 30.0, 120.0, 30.0) is None
        assert calculate_distance(120.0, None, 120.0, 30.0) is None
        assert calculate_distance(120.0, 30.0, None, 30.0) is None
        assert calculate_distance(120.0, 30.0, 120.0, None) is None


class TestSortEntitiesByDistance:
    """测试实体排序函数"""

    def test_sort_entities_normal(self):
        """测试正常排序"""
        # 参考点：上海
        reference = FireFightingFacility(
            id="ref",
            name="参考点",
            longitude=121.4737,
            latitude=31.2304
        )

        # 创建不同距离的实体
        entities = [
            # 北京（远）
            FireFightingFacility(
                id="1",
                name="北京",
                longitude=116.4074,
                latitude=39.9042
            ),
            # 杭州（近）
            FireFightingFacility(
                id="2",
                name="杭州",
                longitude=120.1551,
                latitude=30.2741
            ),
            # 南京（中）
            FireFightingFacility(
                id="3",
                name="南京",
                longitude=118.7969,
                latitude=32.0603
            ),
        ]

        sorted_entities = sort_entities_by_distance(reference, entities)

        # 验证排序：杭州 < 南京 < 北京
        assert sorted_entities[0].name == "杭州"
        assert sorted_entities[1].name == "南京"
        assert sorted_entities[2].name == "北京"

    def test_sort_entities_with_none_coords(self):
        """测试包含无坐标实体的排序"""
        reference = Shelter(
            id="ref",
            shelter_name="参考点",
            longitude=120.0,
            latitude=30.0
        )

        entities = [
            Shelter(id="1", shelter_name="有坐标1", longitude=120.1, latitude=30.1),
            Shelter(id="2", shelter_name="无坐标1", longitude=None, latitude=None),
            Shelter(id="3", shelter_name="有坐标2", longitude=120.05, latitude=30.05),
            Shelter(id="4", shelter_name="无坐标2", longitude=None, latitude=30.0),
        ]

        sorted_entities = sort_entities_by_distance(reference, entities)

        # 有坐标的应该在前面，且按距离排序
        assert sorted_entities[0].shelter_name == "有坐标2"  # 最近
        assert sorted_entities[1].shelter_name == "有坐标1"  # 较远
        # 无坐标的在后面
        assert sorted_entities[2].shelter_name in ["无坐标1", "无坐标2"]
        assert sorted_entities[3].shelter_name in ["无坐标1", "无坐标2"]

    def test_sort_entities_reference_no_coords(self):
        """测试参考实体无坐标的情况"""
        reference = FireFightingFacility(
            id="ref",
            name="参考点",
            longitude=None,
            latitude=None
        )

        entities = [
            FireFightingFacility(id="1", name="实体1", longitude=120.0, latitude=30.0),
            FireFightingFacility(id="2", name="实体2", longitude=121.0, latitude=31.0),
        ]

        sorted_entities = sort_entities_by_distance(reference, entities)

        # 应该返回原数组的副本，顺序不变
        assert len(sorted_entities) == 2
        assert sorted_entities[0].name == "实体1"
        assert sorted_entities[1].name == "实体2"
        # 验证是副本而非原数组
        assert sorted_entities is not entities

    def test_sort_entities_empty_list(self):
        """测试空数组"""
        reference = FireFightingFacility(
            id="ref",
            name="参考点",
            longitude=120.0,
            latitude=30.0
        )

        sorted_entities = sort_entities_by_distance(reference, [])
        assert sorted_entities == []
