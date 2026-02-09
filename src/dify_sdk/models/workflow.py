"""
Dify 工作流相关数据模型

定义工作流执行、任务管理相关的 Pydantic 模型。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    """工作流执行请求"""

    inputs: Dict[str, Any] = Field(..., description="工作流输入参数")
    user: str = Field(..., description="用户标识符")
    response_mode: str = Field(
        default="blocking", description="响应模式: blocking 或 streaming"
    )
    files: Optional[List[str]] = Field(default=None, description="文件 ID 列表")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "inputs": {"query": "岱山园区有哪些企业?"},
                    "user": "user-123",
                    "response_mode": "blocking",
                }
            ]
        }
    }


class WorkflowRunResponse(BaseModel):
    """工作流执行响应"""

    workflow_id: str = Field(..., description="工作流 ID")
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="执行状态: succeeded/failed/running")
    result: str = Field(default="", description="执行结果文本")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    error: Optional[str] = Field(None, description="错误信息")
    elapsed_time: float = Field(default=0.0, description="执行耗时(秒)")
    total_tokens: int = Field(default=0, description="Token 使用量")
    created_at: Optional[int] = Field(None, description="创建时间 (时间戳)")
    finished_at: Optional[int] = Field(None, description="完成时间 (时间戳)")


class TaskStatus(BaseModel):
    """任务状态"""

    id: str = Field(..., alias="task_id", description="任务 ID")
    workflow_id: str = Field(..., description="工作流 ID")
    status: str = Field(..., description="任务状态: running/succeeded/failed/stopped")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="任务输入")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="任务输出")
    error: Optional[str] = Field(None, description="错误信息")
    elapsed_time: float = Field(default=0.0, description="执行耗时(秒)")
    total_tokens: int = Field(default=0, description="Token 使用量")
    created_at: Optional[int] = Field(None, description="创建时间 (时间戳)")
    finished_at: Optional[int] = Field(None, description="完成时间 (时间戳)")


class TaskStopResponse(BaseModel):
    """任务停止响应"""

    success: bool = Field(..., description="是否成功停止")
    message: str = Field(..., description="操作结果消息")


class WorkflowStreamEventData(BaseModel):
    """工作流流式事件数据"""

    # 节点事件字段
    id: Optional[str] = Field(None, description="节点/任务 ID")
    node_id: Optional[str] = Field(None, description="节点 ID")
    node_type: Optional[str] = Field(None, description="节点类型")
    title: Optional[str] = Field(None, description="节点标题")
    index: Optional[int] = Field(None, description="节点索引")
    predecessor_node_id: Optional[str] = Field(None, description="前置节点 ID")
    inputs: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="输入数据"
    )
    outputs: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="输出数据"
    )

    # 工作流事件字段
    workflow_id: Optional[str] = Field(None, description="工作流 ID")

    # 状态字段
    status: Optional[str] = Field(None, description="执行状态")
    elapsed_time: Optional[float] = Field(None, description="执行耗时(秒)")
    total_tokens: Optional[int] = Field(None, description="Token 使用量")
    total_steps: Optional[int] = Field(None, description="总步骤数")

    # 时间戳
    created_at: Optional[int] = Field(None, description="创建时间 (时间戳)")
    finished_at: Optional[int] = Field(None, description="完成时间 (时间戳)")


class WorkflowStreamEvent(BaseModel):
    """工作流流式事件"""

    event_type: str = Field(..., description="事件类型")
    task_id: Optional[str] = Field(None, description="任务 ID")
    workflow_run_id: Optional[str] = Field(None, description="工作流运行 ID")
    data: WorkflowStreamEventData = Field(
        default_factory=lambda: WorkflowStreamEventData(), description="事件数据"
    )

    class Config:
        """Pydantic 配置"""

        populate_by_name = True  # 支持别名
