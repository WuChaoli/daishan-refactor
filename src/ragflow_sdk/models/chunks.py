"""
Chunk 相关模型
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Chunk 模型"""

    id: str = Field(description="Chunk ID")
    document_id: Optional[str] = Field(default=None, description="所属文档 ID")
    dataset_id: Optional[str] = Field(default=None, description="所属数据集 ID")
    content: str = Field(description="Chunk 内容")
    keywords: Optional[List[str]] = Field(
        default_factory=list, description="关键词列表"
    )
    similarity: Optional[float] = Field(default=None, description="相似度分数")
    term_similarity: Optional[float] = Field(default=None, description="关键词相似度")
    vector_similarity: Optional[float] = Field(default=None, description="向量相似度")
    score: Optional[float] = Field(default=None, description="分数（similarity 别名）")

    class Config:
        """Pydantic 配置"""

        allow_population_by_field_name = True


class ChunkCreate(BaseModel):
    """创建 Chunk 请求"""

    content: str = Field(..., description="Chunk 内容")


class ChunkUpdate(BaseModel):
    """更新 Chunk 请求"""

    content: Optional[str] = Field(default=None, description="Chunk 内容")
    available: Optional[int] = Field(default=None, description="是否可用")


class RetrievalRequest(BaseModel):
    """检索请求"""

    question: str = Field(..., description="检索问题")
    dataset_ids: List[str] = Field(..., description="数据集 ID 列表")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=1024, description="每页数量")
    similarity_threshold: float = Field(
        default=0.2, ge=0.0, le=1.0, description="相似度阈值"
    )
    top_k: int = Field(default=1024, ge=1, description="向量检索数量")
