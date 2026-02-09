"""
Dify SDK 配置管理

管理 SDK 的配置项,支持从环境变量、构造参数和配置文件加载配置。
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from .config_loader import (find_config_file, load_chat_config,
                            load_config_file, validate_config)


class Config(BaseSettings):
    """
    Dify SDK 配置类

    支持从环境变量和构造参数加载配置。
    构造参数优先级高于环境变量。

。

    Attributes:
        api_key: Dify API Key (必需)
        base_url: Dify API Base URL
        timeout: HTTP 请求超时时间(秒)
        max_retries: 网络错误最大重试次数
    """

    # 从环境变量读取的配置
    api_key: str = Field(default="", description="Dify API Key")
    base_url: str = Field(default="https://api.dify.ai", description="Dify API Base URL")
    timeout: int = Field(default=30, description="HTTP 请求超时时间(秒)")
    max_retries: int = Field(default=3, description="网络错误最大重试次数")

    class Config:
        """Pydantic 配置"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略额外字段(如 workflow_id)

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        **kwargs,
    ):
        """
        初始化配置

        Args:
            api_key: Dify API Key。如果为 None,则从环境变量读取
            base_url: API Base URL。如果为 None,则从环境变量读取,默认为 https://api.dify.ai
            timeout: 请求超时时间(秒)。如果为 None,则从环境变量读取,默认为 30
            max_retries: 最大重试次数。如果为 None,则从环境变量读取,默认为 3
            **kwargs: 其他配置参数
        """
        # 准备环境变量值
        env_values = {
            "api_key": os.getenv("DIFY_API_KEY", ""),
            "base_url": os.getenv("DIFY_BASE_URL", "https://api.dify.ai"),
            "timeout": int(os.getenv("DIFY_TIMEOUT", "30")),
            "max_retries": int(os.getenv("DIFY_MAX_RETRIES", "3")),
        }

        # 构造参数优先级高于环境变量
        final_values = {
            "api_key": api_key if api_key is not None else env_values["api_key"],
            "base_url": base_url if base_url is not None else env_values["base_url"],
            "timeout": timeout if timeout is not None else env_values["timeout"],
            "max_retries": (
                max_retries if max_retries is not None else env_values["max_retries"]
            ),
        }

        # 验证必需的配置
        if not final_values["api_key"]:
            raise ValueError(
                "API Key 未提供。请通过构造参数传入 api_key, "
                "或设置环境变量 DIFY_API_KEY"
            )

        # 验证配置值
        if final_values["timeout"] <= 0:
            raise ValueError(f"timeout 必须大于 0,当前值: {final_values['timeout']}")

        if final_values["max_retries"] < 0:
            raise ValueError(
                f"max_retries 不能为负数,当前值: {final_values['max_retries']}"
            )

        # 规范化 base_url
        base_url_value = final_values["base_url"]

        # 移除末尾斜杠
        if base_url_value.endswith("/"):
            base_url_value = base_url_value.rstrip("/")

        # 如果 base_url 以 /v1 结尾,移除它(因为端点路径中已经包含 /v1)
        if base_url_value.endswith("/v1"):
            base_url_value = base_url_value[:-3]

        final_values["base_url"] = base_url_value

        # 调用父类初始化
        super().__init__(**final_values, **kwargs)

    @classmethod
    def from_workflows_config(
        cls,
        workflow_name: str,
        config_path: Optional[str] = None,
        environment: str = "default",
    ) -> "Config":
        """
        从配置文件创建工作流配置

        Args:
            workflow_name: 工作流名称 (如 'safety_analysis')
            config_path: 配置文件路径,不指定则自动查找
            environment: 环境名称 (默认: 'default')

        Returns:
            Config: 配置对象

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置验证失败

        Example:
            >>> config = Config.from_workflows_config(
            ...     workflow_name='safety_analysis',
            ...     environment='production'
            ... )
        """
        # 查找配置文件 (如果未指定)
        if config_path is None:
            config_path = find_config_file()

        if config_path is None:
            raise FileNotFoundError(
                "未找到配置文件。请确保以下位置之一存在 dify.yaml:\n"
                "  - ./dify.yaml\n"
                "  - ./config/dify.yaml\n"
                "  - ~/.dify/dify.yaml"
            )

        # 加载配置
        config_data = load_config_file(config_path=config_path)

        # 验证配置
        validate_config(config_data)

        # 创建 Config 对象
        return cls(**config_data)

    @classmethod
    def from_chats_config(
        cls,
        chat_name: str,
        config_path: Optional[str] = None,
        environment: str = "default",
    ) -> "Config":
        """
        从配置文件创建聊天应用配置

        Args:
            chat_name: 聊天应用名称 (如 'sql_result_formatter')
            config_path: 配置文件路径,不指定则自动查找
            environment: 环境名称 (默认: 'default')

        Returns:
            Config: 配置对象

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置验证失败

        Example:
            >>> config = Config.from_chats_config(
            ...     chat_name='sql_result_formatter',
            ...     environment='production'
            ... )
        """
        # 查找配置文件 (如果未指定)
        if config_path is None:
            config_path = find_config_file()

        if config_path is None:
            raise FileNotFoundError(
                "未找到配置文件。请确保以下位置之一存在 dify.yaml:\n"
                "  - ./dify.yaml\n"
                "  - ./config/dify.yaml\n"
                "  - ~/.dify/dify.yaml"
            )

        # 加载配置
        config_data = load_chat_config(
            config_path=config_path, chat_name=chat_name, environment=environment
        )

        # 验证配置
        validate_config(config_data)

        # 创建 Config 对象
        return cls(**config_data)

    def get_headers(self) -> dict:
        """
        获取 HTTP 请求头

        Returns:
            dict: 包含 Authorization 和 Content-Type 的请求头字典
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
