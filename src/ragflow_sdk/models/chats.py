"""
聊天相关模型
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Chat(BaseModel):
    """聊天助手模型"""

    id: str = Field(description="聊天助手 ID")
    name: str = Field(description="聊天助手名称")
    description: Optional[str] = Field(default=None, description="描述")
    avatar: Optional[str] = Field(default=None, description="头像")
    llm_id: Optional[str] = Field(default=None, description="LLM ID")
    prompt: Optional[Dict] = Field(default_factory=dict, description="提示词配置")
    dataset_ids: Optional[List[str]] = Field(
        default_factory=list, description="关联数据集 ID 列表"
    )


class ChatCreate(BaseModel):
    """创建聊天助手请求"""

    name: str = Field(..., description="聊天助手名称", max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    avatar: Optional[str] = Field(default=None, description="头像")
    llm_id: Optional[str] = Field(default=None, description="LLM 模型 ID")
    prompt: Optional[Dict] = Field(default_factory=dict, description="提示词配置")
    dataset_ids: Optional[List[str]] = Field(
        default_factory=list, description="关联数据集 ID 列表"
    )


class ChatUpdate(BaseModel):
    """更新聊天助手请求"""

    name: Optional[str] = Field(default=None, description="聊天助手名称")
    description: Optional[str] = Field(default=None, description="描述")
    avatar: Optional[str] = Field(default=None, description="头像")
    llm_id: Optional[str] = Field(default=None, description="LLM 模型 ID")
    prompt: Optional[Dict] = Field(default=None, description="提示词配置")
    dataset_ids: Optional[List[str]] = Field(
        default=None, description="关联数据集 ID 列表"
    )


class ChatSession(BaseModel):
    """聊天会话模型"""

    id: str = Field(description="会话 ID")
    user_id: str = Field(default="", description="用户 ID")
    assistant_id: str = Field(description="聊天助手 ID")
    name: str = Field(description="会话名称")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求"""

    question: str = Field(..., description="用户问题")
    stream: bool = Field(default=False, description="是否使用流式响应")
    session_id: Optional[str] = Field(default=None, description="会话 ID")
