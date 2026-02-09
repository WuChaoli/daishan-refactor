"""
Dify 文件上传相关数据模型

定义文件上传请求和响应的 Pydantic 模型。
"""

from typing import Optional

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """文件上传响应"""

    id: str = Field(..., description="文件 ID,用于工作流输入")
    name: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小(字节)")
    mime_type: str = Field(..., description="MIME 类型")
    created_at: str = Field(..., description="上传时间戳")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "file-abc-123",
                    "name": "safety_report.pdf",
                    "size": 1024000,
                    "mime_type": "application/pdf",
                    "created_at": "1679586595",
                }
            ]
        }
    }
