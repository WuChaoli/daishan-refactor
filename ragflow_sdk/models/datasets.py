"""
数据集相关模型
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Dataset(BaseModel):
    """数据集模型"""

    id: str = Field(description="数据集 ID")
    name: str = Field(description="数据集名称")
    description: Optional[str] = Field(default=None, description="数据集描述")
    chunk_num: int = Field(default=0, description="文档数量（或 chunk_count）")
    avatar: Optional[str] = Field(default=None, description="头像")
    chunk_method: str = Field(default="naive", description="分块方法")
    parser_id: Optional[str] = Field(default=None, description="解析器 ID")
    parser_config: Optional[Dict] = Field(
        default_factory=dict, description="解析器配置"
    )

    class Config:
        """Pydantic 配置"""

        populate_by_name = True
        # 支持字段别名，提高兼容性
        json_schema_extra = {"example": {"id": "dataset-123", "name": "示例数据集"}}


class DatasetCreate(BaseModel):
    """创建数据集请求"""

    name: str = Field(..., description="数据集名称")
    description: Optional[str] = Field(default=None, description="数据集描述")
    chunk_method: str = Field(default="naive", description="分块方法")
    parser_id: Optional[str] = Field(default=None, description="解析器 ID")
    parser_config: Optional[Dict] = Field(
        default_factory=dict, description="解析器配置"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """验证数据集名称不能为空"""
        if not v or not v.strip():
            raise ValueError("数据集名称不能为空")
        return v.strip()


class DatasetUpdate(BaseModel):
    """更新数据集请求"""

    name: Optional[str] = Field(default=None, description="数据集名称")
    description: Optional[str] = Field(default=None, description="数据集描述")
    chunk_method: Optional[str] = Field(default=None, description="分块方法")
    parser_id: Optional[str] = Field(default=None, description="解析器 ID")
    parser_config: Optional[Dict] = Field(default=None, description="解析器配置")


class DatasetListParams(BaseModel):
    """数据集列表查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=1000, description="每页数量")
    orderby: Optional[str] = Field(default="create_time", description="排序字段")
    desc: bool = Field(default=True, description="是否降序")
    name: Optional[str] = Field(default=None, description="数据集名称（模糊搜索）")
    id: Optional[str] = Field(default=None, description="数据集 ID（精确搜索）")
