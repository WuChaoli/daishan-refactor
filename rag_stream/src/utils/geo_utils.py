"""地理距离计算工具"""
import math
from typing import List, TypeVar, Protocol, Optional


class HasCoordinates(Protocol):
    """具有坐标属性的协议"""
    longitude: Optional[float]
    latitude: Optional[float]


T = TypeVar('T', bound=HasCoordinates)


def calculate_distance(
    lon1: Optional[float],
    lat1: Optional[float],
    lon2: Optional[float],
    lat2: Optional[float]
) -> Optional[float]:
    """
    使用 Haversine 公式计算两个经纬度点之间的距离

    Args:
        lon1: 第一个点的经度
        lat1: 第一个点的纬度
        lon2: 第二个点的经度
        lat2: 第二个点的纬度

    Returns:
        两点之间的距离（单位：千米），如果任一坐标为 None 则返回 None
    """
    if None in (lon1, lat1, lon2, lat2):
        return None

    # 地球半径（千米）
    R = 6371.0

    # 转换为弧度
    lon1_rad = math.radians(lon1)
    lat1_rad = math.radians(lat1)
    lon2_rad = math.radians(lon2)
    lat2_rad = math.radians(lat2)

    # Haversine 公式
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def sort_entities_by_distance(
    reference_entity: HasCoordinates,
    entities: List[T]
) -> List[T]:
    """
    根据与参考实体的空间距离对实体数组进行排序

    Args:
        reference_entity: 参考实体，包含 longitude 和 latitude 属性
        entities: 待排序的实体数组

    Returns:
        按距离由近到远排序后的新实体数组
        - 有坐标的实体按距离排序在前
        - 无坐标的实体排在最后，保持原有顺序
    """
    if not entities:
        return []

    # 如果参考实体没有坐标，返回原数组的副本
    ref_lon = getattr(reference_entity, 'longitude', None)
    ref_lat = getattr(reference_entity, 'latitude', None)

    if ref_lon is None or ref_lat is None:
        return entities.copy()

    # 分离有坐标和无坐标的实体
    entities_with_coords = []
    entities_without_coords = []

    for entity in entities:
        # 使用 getattr 安全地获取坐标属性
        entity_lon = getattr(entity, 'longitude', None)
        entity_lat = getattr(entity, 'latitude', None)

        if entity_lon is not None and entity_lat is not None:
            distance = calculate_distance(
                ref_lon,
                ref_lat,
                entity_lon,
                entity_lat
            )
            entities_with_coords.append((entity, distance))
        else:
            entities_without_coords.append(entity)

    # 按距离排序有坐标的实体
    entities_with_coords.sort(key=lambda x: x[1] if x[1] is not None else float('inf'))

    # 组合结果：有坐标的在前，无坐标的在后
    sorted_entities = [entity for entity, _ in entities_with_coords]
    sorted_entities.extend(entities_without_coords)

    return sorted_entities
