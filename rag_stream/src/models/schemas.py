from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


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

