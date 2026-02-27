from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from rag_stream.models.emergency_entities import parse_location


class ChatType(str, Enum):
    """聊天类型枚举"""

    法律法规 = "法律法规"
    标准规范 = "标准规范"
    应急知识 = "应急知识"
    事故案例 = "事故案例"
    MSDS = "MSDS"
    标准政策 = "标准政策"
    通用 = "通用"
    重大危险源预警 = "重大危险源预警"
    当日安全态势 = "当日安全态势"
    双重预防机制效果 = "双重预防机制效果"
    园区开停车 = "园区开停车"
    园区特殊作业态势 = "园区特殊作业态势"
    园区企业态势 = "园区企业态势"


class ChatRequest(BaseModel):
    """聊天请求模型"""

    question: str = Field(..., description="用户问题", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    stream: bool = Field(True, description="是否启用流式响应")

class ChatDeleteRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")


class SessionRequest(BaseModel):
    """创建会话请求模型（main.py 迁移）"""

    name: str = Field(..., description="会话名称", min_length=1)
    user_id: Optional[str] = Field(None, description="用户ID")


class ChatResponse(BaseModel):
    """聊天响应模型"""

    code: int = Field(0, description="响应状态码")
    message: str = Field("", description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class StreamChunk(BaseModel):
    """流式响应块模型"""

    session_id: str = Field(..., description="会话ID")
    answer: str = Field(..., description="回答内容")
    flag: int = Field(1, description="标志位")
    word_id: int = Field(..., description="词汇ID")


class SessionResponse(BaseModel):
    """会话响应模型"""

    code: int = Field(0, description="响应状态码")
    message: str = Field("", description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="会话数据")


# 意图识别相关模型
class QueryResult(BaseModel):
    """查询结果模型"""

    question: str = Field(..., description="匹配的问题原文")
    similarity: float = Field(..., description="相似度分数")


class IntentRequest(BaseModel):
    """意图识别请求模型"""

    text_input: str = Field(..., description="用户输入文本", min_length=1)
    user_id: Optional[str] = Field(None, description="用户ID")


class GuessQuestionsRequest(BaseModel):
    """猜你想问请求模型"""

    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)


class IntentResponse(BaseModel):
    """意图识别响应模型"""

    type: int = Field(..., description="意图类型 (0/1/2)")
    query: str = Field(..., description="用户原始查询")
    results: list[QueryResult] = Field(default_factory=list, description="Top 5 查询结果")
    similarity: float = Field(..., description="最高相似度")
    database: str = Field(..., description="匹配的知识库名称")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    suggestion: Optional[str] = Field(None, description="建议")


class PeopleDispatchRequest(BaseModel):
    """人员调度请求模型"""

    accidentId: str = Field(..., description="事故ID")
    voiceText: Optional[str] = Field(None, description="语音文本内容")


class SourceDispatchRequest(BaseModel):
    """资源调度请求模型"""

    accidentId: str = Field(..., description="事故ID", min_length=1)
    sourceType: Literal[
        "emergencySupplies",
        "rescueTeam",
        "emergencyExpert",
        "fireFightingFacilities",
        "shelter",
        "medicalInstitution",
        "rescueOrganization",
        "protectionTarget"
    ] = Field(..., description="资源类型")
    voiceText: Optional[str] = Field(None, description="语音文本内容")


class AccidentEventData(BaseModel):
    """事故事件数据模型"""

    accident_name: Optional[str] = Field(None, description="事故名称")
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    hazardous_chemicals: Optional[str] = Field(None, description="危险化学品")
    accident_overview: Optional[str] = Field(None, description="事故概述")

    @classmethod
    def from_db_row(
        cls,
        accident_name: Optional[str],
        coordinate: Optional[str],
        hazardous_chemicals: Optional[str],
        accident_overview: Optional[str]
    ):
        """从数据库行创建实例"""
        longitude, latitude = parse_location(coordinate)
        return cls(
            accident_name=accident_name,
            longitude=longitude,
            latitude=latitude,
            hazardous_chemicals=hazardous_chemicals,
            accident_overview=accident_overview
        )

    def to_json_str(self) -> str:
        """转换为 JSON 字符串"""
        return self.model_dump_json(indent=2, exclude_none=True)
