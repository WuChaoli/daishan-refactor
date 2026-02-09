"""应急资源实体类"""
import json
import re
from typing import Tuple, Optional
from pydantic import BaseModel


def parse_location(location_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    解析位置字符串，提取经纬度

    Args:
        location_str: 位置JSON字符串，格式如：
            - {"type":"Point","coordinates":[122.21945804103106,30.265265407892773,1]}
            - [122.21945804103106,30.265265407892773]

    Returns:
        (longitude, latitude) 元组，如果解析失败返回 (None, None)
    """
    if not location_str:
        return None, None

    # 尝试JSON解析
    try:
        location_data = json.loads(location_str)

        # 处理 {"type":"Point","coordinates":[lon,lat,...]} 格式
        if isinstance(location_data, dict):
            coordinates = location_data.get("coordinates", [])
            if len(coordinates) >= 2:
                longitude = float(coordinates[0])
                latitude = float(coordinates[1])
                return longitude, latitude

        # 处理 [lon,lat] 格式
        elif isinstance(location_data, list) and len(location_data) >= 2:
            longitude = float(location_data[0])
            latitude = float(location_data[1])
            return longitude, latitude
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        pass

    # JSON解析失败，尝试正则匹配 [经度,纬度] 格式
    try:
        pattern = r'\[([+-]?\d+\.?\d*),\s*([+-]?\d+\.?\d*)'
        match = re.search(pattern, location_str)
        if match:
            longitude = float(match.group(1))
            latitude = float(match.group(2))
            return longitude, latitude
    except (ValueError, AttributeError):
        pass

    return None, None


class EmergencySupply(BaseModel):
    """应急物资"""
    id: str
    material_name: str

    class Config:
        frozen = True


class RescueTeam(BaseModel):
    """救援队伍"""
    id: str
    team_name: str

    class Config:
        frozen = True


class EmergencyExpert(BaseModel):
    """应急专家"""
    id: str
    expert_name: str

    class Config:
        frozen = True


class FireFightingFacility(BaseModel):
    """消防设施"""
    id: str
    name: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @classmethod
    def from_db_row(cls, id: str, name: str, latitude_longitude: Optional[str]):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(latitude_longitude)
        return cls(
            id=id,
            name=name,
            longitude=longitude,
            latitude=latitude
        )

    class Config:
        frozen = True


class Shelter(BaseModel):
    """避难场所"""
    id: str
    shelter_name: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @classmethod
    def from_db_row(cls, id: str, shelter_name: str, lon_and_lat: Optional[str]):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(lon_and_lat)
        return cls(
            id=id,
            shelter_name=shelter_name,
            longitude=longitude,
            latitude=latitude
        )

    class Config:
        frozen = True


class MedicalInstitution(BaseModel):
    """医疗机构"""
    id: str
    institution_name: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @classmethod
    def from_db_row(cls, id: str, institution_name: str, local_pos: Optional[str]):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(local_pos)
        return cls(
            id=id,
            institution_name=institution_name,
            longitude=longitude,
            latitude=latitude
        )

    class Config:
        frozen = True


class RescueOrganization(BaseModel):
    """救援机构"""
    id: str
    institution_name: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @classmethod
    def from_db_row(cls, id: str, institution_name: str, local_pos: Optional[str]):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(local_pos)
        return cls(
            id=id,
            institution_name=institution_name,
            longitude=longitude,
            latitude=latitude
        )

    class Config:
        frozen = True


class ProtectionTarget(BaseModel):
    """防护目标"""
    id: str
    target_name: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @classmethod
    def from_db_row(cls, id: str, target_name: str, local_pos: Optional[str]):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(local_pos)
        return cls(
            id=id,
            target_name=target_name,
            longitude=longitude,
            latitude=latitude
        )

    class Config:
        frozen = True
