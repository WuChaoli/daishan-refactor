"""
Dify SDK Blocking模式响应解析器
"""
import requests
from .base import BaseParser
from ..models.chat import ChatMessageResponse


class BlockParser(BaseParser):
    """
    Blocking模式响应解析器

    解析Dify Chat API的blocking模式响应，返回ChatMessageResponse对象。
    """

    def parse(self, response: requests.Response) -> ChatMessageResponse:
        """
        解析blocking响应为ChatMessageResponse

        Args:
            response: requests.Response对象

        Returns:
            ChatMessageResponse: 解析后的聊天消息响应对象

        Raises:
            DifyError: JSON解析失败或数据验证失败
        """
        data = self.parse_json(response)
        return ChatMessageResponse(**data)

    def parse_answer(self, response: requests.Response) -> str:
        """
        快速提取answer字段

        Args:
            response: requests.Response对象

        Returns:
            str: answer内容
        """
        data = self.parse_json(response)
        return self.extract_answer(data)
