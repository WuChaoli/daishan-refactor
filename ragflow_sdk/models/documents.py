"""
文档相关模型
"""

from typing import Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """文档模型"""

    id: str = Field(description="文档 ID")
    name: str = Field(description="文档名称")
    dataset_id: str = Field(description="所属数据集 ID")
    size: int = Field(default=0, description="文档大小（字节）")
    type: Optional[str] = Field(default=None, description="文档类型")
    chunk_num: int = Field(default=0, description="分块数量")
    status: str = Field(default="1", description="文档状态")
    progress: float = Field(default=0.0, description="处理进度")
    begin_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
    error: Optional[str] = Field(default=None, description="错误信息")

    class Config:
        """Pydantic 配置"""

        allow_population_by_field_name = True
        fields = {"chunk_num": "chunk_count"}


class DocumentCreate(BaseModel):
    """创建/上传文档请求"""

    name: Optional[str] = Field(default=None, description="文档名称")
    description: Optional[str] = Field(default=None, description="文档描述")


class DocumentUpdate(BaseModel):
    """更新文档请求"""

    name: Optional[str] = Field(default=None, description="文档名称")
    description: Optional[str] = Field(default=None, description="文档描述")


class DocumentListParams(BaseModel):
    """文档列表查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=1000, description="每页数量")
    orderby: Optional[str] = Field(default="create_time", description="排序字段")
    desc: bool = Field(default=True, description="是否降序")
    keywords: Optional[str] = Field(default=None, description="关键词搜索")
    id: Optional[str] = Field(default=None, description="文档 ID")
    name: Optional[str] = Field(default=None, description="文档名称")
