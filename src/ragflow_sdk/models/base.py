"""
基础数据模型

使用 Pydantic 提供类型安全和数据验证
"""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    基础响应模型

    RAGFlow API 的标准响应格式
    """

    code: int = Field(description="响应码，0 表示成功")
    message: str = Field(default="", description="响应消息")

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.code == 0

    @property
    def is_error(self) -> bool:
        """是否失败"""
        return self.code != 0


class DataResponse(BaseModel, Generic[T]):
    """
    数据响应模型

    包含 data 字段的响应
    """

    code: int = Field(description="响应码")
    message: str = Field(default="", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.code == 0


class PaginatedData(BaseModel, Generic[T]):
    """
    分页数据模型
    """

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数量")

    @property
    def has_more(self) -> bool:
        """是否有更多数据"""
        return len(self.items) < self.total

    def __len__(self) -> int:
        """返回当前页的数据数量"""
        return len(self.items)
