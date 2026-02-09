"""
Dify 聊天应用数据模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    """聊天消息响应"""

    message_id: str = Field(..., description="消息 ID")
    conversation_id: str = Field(..., description="对话 ID")
    mode: str = Field(..., description="模式 (chat/companion)")
    answer: str = Field(..., description="AI 回答")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: int = Field(..., description="创建时间 (时间戳)")
    total_tokens: Optional[int] = Field(None, description="总 Token 数")
    total_price: Optional[float] = Field(None, description="总价格")
    currency: Optional[str] = Field(None, description="货币单位")

    # 额外字段
    workflow_id: Optional[str] = Field(None, description="工作流 ID (如果是工作流聊天)")
    task_id: Optional[str] = Field(None, description="任务 ID")
    status: str = Field(default="succeeded", description="状态")

    # 兼容字段
    @property
    def result(self) -> str:
        """回答内容 (兼容 WorkflowRunResponse)"""
        return self.answer

    @property
    def outputs(self) -> Dict[str, Any]:
        """输出 (兼容 WorkflowRunResponse)"""
        return {"answer": self.answer, "metadata": self.metadata}

    @property
    def elapsed_time(self) -> Optional[float]:
        """耗时 (兼容 WorkflowRunResponse)"""
        return None

    class Config:
        """Pydantic 配置"""

        populate_by_name = True
        extra = "allow"  # 允许额外字段


class ChatStreamEvent(BaseModel):
    """聊天流式事件"""

    event_type: str = Field(..., description="事件类型")
    message_id: Optional[str] = Field(None, description="消息 ID")
    conversation_id: Optional[str] = Field(None, description="对话 ID")
    task_id: Optional[str] = Field(None, description="任务 ID")

    # 事件数据
    answer: Optional[str] = Field(None, description="回答内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: Optional[int] = Field(None, description="创建时间 (时间戳)")

    # 工作流相关
    workflow_id: Optional[str] = Field(None, description="工作流 ID")
    status: Optional[str] = Field(None, description="状态")
    elapsed_time: Optional[float] = Field(None, description="耗时")

    class Config:
        """Pydantic 配置"""

        populate_by_name = True
        extra = "allow"


class ChatMessage(BaseModel):
    """聊天消息"""

    role: str = Field(..., description="角色 (user/assistant)")
    content: str = Field(..., description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ChatContext(BaseModel):
    """聊天上下文"""

    conversation_id: Optional[str] = Field(None, description="对话 ID")
    messages: Optional[List[ChatMessage]] = Field(None, description="历史消息")
    user: Optional[str] = Field(None, description="用户 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
