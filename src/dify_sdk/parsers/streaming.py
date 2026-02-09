"""
Dify SDK SSE 流式响应解析器

解析 Server-Sent Events (SSE) 格式的流式响应。
"""

import json
import time
from typing import Iterator

import requests

from .base import BaseParser
from ..models.workflow import WorkflowStreamEvent
from ..models.chat import ChatStreamEvent


class StreamingParser:
    """
    SSE 流式响应解析器

    解析 Dify API 返回的 SSE 格式流式响应。

    SSE 格式示例:
        data: {"event": "node_started", "task_id": "...", "data": {...}}
        data: {"event": "workflow_finished", ...}
    """

    def parse_events(
        self, response: requests.Response
    ) -> Iterator[WorkflowStreamEvent]:
        """
        解析 SSE 流式响应

        Args:
            response: requests.Response 对象 (stream=True)

        Yields:
            WorkflowStreamEvent: 解析后的事件对象

        Raises:
            DifyConnectionError: SSE 流解析失败或连接中断
        """
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                # 跳过注释和心跳
                if line.startswith(":"):
                    continue

                # 解析 "data: {...}" 格式
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀

                    try:
                        # 解析 JSON
                        event_data = json.loads(data_str)

                        # 转换为 WorkflowStreamEvent
                        event = self._parse_event_data(event_data)

                        yield event

                    except json.JSONDecodeError as e:
                        # JSON 解析失败,跳过该行
                        continue

        except requests.exceptions.RequestException as e:
            from ..core.exceptions import DifyConnectionError

            raise DifyConnectionError(
                message=f"SSE 连接中断: {str(e)}", original_error=e
            )

    def _parse_event_data(self, data: dict) -> WorkflowStreamEvent:
        """
        解析事件数据

        Args:
            data: 从 SSE 解析出的原始数据

        Returns:
            WorkflowStreamEvent: 标准化的事件对象
        """
        # 提取事件类型
        event_type = data.get("event", "unknown")

        # 提取 task_id 和 workflow_run_id
        task_id = data.get("task_id")
        workflow_run_id = data.get("workflow_run_id")

        # 提取事件数据
        event_data = data.get("data", {})

        # 构建标准化事件对象
        return WorkflowStreamEvent(
            event_type=event_type,
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            data=event_data,
        )


class ChatStreamingParser(BaseParser):
    """
    Chat流式响应解析器

    解析Dify Chat API的SSE流式响应，逐个yield ChatStreamEvent。
    """

    def parse(self, response: requests.Response) -> Iterator[ChatStreamEvent]:
        """
        解析SSE流，yield ChatStreamEvent

        Args:
            response: requests.Response对象 (stream=True)

        Yields:
            ChatStreamEvent: 解析后的聊天流式事件

        Raises:
            DifyConnectionError: SSE流解析失败或连接中断
        """
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                # 跳过注释和心跳
                if line.startswith(":"):
                    continue

                # 解析 "data: {...}" 格式
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀

                    try:
                        # 解析 JSON
                        event_data = json.loads(data_str)

                        # 转换为 ChatStreamEvent
                        event = self._parse_event(event_data)

                        yield event

                    except json.JSONDecodeError:
                        # JSON 解析失败,跳过该行
                        continue

        except requests.exceptions.RequestException as e:
            from ..core.exceptions import DifyConnectionError

            raise DifyConnectionError(
                message=f"SSE 连接中断: {str(e)}", original_error=e
            )

    def _parse_event(self, data: dict) -> ChatStreamEvent:
        """
        解析单个SSE事件数据

        Args:
            data: 从SSE解析出的原始数据

        Returns:
            ChatStreamEvent: 标准化的聊天事件对象
        """
        return ChatStreamEvent(
            event_type=data.get("event", "unknown"),
            message_id=data.get("message_id"),
            conversation_id=data.get("conversation_id"),
            task_id=data.get("task_id"),
            answer=data.get("answer"),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            workflow_id=data.get("workflow_id"),
            status=data.get("status"),
            elapsed_time=data.get("elapsed_time"),
        )

    def parse_answers(self, response: requests.Response) -> Iterator[str]:
        """
        流式提取answer字段
        
        Args:
            response: requests.Response对象 (stream=True)
        
        Yields:
            str: answer内容片段
        """
        for event in self.parse(response):
            if event.answer:
                yield event.answer


