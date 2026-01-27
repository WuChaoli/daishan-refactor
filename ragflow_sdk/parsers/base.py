"""
Parser 基类模块

设计原则：
- 定义清晰的解析器接口
- 提供通用的解析工具方法
- 支持自定义解析逻辑
- 详细的错误信息
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from ..core.exceptions import ParseError

T = TypeVar("T", bound=BaseModel)


class BaseParser(ABC):
    """
    响应解析器基类

    所有解析器都应继承此类并实现 parse 方法
    """

    @abstractmethod
    def parse(self, response: requests.Response) -> Any:
        """
        解析 HTTP 响应

        Args:
            response: HTTP 响应对象

        Returns:
            解析后的数据

        Raises:
            ParseError: 解析失败时抛出
        """
        pass

    def parse_json(self, response: requests.Response) -> dict:
        """
        将响应解析为 JSON 字典

        Args:
            response: HTTP 响应对象

        Returns:
            JSON 字典

        Raises:
            ParseError: JSON 解析失败时抛出
        """
        try:
            return response.json()
        except Exception as e:
            raise ParseError(
                message="无法解析 JSON 响应",
                raw_data=response.text[:500] if hasattr(response, "text") else None,
                expected_format="JSON",
                details={
                    "content_type": response.headers.get("content-type", "unknown"),
                    "status_code": response.status_code,
                },
                original_error=e,
            )

    def validate_structure(
        self,
        data: dict,
        required_fields: Optional[list] = None,
        optional_fields: Optional[list] = None,
    ) -> bool:
        """
        验证数据结构

        Args:
            data: 响应数据
            required_fields: 必需的字段列表
            optional_fields: 可选的字段列表（用于提示）

        Returns:
            是否验证通过

        Raises:
            ParseError: 数据结构验证失败时抛出
        """
        if not isinstance(data, dict):
            raise ParseError(
                message="响应数据必须是字典类型",
                raw_data=str(data)[:500],
                expected_format="dict",
                details={"actual_type": type(data).__name__},
            )

        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ParseError(
                    message=f"响应数据缺少必需字段: {', '.join(missing_fields)}",
                    raw_data=str(data)[:500],
                    details={
                        "missing_fields": missing_fields,
                        "available_fields": list(data.keys()),
                        "optional_fields": optional_fields or [],
                    },
                )

        return True

    def parse_model(self, data: dict, model_class: Type[T]) -> T:
        """
        将数据解析为指定的 Pydantic 模型

        Args:
            data: 原始数据
            model_class: 目标模型类

        Returns:
            模型实例

        Raises:
            ParseError: 解析失败时抛出
        """
        try:
            return model_class(**data)
        except ValidationError as e:
            raise ParseError(
                message=f"无法解析为 {model_class.__name__} 模型",
                raw_data=str(data)[:500],
                expected_format=model_class.__name__,
                details={
                    "model_class": model_class.__name__,
                    "validation_errors": e.errors(),
                },
                original_error=e,
            )

    def extract_data(self, response: dict, data_key: str = "data") -> Any:
        """
        从响应中提取数据字段

        Args:
            response: 响应字典
            data_key: 数据字段名

        Returns:
            提取的数据

        Raises:
            ParseError: 数据字段不存在时抛出
        """
        if data_key not in response:
            raise ParseError(
                message=f"响应中缺少 '{data_key}' 字段",
                raw_data=str(response)[:500],
                details={"available_fields": list(response.keys())},
            )

        return response[data_key]
