"""Chunk 相关模型"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator


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
    dataset_ids: Optional[List[str]] = Field(
        default=None, description="数据集 ID 列表"
    )
    document_ids: Optional[List[str]] = Field(
        default=None, description="文档 ID 列表"
    )
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=1024, description="每页数量")
    similarity_threshold: float = Field(
        default=0.2, ge=0.0, le=1.0, description="相似度阈值"
    )
    vector_similarity_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="向量相似度权重"
    )
    top_k: int = Field(default=1024, ge=1, description="向量检索数量")
    rerank_id: Optional[Union[str, int]] = Field(
        default=None, description="重排序模型 ID"
    )
    keyword: bool = Field(default=False, description="是否启用关键词匹配")
    highlight: bool = Field(default=False, description="是否启用高亮")
    cross_languages: Optional[List[str]] = Field(
        default=None, description="跨语言关键词检索语言列表"
    )
    metadata_condition: Optional[Dict[str, Any]] = Field(
        default=None, description="元数据过滤条件"
    )
    use_kg: bool = Field(default=False, description="是否启用知识图谱检索")
    toc_enhance: bool = Field(default=False, description="是否启用 TOC 增强检索")

    @model_validator(mode="after")
    def validate_dataset_or_document_ids(self) -> "RetrievalRequest":
        """dataset_ids 与 document_ids 至少提供一个。"""
        if not self.dataset_ids and not self.document_ids:
            raise ValueError("dataset_ids 和 document_ids 至少需要提供一个")
        return self
