"""
Dify SDK 响应解析器基类
"""
from abc import ABC, abstractmethod
from typing import Any
import requests
import json


class BaseParser(ABC):
    """
    Dify响应解析器基类

    提供通用的解析能力和工具方法，子类需实现具体的parse方法。
    """

    @abstractmethod
    def parse(self, response: requests.Response) -> Any:
        """
        解析响应 - 子类必须实现

        Args:
            response: requests.Response对象

        Returns:
            Any: 解析后的数据，具体类型由子类决定
        """
        pass

    def parse_json(self, response: requests.Response) -> dict:
        """
        解析JSON响应

        Args:
            response: requests.Response对象

        Returns:
            dict: 解析后的JSON数据

        Raises:
            DifyError: JSON解析失败
        """
        try:
            return response.json()
        except json.JSONDecodeError as e:
            from ..core.exceptions import DifyError
            raise DifyError(f"JSON解析失败: {str(e)}")

    def extract_answer(self, data: dict) -> str:
        """
        提取answer字段 - 通用逻辑

        Args:
            data: 包含answer字段的字典

        Returns:
            str: answer内容，如果不存在则返回空字符串
        """
        return data.get("answer", "")