class DaishanStreamingParser(BaseParser):
    """
    Daishan 统一流式响应解析器

    将 Dify ChatStreamEvent 转换为统一 SSE 格式，
    与 convert_json_to_stream 输出格式完全一致。

    格式示例:
        event: start
        data: {"message":"开始流式输出"}

        id: 1
        event: message
        data: {"content":"Hel","type":"chunk"}

        event: complete
        data: {"message":"流式输出已完成"}

        event: end
        data: [DONE]

    Args:
        chunk_size: 分块大小，默认 3 字符
        chunk_delay: 分块延迟（秒），默认 0.02 秒
        include_metadata: 是否包含元数据，默认 True

    Usage:
        >>> parser = DaishanStreamingParser(chunk_size=3, chunk_delay=0.02)
        >>> for event in parser.parse(response):
        ...     yield event
    """

    def __init__(
        self,
        chunk_size: int = 3,
        chunk_delay: float = 0.02,
        include_metadata: bool = True,
    ):
        """
        初始化解析器

        Args:
            chunk_size: 每个消息块的大小（字符数）
            chunk_delay: 发送每个块的延迟时间（秒）
            include_metadata: 是否在 start 事件中包含元数据
        """
        self.chunk_size = chunk_size
        self.chunk_delay = chunk_delay
        self.include_metadata = include_metadata

    def parse(self, response: requests.Response) -> Iterator[str]:
        """
        解析 Dify SSE 流，转换为统一格式

        真正的流式输出：边接收 Dify 事件，边输出统一格式事件

        Args:
            response: requests.Response 对象 (stream=True)

        Yields:
            str: SSE 格式的事件字符串

        Raises:
            DifyConnectionError: SSE 连接中断或解析失败
        """
        try:
            # 复用 ChatStreamingParser
            dify_parser = ChatStreamingParser()
            
            metadata = {}
            message_id = 0
            start_yielded = False
            has_answer = False
            
            # 实时处理每个 Dify 事件
            for event in dify_parser.parse(response):
                # 提取元数据（只取第一次）
                if not metadata and any(
                    [
                        event.message_id,
                        event.conversation_id,
                        event.task_id,
                        event.workflow_id,
                    ]
                ):
                    metadata = {
                        k: v
                        for k, v in {
                            "message_id": event.message_id,
                            "conversation_id": event.conversation_id,
                            "task_id": event.task_id,
                            "workflow_id": event.workflow_id,
                        }.items()
                        if v is not None
                    }
                
                # 收集 answer
                if event.answer:
                    has_answer = True
                    
                    # 生成 start 事件（如果还没生成过）
                    if not start_yielded:
                        start_yielded = True
                        yield self._yield_start_event(metadata)
                    
                    # 分块发送 message 事件（流式输出）
                    for i in range(0, len(event.answer), self.chunk_size):
                        chunk = event.answer[i : i + self.chunk_size]
                        message_id += 1
                        yield (
                            f"id: {message_id}\n"
                            f"event: message\n"
                            f"data: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
                        )
                        # 模拟打字机效果
                        time.sleep(self.chunk_delay)
            
            # 如果没有任何 answer，至少生成 start, complete, end
            if not has_answer:
                if not start_yielded:
                    yield self._yield_start_event(metadata)
                yield self._yield_complete_event()
                yield self._yield_end_event()
            else:
                # 生成 complete 和 end 事件
                yield self._yield_complete_event()
                yield self._yield_end_event()

        except Exception as e:
            # 错误处理
            error_msg = f"流式转换异常: {str(e)}"
            yield self._yield_error_event(error_msg)

    def _yield_start_event(self, metadata: dict) -> str:
        """
        生成 start 事件

        Args:
            metadata: 元数据字典

        Returns:
            str: SSE 格式的 start 事件
        """
        start_data = {"message": "开始流式输出"}

        # 可选：包含元数据
        if self.include_metadata and metadata:
            start_data["metadata"] = metadata

        return (
            f"event: start\ndata: {json.dumps(start_data, ensure_ascii=False)}\n\n"
        )

    def _yield_message_chunks(self, text: str) -> Iterator[str]:
        """
        分块发送 message 事件

        Args:
            text: 完整文本内容

        Yields:
            str: SSE 格式的 message 事件
        """
        message_id = 0
        chunk_size = self.chunk_size

        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            message_id += 1

            event_str = (
                f"id: {message_id}\n"
                f"event: message\n"
                f"data: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
            )

            yield event_str

            # 模拟打字机效果
            time.sleep(self.chunk_delay)

    def _yield_complete_event(self) -> str:
        """
        生成 complete 事件

        Returns:
            str: SSE 格式的 complete 事件
        """
        return (
            f"event: complete\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\n\n"
        )

    def _yield_end_event(self) -> str:
        """
        生成 end 事件

        Returns:
            str: SSE 格式的 end 事件
        """
        return "event: end\ndata: [DONE]\n\n"

    def _yield_error_event(self, error_msg: str) -> str:
        """
        生成 error 事件

        Args:
            error_msg: 错误消息

        Returns:
            str: SSE 格式的 error 事件
        """
        return (
            f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
        )
