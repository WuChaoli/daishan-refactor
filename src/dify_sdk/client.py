"""
Dify 工作流 API SDK 客户端

提供简洁的 Pythonic API 接口,用于与 Dify 工作流服务交互。
"""

from typing import Any, BinaryIO, Dict, Iterator, Optional

from .core.config import Config
from .core.exceptions import (DifyAPIError, DifyConnectionError,
                              DifyValidationError)
from .http.client import HTTPClient
from .models.chat import ChatMessageResponse, ChatStreamEvent
from .models.file import FileUploadResponse
from .models.workflow import (TaskStatus, TaskStopResponse,
                              WorkflowRunResponse, WorkflowStreamEvent)
from .parsers.base import BaseParser
from .parsers.streaming import StreamingParser


class DifyClient:
    """
    Dify 工作流 API 客户端主类

    提供简洁的 Pythonic API 接口,用于与 Dify 工作流服务交互。
    支持同步执行、流式执行、文件上传、任务管理等功能。

    示例:
        >>> # 使用环境变量
        >>> import os
        >>> os.environ['DIFY_API_KEY'] = 'your-api-key'
        >>> client = DifyClient()

        >>> # 使用构造参数
        >>> client = DifyClient(api_key='your-api-key')

        >>> # 执行工作流
        >>> response = client.run_workflow(
        ...     inputs={'query': '岱山园区有哪些企业?'},
        ...     user='user-123'
        ... )
        >>> print(response.result)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化 Dify 客户端

        Args:
            api_key: Dify API Key。如果为 None,则从环境变量 DIFY_API_KEY 读取
            base_url: Dify API Base URL。如果为 None,默认为 https://api.dify.ai
            timeout: HTTP 请求超时时间(秒),默认 30
            max_retries: 网络错误最大重试次数,默认 3

        Raises:
            ValueError: 当 API Key 未提供或环境变量中也未设置时
        """
        # 加载配置
        self.config = Config(
            api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries
        )

        # 初始化 HTTP 客户端
        self.http_client = HTTPClient(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        # 初始化 SSE 流式解析器
        self.streaming_parser = StreamingParser()

    # ============================================================
    # 类方法 - 从配置创建客户端
    # ============================================================

    @classmethod
    def from_config(
        cls,
        name: str,
        app_type: str = "workflow",
        config_path: Optional[str] = None,
        environment: str = "default",
        **kwargs,
    ) -> "DifyClient":
        """
        从配置文件创建客户端 (支持工作流和聊天应用)

        Args:
            name: 应用名称 (如 'safety_analysis', 'sql_result_formatter')
            app_type: 应用类型,可选值:
                - 'workflow': 工作流应用 (默认,向后兼容)
                - 'chat': 聊天应用
                - 未来可扩展: 'agent', 'completion' 等
            config_path: 配置文件路径,不指定则自动查找
            environment: 环境名称 (默认: 'default')
            **kwargs: 覆盖配置文件中的值

        Returns:
            DifyClient: 客户端实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: app_type 不支持或配置验证失败

        Example:
            >>> # 加载工作流 (默认)
            >>> client = DifyClient.from_config('safety_analysis')
            >>> # 等同于
            >>> client = DifyClient.from_config('safety_analysis', app_type='workflow')
            >>>
            >>> # 加载聊天应用
            >>> client = DifyClient.from_config('sql_result_formatter', app_type='chat')
            >>>
            >>> # 指定环境
            >>> client = DifyClient.from_config(
            ...     'qa_assistant',
            ...     app_type='chat',
            ...     environment='production'
            ... )
            >>>
            >>> # 覆盖配置
            >>> client = DifyClient.from_config(
            ...     'safety_analysis',
            ...     timeout=60
            ... )
        """
        # 验证 app_type
        supported_types = ["workflow", "chat"]
        if app_type not in supported_types:
            raise ValueError(
                f"不支持的 app_type: '{app_type}'. "
                f"支持的应用类型: {', '.join(supported_types)}"
            )

        # 根据 app_type 加载配置
        if app_type == "workflow":
            config = Config.from_workflows_config(
                workflow_name=name, config_path=config_path, environment=environment
            )
        elif app_type == "chat":
            config = Config.from_chats_config(
                chat_name=name, config_path=config_path, environment=environment
            )

        # 构造参数覆盖 (如果有)
        if kwargs:
            # 创建配置对象副本并应用覆盖
            config_dict = config.model_dump()
            config_dict.update(kwargs)
            config = Config(**config_dict)

        # 创建客户端
        return cls(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    # ============================================================
    # 工作流执行 - 同步模式
    # ============================================================

    def run_workflow(
        self,
        inputs: Dict[str, Any],
        user: Optional[str] = None,
        response_mode: str = "blocking",
        files: Optional[list[str]] = None,
        **kwargs,
    ) -> WorkflowRunResponse:
        """
        同步执行 Dify 工作流 (阻塞模式)

        此方法会等待工作流完全执行完成后返回结果。
        适合执行时间较短的工作流。

        Args:
            inputs: 工作流输入参数,键值对字典
            user: 用户标识符,用于隔离不同用户的会话
            response_mode: 响应模式,默认 "blocking"
            files: 文件 ID 列表,用于多模态输入
            **kwargs: 其他可选参数 (如 workflow_id)

        Returns:
            WorkflowRunResponse: 工作流执行结果

        Raises:
            DifyValidationError: 参数验证失败
            DifyAPIError: API 返回错误 (4xx, 5xx)
            DifyConnectionError: 网络连接错误

        示例:
            >>> response = client.run_workflow(
            ...     inputs={'query': '岱山园区有哪些企业?'},
            ...     user='user-123'
            ... )
            >>> print(f"状态: {response.status}")
            >>> print(f"结果: {response.result}")
        """
        # 参数验证
        if not inputs:
            raise DifyValidationError("inputs 参数不能为空")

        if response_mode not in ["blocking", "streaming"]:
            raise DifyValidationError(
                f"response_mode 必须是 'blocking' 或 'streaming',当前值: {response_mode}"
            )

        # 构建请求体
        request_data = {"inputs": inputs, "response_mode": "blocking", "user": user or "anonymous"}

        if files:
            request_data["files"] = files

        # 选择端点
        workflow_id = kwargs.get("workflow_id")
        if workflow_id:
            endpoint = f"/v1/workflows/{workflow_id}/run"
        else:
            endpoint = "/v1/workflows/run"

        # 发送 HTTP 请求
        response = self.http_client.post(endpoint=endpoint, json=request_data)

        # 解析响应
        response_data = response.json()

        # 转换为 Pydantic 模型
        return WorkflowRunResponse(**response_data)

    # ============================================================
    # 聊天应用执行 - 同步模式
    # ============================================================

    def run_chat(
        self,
        query: str,
        user: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        response_mode: str = "blocking",
        conversation_id: Optional[str] = None,
        files: Optional[list[str]] = None,
        parser: Optional[BaseParser] = None,
        **kwargs,
    ) -> ChatMessageResponse:
        """
        同步执行 Dify 聊天应用 (阻塞模式)

        此方法会等待聊天应用完全执行完成后返回结果。
        适合聊天机器人、对话问答等场景。

        Args:
            query: 用户查询/问题
            user: 用户标识符,用于隔离不同用户的会话
            inputs: 额外输入参数,键值对字典
            response_mode: 响应模式,默认 "blocking"
            conversation_id: 对话 ID,用于多轮对话
            files: 文件 ID 列表,用于多模态输入
            parser: 自定义响应解析器。如果为 None,使用默认的 BlockParser
            **kwargs: 其他可选参数

        Returns:
            ChatMessageResponse: 聊天消息响应

        Raises:
            DifyValidationError: 参数验证失败
            DifyAPIError: API 返回错误 (4xx, 5xx)
            DifyConnectionError: 网络连接错误

        示例:
            >>> response = client.run_chat(
            ...     query='岱山园区有哪些企业?',
            ...     user='user-123'
            ... )
            >>> print(f"回答: {response.answer}")
        """
        # 参数验证
        if not query:
            raise DifyValidationError("query 参数不能为空")

        if response_mode not in ["blocking", "streaming"]:
            raise DifyValidationError(
                f"response_mode 必须是 'blocking' 或 'streaming',当前值: {response_mode}"
            )

        # 构建请求体
        request_data = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": response_mode,
            "user": user or "anonymous",
            "conversation_id": conversation_id or "",
        }

        if files:
            request_data["files"] = files

        # 发送 HTTP 请求 (聊天端点)
        response = self.http_client.post(
            endpoint="/v1/chat-messages", json=request_data
        )

        # 使用自定义parser或默认BlockParser
        if parser is None:
            from .parsers.block import BlockParser
            parser = BlockParser()
        return parser.parse(response)

    # ============================================================
    # 聊天应用执行 - 流式模式
    # ============================================================

    def run_chat_streaming(
        self,
        query: str,
        user: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        files: Optional[list[str]] = None,
        parser: Optional[BaseParser] = None,
        **kwargs,
    ) -> Iterator[ChatStreamEvent]:
        """
        流式执行 Dify 聊天应用 (SSE 模式)

        通过 Server-Sent Events (SSE) 实时返回聊天响应事件。
        适合需要实时显示回答内容的场景。

        Args:
            query: 用户查询/问题
            user: 用户标识符
            inputs: 额外输入参数
            conversation_id: 对话 ID,用于多轮对话
            files: 文件 ID 列表
            parser: 自定义响应解析器。如果为 None,使用默认的 ChatStreamingParser
            **kwargs: 其他可选参数

        Yields:
            ChatStreamEvent: 聊天流式事件

        Raises:
            DifyValidationError: 参数验证失败
            DifyConnectionError: 网络连接错误或 SSE 流中断

        示例:
            >>> for event in client.run_chat_streaming(
            ...     query='分析企业安全风险',
            ...     user='user-123'
            ... ):
            ...     if event.event_type == 'message':
            ...         print(f"回答片段: {event.answer}")
            ...     elif event.event_type == 'message_end':
            ...         print(f"对话完成: {event.message_id}")
        """
        # 参数验证
        if not query:
            raise DifyValidationError("query 参数不能为空")

        # 构建请求体
        request_data = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user or "anonymous",
            "conversation_id": conversation_id or "",
        }

        if files:
            request_data["files"] = files

        # 发送 HTTP 请求 (流式响应)
        response = self.http_client.post_stream(
            endpoint="/v1/chat-messages", json=request_data
        )

        # 使用自定义parser或默认ChatStreamingParser
        if parser is None:
            from .parsers.streaming import ChatStreamingParser
            parser = ChatStreamingParser()
        for chat_event in parser.parse(response):
            yield chat_event

    # ============================================================
    # 工作流执行 - 流式模式
    # ============================================================

    def run_workflow_streaming(
        self,
        inputs: Dict[str, Any],
        user: Optional[str] = None,
        files: Optional[list[str]] = None,
        **kwargs,
    ) -> Iterator[WorkflowStreamEvent]:
        """
        流式执行 Dify 工作流 (SSE 模式)

        通过 Server-Sent Events (SSE) 实时返回工作流执行事件。
        适合执行时间较长的工作流,或需要实时监控执行进度的场景。

        Args:
            inputs: 工作流输入参数,键值对字典
            user: 用户标识符
            files: 文件 ID 列表 (可选)
            **kwargs: 其他可选参数 (如 workflow_id)

        Yields:
            WorkflowStreamEvent: 工作流执行事件

        Raises:
            DifyValidationError: 参数验证失败
            DifyConnectionError: 网络连接错误或 SSE 流中断

        示例:
            >>> for event in client.run_workflow_streaming(
            ...     inputs={'query': '分析企业安全风险'},
            ...     user='user-123'
            ... ):
            ...     if event.event_type == 'node_started':
            ...         print(f"🚀 节点开始: {event.data.title}")
            ...     elif event.event_type == 'workflow_finished':
            ...         print(f"🎉 工作流完成,状态: {event.data.status}")
        """
        # 参数验证
        if not inputs:
            raise DifyValidationError("inputs 参数不能为空")

        # 构建请求体
        request_data = {"inputs": inputs, "response_mode": "streaming", "user": user or "anonymous"}

        if files:
            request_data["files"] = files

        # 选择端点
        workflow_id = kwargs.get("workflow_id")
        if workflow_id:
            endpoint = f"/v1/workflows/{workflow_id}/run"
        else:
            endpoint = "/v1/workflows/run"

        # 发送 HTTP 请求 (流式响应)
        response = self.http_client.post_stream(endpoint=endpoint, json=request_data)

        # 解析 SSE 流
        for event in self.streaming_parser.parse_events(response):
            yield event

    # ============================================================
    # 执行指定版本的工作流
    # ============================================================

    def run_workflow_by_id(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        user: Optional[str] = None,
        response_mode: str = "blocking",
        files: Optional[list[str]] = None,
    ) -> WorkflowRunResponse:
        """
        执行指定版本的工作流

        通过 workflow_id 指定要执行的工作流版本,
        而非使用默认发布的版本。

        Args:
            workflow_id: 工作流 ID (从 Dify 控制台获取)
            inputs: 工作流输入参数
            user: 用户标识符
            response_mode: 响应模式,默认 "blocking"
            files: 文件 ID 列表 (可选)

        Returns:
            WorkflowRunResponse: 工作流执行结果

        Raises:
            DifyValidationError: workflow_id 格式错误或参数验证失败
            DifyAPIError: 工作流不存在或执行失败 (404, 400)
            DifyConnectionError: 网络连接错误

        示例:
            >>> response = client.run_workflow_by_id(
            ...     workflow_id='workflow-abc-123',
            ...     inputs={'query': '查询隐患数据'},
            ...     user='user-123'
            ... )
            >>> print(response.result)
        """
        # 参数验证
        if not workflow_id or not isinstance(workflow_id, str):
            raise DifyValidationError("workflow_id 必须是非空字符串")

        # 复用 run_workflow 方法,传入 workflow_id
        return self.run_workflow(
            inputs=inputs,
            user=user,
            response_mode=response_mode,
            files=files,
            workflow_id=workflow_id,
        )

    # ============================================================
    # 任务管理 - 查询任务状态
    # ============================================================

    def get_task(self, task_id: str) -> TaskStatus:
        """
        查询工作流任务的执行状态和结果

        Args:
            task_id: 任务 ID,从工作流执行响应中获取

        Returns:
            TaskStatus: 任务状态对象

        Raises:
            DifyValidationError: task_id 为空或格式错误
            DifyAPIError: 任务不存在 (404) 或其他 API 错误
            DifyConnectionError: 网络连接错误

        示例:
            >>> status = client.get_task('task-abc-123')
            >>> if status.status == 'succeeded':
            ...     print(f"结果: {status.outputs}")
            >>> elif status.status == 'running':
            ...     print("任务仍在执行中...")
        """
        # 参数验证
        if not task_id or not isinstance(task_id, str):
            raise DifyValidationError("task_id 必须是非空字符串")

        # 构建端点
        endpoint = f"/v1/workflows/tasks/{task_id}"

        # 发送 GET 请求
        response = self.http_client.get(endpoint=endpoint)

        # 解析响应
        response_data = response.json()

        # 转换为 Pydantic 模型
        return TaskStatus(**response_data)

    # ============================================================
    # 任务管理 - 停止任务
    # ============================================================

    def stop_task(self, task_id: str) -> TaskStopResponse:
        """
        停止正在执行的工作流任务

        Args:
            task_id: 要停止的任务 ID

        Returns:
            TaskStopResponse: 停止操作结果

        Raises:
            DifyValidationError: task_id 为空或格式错误
            DifyAPIError: 任务不存在或已完成 (404, 400)
            DifyConnectionError: 网络连接错误

        示例:
            >>> result = client.stop_task('task-abc-123')
            >>> if result.success:
            ...     print("任务已停止")
        """
        # 参数验证
        if not task_id or not isinstance(task_id, str):
            raise DifyValidationError("task_id 必须是非空字符串")

        # 构建端点
        endpoint = f"/v1/workflows/tasks/{task_id}/stop"

        # 发送 POST 请求
        try:
            response = self.http_client.post(endpoint=endpoint, json={})
        except DifyAPIError as e:
            # 处理特殊错误码
            if e.status_code == 404:
                return TaskStopResponse(success=False, message=f"任务不存在: {task_id}")
            if e.status_code == 400:
                return TaskStopResponse(success=False, message="任务已完成或无法停止")
            raise

        # 解析成功响应
        response_data = response.json()
        return TaskStopResponse(**response_data)

    # ============================================================
    # 文件上传
    # ============================================================

    def upload_file(
        self, file: BinaryIO, filename: Optional[str] = None
    ) -> FileUploadResponse:
        """
        上传文件到 Dify,用于多模态工作流输入

        支持的文件类型: 文本文件 (TXT, PDF, MD, DOCX 等)、图片等

        Args:
            file: 文件对象 (支持 read() 方法的二进制文件对象)
            filename: 文件名 (可选,如果未提供则尝试从 file 对象获取)

        Returns:
            FileUploadResponse: 文件上传结果

        Raises:
            DifyValidationError: 文件对象无效或文件类型不支持
            DifyAPIError: 文件过大 (413) 或上传失败
            DifyConnectionError: 网络连接错误

        示例:
            >>> with open('safety_report.pdf', 'rb') as f:
            ...     upload_response = client.upload_file(f)
            >>> print(f"文件 ID: {upload_response.id}")
            >>>
            >>> # 使用文件 ID 执行工作流
            >>> response = client.run_workflow(
            ...     inputs={'file': [upload_response.id]},
            ...     user='user-123'
            ... )
        """
        # 参数验证
        if not file:
            raise DifyValidationError("file 参数不能为空")

        if not hasattr(file, "read"):
            raise DifyValidationError("file 必须是文件对象 (支持 read() 方法)")

        # 获取文件名
        if filename is None:
            if hasattr(file, "name"):
                filename = file.name
            else:
                raise DifyValidationError("无法确定文件名,请提供 filename 参数")

        # 读取文件内容
        try:
            file_content = file.read()
        except Exception as e:
            raise DifyValidationError(f"读取文件失败: {str(e)}")

        # 验证文件大小 (15MB 限制)
        MAX_FILE_SIZE = 15 * 1024 * 1024
        if len(file_content) > MAX_FILE_SIZE:
            raise DifyValidationError(
                f"文件过大 ({len(file_content)} 字节),最大支持 {MAX_FILE_SIZE} 字节"
            )

        # 验证文件类型
        ALLOWED_EXTENSIONS = {
            ".txt",
            ".pdf",
            ".md",
            ".markdown",
            ".docx",
            ".doc",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
        }

        file_ext = ""
        if filename and "." in filename:
            file_ext = "." + filename.split(".")[-1].lower()
        if file_ext and file_ext not in ALLOWED_EXTENSIONS:
            raise DifyValidationError(
                f"不支持的文件类型: {file_ext},支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 构建 multipart/form-data 请求
        files = {"file": (filename, file_content)}

        # 发送上传请求
        response = self.http_client.post_multipart(
            endpoint="/v1/files/upload", files=files
        )

        # 解析响应
        response_data = response.json()
        return FileUploadResponse(**response_data)

    # ============================================================
    # 工作流日志查询 (流式)
    # ============================================================

    def get_workflow_logs(self, workflow_run_id: str) -> Iterator[WorkflowStreamEvent]:
        """
        获取工作流执行的详细日志 (流式)

        返回工作流执行过程中各个节点的详细日志信息,
        包括输入、输出、执行时间等。

        Args:
            workflow_run_id: 工作流执行 ID (从 WorkflowRunResponse 中获取)

        Yields:
            WorkflowStreamEvent: 日志事件

        Raises:
            DifyValidationError: workflow_run_id 为空或格式错误
            DifyConnectionError: 网络连接错误或 SSE 流中断

        示例:
            >>> for log in client.get_workflow_logs('run-abc-123'):
            ...     if log.event_type == 'node_finished':
            ...         print(f"节点 {log.data.node_id} 完成")
            ...         print(f"输入: {log.data.inputs}")
            ...         print(f"输出: {log.data.outputs}")
        """
        # 参数验证
        if not workflow_run_id or not isinstance(workflow_run_id, str):
            raise DifyValidationError("workflow_run_id 必须是非空字符串")

        # 构建查询参数
        params = {"workflow_run_id": workflow_run_id}

        # 发送 SSE 请求
        response = self.http_client.get_stream(
            endpoint="/v1/workflows/logs", params=params
        )

        # 解析 SSE 流
        for event in self.streaming_parser.parse_events(response):
            yield event

    # ============================================================
    # 便捷方法
    # ============================================================

    def run_and_wait(
        self,
        inputs: Dict[str, Any],
        user: Optional[str] = None,
        check_interval: float = 1.0,
        timeout: int = 300,
        **kwargs,
    ) -> WorkflowRunResponse:
        """
        执行工作流并等待完成 (轮询模式)

        对于不支持流式模式的场景,此方法通过轮询任务状态
        等待工作流执行完成。

        Args:
            inputs: 工作流输入参数
            user: 用户标识符
            check_interval: 轮询间隔(秒),默认 1 秒
            timeout: 超时时间(秒),默认 300 秒 (5分钟)
            **kwargs: 其他参数传递给 run_workflow()

        Returns:
            WorkflowRunResponse: 工作流执行结果

        Raises:
            DifyValidationError: 参数验证失败
            DifyConnectionError: 网络连接错误
            TimeoutError: 等待超时

        示例:
            >>> try:
            ...     response = client.run_and_wait(
            ...         inputs={'query': '长时间运行的任务'},
            ...         user='user-123',
            ...         timeout=600  # 10分钟超时
            ...     )
            ...     print(response.result)
            ... except TimeoutError:
            ...     print("工作流执行超时")
        """
        import time

        # 执行工作流 (获取 task_id)
        run_response = self.run_workflow(inputs=inputs, user=user, **kwargs)

        task_id = run_response.task_id

        # 如果工作流已经完成,直接返回
        if run_response.status in ["succeeded", "failed"]:
            return run_response

        # 轮询任务状态
        start_time = time.time()

        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError(f"等待工作流完成超时 (超过 {timeout} 秒)")

            # 查询任务状态
            task_status = self.get_task(task_id)

            # 如果完成,返回结果
            if task_status.status == "succeeded":
                return WorkflowRunResponse(
                    workflow_id=task_status.workflow_id,
                    task_id=task_status.id,
                    status="succeeded",
                    result=task_status.outputs.get("result", ""),
                    outputs=task_status.outputs,
                    elapsed_time=task_status.elapsed_time,
                    total_tokens=task_status.total_tokens,
                    created_at=task_status.created_at,
                    finished_at=task_status.finished_at,
                )

            if task_status.status == "failed":
                raise DifyAPIError(
                    message=f"工作流执行失败: {task_status.error}", status_code=500
                )

            if task_status.status == "stopped":
                raise DifyAPIError(message="工作流已被停止", status_code=400)

            # 等待后继续轮询
            time.sleep(check_interval)

    # ============================================================
    # 上下文管理器支持
    # ============================================================

    def __enter__(self):
        """
        支持上下文管理器协议

        示例:
            >>> with DifyClient(api_key='your-api-key') as client:
            ...     response = client.run_workflow(...)
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        清理资源 (关闭 HTTP 连接)
        """
        self.http_client.close()
