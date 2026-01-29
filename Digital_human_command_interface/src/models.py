"""
Pydantic 数据模型定义
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class IntentRequest(BaseModel):
    """意图识别请求"""

    text_input: str = Field(
        ..., min_length=1, max_length=1000, description="用户查询文本"
    )
    user_id: Optional[str] = Field(
        None, max_length=100, description="用户标识符，用于会话管理和日志追踪"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text_input": "今天天气怎么样",
                "user_id": "user-12345",
            }
        }

    @field_validator("text_input")
    @classmethod
    def validate_text_input(cls, v: str) -> str:
        """验证 text_input 不包含控制字符"""
        if any(ord(c) < 32 for c in v):
            raise ValueError("查询包含非法控制字符")
        return v.strip()

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        """验证 user_id 格式"""
        if v is None:
            return None
        if any(ord(c) < 32 for c in v):
            raise ValueError("用户ID包含非法控制字符")
        return v.strip()


class QueryResult(BaseModel):
    """单个查询结果"""

    question: str = Field(..., description="匹配的问题原文")
    similarity: float = Field(..., description="相似度分数")

    class Config:
        json_schema_extra = {
            "example": {"question": "天气查询方法", "similarity": 0.85}
        }


class IntentResponse(BaseModel):
    """意图识别响应"""

    type: int = Field(
        ..., ge=0, le=10, description="意图类型: 0=语义类, 1=明确指令, 2=统计类"
    )
    query: str = Field(..., description="用户原始查询")
    results: List[QueryResult] = Field(..., description="Top 5 查询结果列表")

    class Config:
        json_schema_extra = {
            "example": {
                "type": 2,
                "query": "今天天气怎么样",
                "results": [
                    {"question": "天气查询方法", "similarity": 0.85},
                    {"question": "天气数据来源", "similarity": 0.75},
                ],
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str = Field(..., description="错误代码")
    message: str = Field(..., description="详细错误描述")
    suggestion: Optional[str] = Field(None, description="改进建议")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "query_length_exceeded",
                "message": "Query length exceeds 1000 characters",
                "suggestion": "Please shorten your query",
            }
        }