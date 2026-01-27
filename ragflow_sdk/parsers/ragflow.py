"""
RAGFlow API 响应解析器

设计原则：
- 继承自 BaseParser
- 处理 RAGFlow API 的特定响应格式
- 提供类型安全的解析方法
- 支持多种响应格式（单对象、列表、分页等）
"""

from typing import Any, List, Optional, Type

import requests
from pydantic import BaseModel

from ..core.exceptions import ParseError
from .base import BaseParser, T


class RAGFlowParser(BaseParser):
    """
    RAGFlow API 响应解析器

    处理 RAGFlow API 的标准响应格式：
    {
        "code": 0,           # 0 表示成功
        "message": "...",    # 消息
        "data": {...}        # 数据
    }

    支持的响应类型：
    - 单对象: {"code": 0, "data": {...}}
    - 列表: {"code": 0, "data": {"items": [...], "total": 100}}
    - 直接列表: {"code": 0, "data": [...]}
    """

    # 可能包含列表数据的字段名
    LIST_FIELDS = [
        "items",
        "datasets",
        "documents",
        "chunks",
        "chats",
        "sessions",
        "agents",
    ]

    def parse(self, response: requests.Response) -> dict:
        """
        解析 HTTP 响应为字典

        Args:
            response: HTTP 响应对象

        Returns:
            解析后的字典

        Raises:
            ParseError: 解析失败时抛出
        """
        # 解析 JSON
        data = self.parse_json(response)

        # 验证基本结构
        self.validate_structure(data, required_fields=["code"])

        # 检查业务错误码
        code = data.get("code")
        if code != 0:
            message = data.get("message", "Unknown error")
            raise ParseError(
                message=f"API 返回错误: {message}",
                raw_data=str(data)[:500],
                details={"code": code, "message": message},
            )

        return data

    def parse_data(self, response: requests.Response) -> Any:
        """
        提取响应中的 data 字段

        Args:
            response: HTTP 响应对象

        Returns:
            data 字段的内容
        """
        parsed = self.parse(response)
        return self.extract_data(parsed, "data")

    def parse_object(self, response: requests.Response, model_class: Type[T]) -> T:
        """
        解析为单个模型对象

        Args:
            response: HTTP 响应对象
            model_class: 目标模型类

        Returns:
            模型实例
        """
        data = self.parse_data(response)

        # 如果 data 为 None，返回空模型
        if data is None:
            return model_class()

        # 如果 data 是字典，解析为模型
        if isinstance(data, dict):
            return self.parse_model(data, model_class)

        raise ParseError(
            message=f"无法将响应解析为 {model_class.__name__}",
            raw_data=str(data)[:500],
            expected_format=f"dict (for {model_class.__name__})",
            details={"actual_type": type(data).__name__},
        )

    def parse_list(self, response: requests.Response, model_class: Type[T]) -> List[T]:
        """
        解析为模型列表

        Args:
            response: HTTP 响应对象
            model_class: 目标模型类

        Returns:
            模型实例列表
        """
        data = self.parse_data(response)

        # 如果 data 为 None，返回空列表
        if data is None:
            return []

        items = []

        # 尝试从字典中提取列表
        if isinstance(data, dict):
            # 查找包含列表的字段
            for field in self.LIST_FIELDS:
                if field in data and isinstance(data[field], list):
                    items = data[field]
                    break

            # 如果没有找到，检查是否有其他列表字段
            if not items:
                for key, value in data.items():
                    if isinstance(value, list):
                        items = value
                        break
        elif isinstance(data, list):
            items = data

        # 解析列表项
        result = []
        for item in items:
            result.append(self.parse_model(item, model_class))

        return result

    def parse_paginated(
        self, response: requests.Response, model_class: Type[T]
    ) -> dict:
        """
        解析为分页数据

        Args:
            response: HTTP 响应对象
            model_class: 目标模型类

        Returns:
            包含 items 和 total 的字典
        """
        data = self.parse_data(response)

        # 如果 data 是 list,直接使用(这是 RAGFlow API 的实际返回格式)
        if isinstance(data, list):
            items_data = data
            total = len(items_data)
        # 如果 data 是 dict,尝试提取列表字段
        elif isinstance(data, dict):
            # 提取列表项
            items_data = []
            for field in self.LIST_FIELDS:
                if field in data and isinstance(data[field], list):
                    items_data = data[field]
                    break

            # 获取总数
            total = data.get("total", len(items_data))
        else:
            raise ParseError(
                message="分页响应的 data 字段必须是字典或列表",
                raw_data=str(data)[:500],
                expected_format="dict with 'items' and 'total' or list",
                details={"actual_type": type(data).__name__},
            )

        # 解析列表项
        items = []
        for item in items_data:
            items.append(self.parse_model(item, model_class))

        return {
            "items": items,
            "total": total,
        }

    def parse_text(self, response: requests.Response) -> str:
        """
        解析为纯文本

        Args:
            response: HTTP 响应对象

        Returns:
            响应文本
        """
        try:
            return response.text
        except Exception as e:
            raise ParseError(
                message="无法解析响应文本",
                raw_data=None,
                details={"exception": str(e)},
                original_error=e,
            )


class StreamingParser(BaseParser):
    """
    流式响应解析器

    用于处理 Server-Sent Events (SSE) 格式的流式响应
    """

    def parse(self, response: requests.Response) -> Any:
        """
        解析流式响应

        Args:
            response: HTTP 响应对象

        Returns:
            解析后的数据块列表
        """
        lines = response.text.strip().split("\n")
        results = []

        for line in lines:
            if line.startswith("data:"):
                data_str = line[5:].strip()

                # 检查结束标记
                if data_str == "[DONE]":
                    continue

                # 解析 JSON 数据
                try:
                    import json

                    data = json.loads(data_str)
                    results.append(data)
                except Exception:
                    continue

        return results

    def parse_stream(self, response: requests.Response) -> List[dict]:
        """
        解析流式响应为数据块列表

        Args:
            response: HTTP 响应对象

        Returns:
            数据块列表
        """
        return self.parse(response)

    def parse_combined(self, response: requests.Response) -> dict:
        """
        解析流式响应并合并为单个响应

        Args:
            response: HTTP 响应对象

        Returns:
            合并后的响应
        """
        chunks = self.parse(response)

        if not chunks:
            return {}

        # 返回最后一个数据块（通常包含完整的响应）
        return chunks[-1]
