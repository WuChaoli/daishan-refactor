"""
岱山意图识别服务配置模块

设计原则：
1. 采用多个独立配置类，每个配置类负责一个功能模块的配置
2. 动态配置（如 chat_ids、database_mapping、chats）以 Dict 形式存储，支持后续扩展
3. 与 dify_sdk、ragflow_sdk 的配置加载方式兼容
4. 支持从 YAML 配置文件、环境变量加载配置
5. 配置优先级：环境变量 > 配置文件 > 默认值
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# ============================================================
# 基础配置模型
# ============================================================


class BaseConfig(BaseModel):
    """基础配置类，提供通用配置方法"""

    @classmethod
    def from_yaml(cls, yaml_path: Path, prefix: str = "") -> "BaseConfig":
        """
        从 YAML 文件加载配置

        Args:
            yaml_path: YAML 配置文件路径
            prefix: 配置键前缀（用于从嵌套配置中提取子节点）

        Returns:
            配置实例
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        if prefix:
            # 获取指定前缀的配置
            keys = prefix.split(".")
            for key in keys:
                config_data = config_data.get(key, {})

        return cls(**config_data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()


# ============================================================
# RAGFlow 配置
# ============================================================


class RAGFlowConfig(BaseConfig):
    """
    RAGFlow 配置

    用于意图识别的 RAGFlow API 配置
    """

    api_key: str = Field(default="", description="RAGFlow API Key")
    base_url: str = Field(default="", description="RAGFlow API Base URL")
    timeout: int = Field(default=30, description="HTTP 请求超时时间(秒)")
    max_retries: int = Field(default=3, description="网络错误最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试间隔基数(秒)，使用指数退避")
    retry_backoff_factor: float = Field(default=2.0, description="退避因子")
    retry_max_delay: float = Field(default=30.0, description="最大重试间隔(秒)")
    list_datasets_page_size: int = Field(default=100, description="获取数据集列表的 page_size")
    list_datasets_timeout: int = Field(default=10, description="获取数据集列表的超时(秒)")
    query_timeout: int = Field(default=60, description="检索查询超时时间(秒)")
    retrieval_top_k: int = Field(default=100, description="检索时的 top_k，减少以提升速度")
    vector_similarity_weight: float = Field(
        default=0.3, description="向量相似度权重（基础配置）"
    )

    # 动态配置：Chat IDs（意图名称 -> Chat ID 映射）
    chat_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="RAGFlow Chat IDs 映射表（意图名称 -> Chat ID）",
    )

    # 动态配置：知识库映射（知识库名 -> 意图类型映射）
    # 兼容 int 或 str（例如 "2"）
    database_mapping: Dict[str, Union[int, str]] = Field(
        default_factory=dict,
        description="知识库到意图类型映射表（知识库名 -> 意图类型，支持 int/str）",
    )

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"max_retries 不能为负数，当前值: {v}")
        return v

    @field_validator("retry_delay", "retry_backoff_factor", "retry_max_delay")
    @classmethod
    def validate_positive_float(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"该值必须大于 0，当前值: {v}")
        return v

    @field_validator("list_datasets_page_size")
    @classmethod
    def validate_list_datasets_page_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"list_datasets_page_size 必须大于 0，当前值: {v}")
        return v

    @field_validator("list_datasets_timeout")
    @classmethod
    def validate_list_datasets_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"list_datasets_timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("query_timeout")
    @classmethod
    def validate_query_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"query_timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("retrieval_top_k")
    @classmethod
    def validate_retrieval_top_k(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"retrieval_top_k 必须大于 0，当前值: {v}")
        return v

    @field_validator("vector_similarity_weight")
    @classmethod
    def validate_vector_similarity_weight(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError(
                f"vector_similarity_weight 必须在 0-1 之间，当前值: {v}"
            )
        return v

    def get_chat_id(self, intent_name: str) -> str:
        """
        获取指定意图的 Chat ID

        Args:
            intent_name: 意图名称

        Returns:
            Chat ID，如果不存在返回空字符串
        """
        return self.chat_ids.get(intent_name, "")

    def get_intent_type(self, database_name: str) -> int:
        """
        获取指定知识库的意图类型

        Args:
            database_name: 知识库名称

        Returns:
            意图类型，如果不存在返回 -1
        """
        value = self.database_mapping.get(database_name, -1)

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            text = value.strip()
            if text == "":
                return -1
            try:
                return int(text)
            except ValueError:
                return -1

        return -1


# ============================================================
# 意图判断配置
# ============================================================


class IntentConfig(BaseConfig):
    """
    意图判断参数配置

    用于意图识别和分类的业务配置
    """

    similarity_threshold: float = Field(
        default=0.4, description="相似度阈值，用于意图判断"
    )
    top_k_per_database: int = Field(
        default=10, description="每个知识库返回的 Top K 候选"
    )
    vector_similarity_weight: Optional[float] = Field(
        default=None, description="向量相似度权重（可选，未设置则继承 ragflow）"
    )
    default_type: int = Field(default=0, description="默认意图类型")
    fixed_question_similarity_threshold: float = Field(
        default=0.6, description="固定问题最小相似度阈值"
    )
    fixed_question_direct_threshold: float = Field(
        default=0.7, description="固定问题直接命中阈值"
    )
    fixed_question_top_k: int = Field(
        default=5, description="固定问题候选最大数量"
    )
    fixed_question_table_name: str = Field(
        default="岱山-指令集-固定问题-0311", description="固定问题知识库名称"
    )

    @field_validator("similarity_threshold")
    @classmethod
    def validate_similarity_threshold(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError(f"similarity_threshold 必须在 0-1 之间，当前值: {v}")
        return v

    @field_validator(
        "fixed_question_similarity_threshold",
        "fixed_question_direct_threshold",
    )
    @classmethod
    def validate_fixed_question_threshold(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError(f"fixed question threshold 必须在 0-1 之间，当前值: {v}")
        return v

    @field_validator("top_k_per_database")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"top_k_per_database 必须大于 0，当前值: {v}")
        return v

    @field_validator("fixed_question_top_k")
    @classmethod
    def validate_fixed_question_top_k(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"fixed_question_top_k 必须大于 0，当前值: {v}")
        return v

    @field_validator("fixed_question_table_name")
    @classmethod
    def validate_fixed_question_table_name(cls, v: str) -> str:
        text = str(v or "").strip()
        if not text:
            raise ValueError("fixed_question_table_name 不能为空")
        return text

    @field_validator("vector_similarity_weight")
    @classmethod
    def validate_intent_vector_similarity_weight(
        cls, v: Optional[float]
    ) -> Optional[float]:
        if v is None:
            return v
        if not 0 <= v <= 1:
            raise ValueError(
                f"intent.vector_similarity_weight 必须在 0-1 之间，当前值: {v}"
            )
        return v


# ============================================================
# 服务器配置
# ============================================================


class ServerConfig(BaseConfig):
    """
    服务器配置

    服务启动和网络监听配置
    """

    host: str = Field(default="0.0.0.0", description="监听主机地址")
    port: int = Field(default=11027, description="监听端口")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1024 <= v <= 65535:
            raise ValueError(f"port 必须在 1024-65535 之间，当前值: {v}")
        return v


# ============================================================
# 日志配置
# ============================================================


class LoggingConfig(BaseConfig):
    """
    日志配置

    日志输出、轮转和存储配置
    """

    log_dir: str = Field(default="logs", description="日志目录")
    max_bytes: int = Field(default=10485760, description="单个日志文件最大字节数（10MB）")
    backup_count: int = Field(default=5, description="备份文件数量")
    total_size_limit: int = Field(
        default=524288000, description="日志总大小限制（500MB）"
    )

    @field_validator("max_bytes", "total_size_limit")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"日志大小限制必须大于 0，当前值: {v}")
        return v

    @field_validator("backup_count")
    @classmethod
    def validate_backup_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"backup_count 不能为负数，当前值: {v}")
        return v


# ============================================================
# Dify Chat 应用配置模型
# ============================================================


class DifyChatConfig(BaseConfig):
    """
    Dify Chat 应用配置

    单个 Chat 应用的配置
    """

    api_key: str = Field(default="", description="Chat 应用 API Key")
    description: str = Field(default="", description="Chat 应用描述")


# ============================================================
# Dify 配置
# ============================================================


class DifyConfig(BaseConfig):
    """
    Dify 配置

    用于集成 Dify 平台服务的配置
    """

    base_url: str = Field(default="http://172.16.11.60/v1", description="Dify API Base URL")
    timeout: int = Field(default=30, description="HTTP 请求超时时间(秒)")
    max_retries: int = Field(default=3, description="网络错误最大重试次数")

    # 动态配置：Chat 应用列表（应用名称 -> 应用配置）
    chats: Dict[str, DifyChatConfig] = Field(
        default_factory=dict,
        description="Dify Chat 应用配置表（应用名称 -> 应用配置）",
    )

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"max_retries 不能为负数，当前值: {v}")
        return v

    def get_chat_config(self, chat_name: str) -> DifyChatConfig:
        """
        获取指定 Chat 应用的配置

        Args:
            chat_name: Chat 应用名称

        Returns:
            Chat 应用配置，如果不存在返回空配置
        """
        return self.chats.get(chat_name, DifyChatConfig())

    def get_chat_api_key(self, chat_name: str) -> str:
        """
        获取指定 Chat 应用的 API Key

        Args:
            chat_name: Chat 应用名称

        Returns:
            API Key，如果不存在返回空字符串
        """
        return self.chats.get(chat_name, DifyChatConfig()).api_key


# ============================================================
# Query Chat 配置
# ============================================================


class QueryChatConfig(BaseConfig):
    """
    Query Chat 配置

    用于 q1 占位改写的聊天模型配置
    """

    enabled: bool = Field(default=True, description="是否启用 q1 占位改写功能")
    api_key: str = Field(default="", description="聊天服务 API Key")
    base_url: str = Field(default="", description="聊天服务 Base URL")
    model: str = Field(default="", description="聊天模型名称")
    timeout: int = Field(default=20, description="HTTP 请求超时时间(秒)")
    temperature: float = Field(default=0.0, description="采样温度")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 2:
            raise ValueError(f"temperature 必须在 0-2 之间，当前值: {v}")
        return v


# ============================================================
# Intent Classification 配置
# ============================================================


class IntentClassificationConfig(BaseConfig):
    """
    Intent Classification 配置

    用于粗粒度意图分类的聊天模型配置
    """

    enabled: bool = Field(default=False, description="是否启用意图分类功能")
    api_key: str = Field(default="", description="聊天服务 API Key")
    base_url: str = Field(default="", description="聊天服务 Base URL")
    model: str = Field(default="", description="聊天模型名称")
    timeout: int = Field(default=3, description="HTTP 请求超时时间(秒)")
    temperature: float = Field(default=0.0, description="采样温度")
    confidence_threshold: float = Field(default=0.5, description="置信度阈值")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"timeout 必须大于 0，当前值: {v}")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 2:
            raise ValueError(f"temperature 必须在 0-2 之间，当前值: {v}")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence_threshold(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError(f"confidence_threshold 必须在 0-1 之间，当前值: {v}")
        return v


# ============================================================
# OpenAI 配置
# ============================================================


class OpenAIConfig(BaseConfig):
    """
    OpenAI 配置

    用于 DaiShanSQL 的 OpenAI 兼容接口配置
    """

    api_key: str = Field(default="", description="OpenAI API Key")
    base_url: str = Field(default="", description="OpenAI API Base URL")
    base_url_embedding: str = Field(default="", description="OpenAI Embedding URL")
    model: str = Field(default="", description="模型名称")


# ============================================================
# MySQL 配置
# ============================================================


class MySQLConfig(BaseConfig):
    """
    MySQL 数据库配置

    用于 DaiShanSQL 的数据库连接配置
    """

    host: str = Field(default="localhost", description="数据库主机地址")
    name: str = Field(default="", description="数据库名称")
    user: str = Field(default="", description="数据库用户名")
    password: str = Field(default="", description="数据库密码")
    port: int = Field(default=3306, description="数据库端口")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError(f"port 必须在 1-65535 之间，当前值: {v}")
        return v


# ============================================================
# 主配置类（聚合所有配置）
# ============================================================


class Settings(BaseModel):
    """
    主配置类

    聚合所有模块的配置，提供统一的配置访问接口
    """

    ragflow: RAGFlowConfig = Field(default_factory=RAGFlowConfig)
    intent: IntentConfig = Field(default_factory=IntentConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    dify: DifyConfig = Field(default_factory=DifyConfig)
    query_chat: QueryChatConfig = Field(default_factory=QueryChatConfig)
    intent_classification: IntentClassificationConfig = Field(default_factory=IntentClassificationConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    mysql: MySQLConfig = Field(default_factory=MySQLConfig)

    # ============================================================
    # 从 YAML 文件加载配置
    # ============================================================

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "Settings":
        """
        从 YAML 配置文件加载所有配置

        Args:
            yaml_path: YAML 配置文件路径

        Returns:
            Settings 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        if not isinstance(config_data, dict):
            raise ValueError("YAML 配置文件根节点必须是字典")

        # 逐个构建各模块配置
        ragflow_cfg = RAGFlowConfig.from_yaml(yaml_path, "ragflow")
        intent_cfg = IntentConfig.from_yaml(yaml_path, "intent")
        server_cfg = ServerConfig.from_yaml(yaml_path, "server")
        logging_cfg = LoggingConfig.from_yaml(yaml_path, "logging")
        dify_cfg = DifyConfig.from_yaml(yaml_path, "dify")
        query_chat_cfg = QueryChatConfig.from_yaml(yaml_path, "query_chat")
        intent_classification_cfg = IntentClassificationConfig.from_yaml(yaml_path, "intent_classification")
        openai_cfg = OpenAIConfig.from_yaml(yaml_path, "openai")
        mysql_cfg = MySQLConfig.from_yaml(yaml_path, "mysql")

        return cls(
            ragflow=ragflow_cfg,
            intent=intent_cfg,
            server=server_cfg,
            logging=logging_cfg,
            dify=dify_cfg,
            query_chat=query_chat_cfg,
            intent_classification=intent_classification_cfg,
            openai=openai_cfg,
            mysql=mysql_cfg,
        )

    @classmethod
    def load_from_yaml_with_env_override(cls, yaml_path: Path) -> "Settings":
        """
        从 YAML 配置文件加载配置，并支持环境变量覆盖

        环境变量命名规则：
        - RAGFLOW_API_KEY -> settings.ragflow.api_key
        - INTENT_SIMILARITY_THRESHOLD -> settings.intent.similarity_threshold
        - SERVER_HOST -> settings.server.host
        - DIFY_BASE_URL -> settings.dify.base_url
        - MYSQL_HOST -> settings.mysql.host

        Args:
            yaml_path: YAML 配置文件路径

        Returns:
            Settings 实例
        """
        settings = cls.load_from_yaml(yaml_path)

        # 应用环境变量覆盖
        env_overrides = {
            # RAGFlow 配置
            "RAGFLOW_API_KEY": ("ragflow", "api_key"),
            "RAGFLOW_BASE_URL": ("ragflow", "base_url"),
            "RAGFLOW_TIMEOUT": ("ragflow", "timeout"),
            "RAGFLOW_MAX_RETRIES": ("ragflow", "max_retries"),
            "RAGFLOW_RETRY_DELAY": ("ragflow", "retry_delay"),
            "RAGFLOW_RETRY_BACKOFF_FACTOR": ("ragflow", "retry_backoff_factor"),
            "RAGFLOW_RETRY_MAX_DELAY": ("ragflow", "retry_max_delay"),
            "RAGFLOW_LIST_DATASETS_PAGE_SIZE": ("ragflow", "list_datasets_page_size"),
            "RAGFLOW_LIST_DATASETS_TIMEOUT": ("ragflow", "list_datasets_timeout"),
            "RAGFLOW_QUERY_TIMEOUT": ("ragflow", "query_timeout"),
            "RAGFLOW_RETRIEVAL_TOP_K": ("ragflow", "retrieval_top_k"),
            # 意图配置
            "INTENT_SIMILARITY_THRESHOLD": ("intent", "similarity_threshold"),
            "INTENT_TOP_K_PER_DATABASE": ("intent", "top_k_per_database"),
            "INTENT_DEFAULT_TYPE": ("intent", "default_type"),
            "INTENT_FIXED_QUESTION_SIMILARITY_THRESHOLD": (
                "intent",
                "fixed_question_similarity_threshold",
            ),
            "INTENT_FIXED_QUESTION_DIRECT_THRESHOLD": (
                "intent",
                "fixed_question_direct_threshold",
            ),
            "INTENT_FIXED_QUESTION_TOP_K": ("intent", "fixed_question_top_k"),
            "INTENT_FIXED_QUESTION_TABLE_NAME": (
                "intent",
                "fixed_question_table_name",
            ),
            # 服务器配置
            "SERVER_HOST": ("server", "host"),
            "SERVER_PORT": ("server", "port"),
            # 日志配置
            "LOG_DIR": ("logging", "log_dir"),
            "LOG_MAX_BYTES": ("logging", "max_bytes"),
            "LOG_BACKUP_COUNT": ("logging", "backup_count"),
            "LOG_TOTAL_SIZE_LIMIT": ("logging", "total_size_limit"),
            # Dify 配置
            "DIFY_BASE_URL": ("dify", "base_url"),
            "DIFY_TIMEOUT": ("dify", "timeout"),
            "DIFY_MAX_RETRIES": ("dify", "max_retries"),
            # Query Chat 配置
            "QUERY_CHAT_API_KEY": ("query_chat", "api_key"),
            "QUERY_CHAT_BASE_URL": ("query_chat", "base_url"),
            "QUERY_CHAT_MODEL": ("query_chat", "model"),
            "QUERY_CHAT_ENABLED": ("query_chat", "enabled"),
            "QUERY_CHAT_TIMEOUT": ("query_chat", "timeout"),
            "QUERY_CHAT_TEMPERATURE": ("query_chat", "temperature"),
            # Intent Classification 配置
            "INTENT_CLASSIFICATION_ENABLED": ("intent_classification", "enabled"),
            "INTENT_CLASSIFICATION_API_KEY": ("intent_classification", "api_key"),
            "INTENT_CLASSIFICATION_BASE_URL": ("intent_classification", "base_url"),
            "INTENT_CLASSIFICATION_MODEL": ("intent_classification", "model"),
            "INTENT_CLASSIFICATION_TIMEOUT": ("intent_classification", "timeout"),
            "INTENT_CLASSIFICATION_TEMPERATURE": ("intent_classification", "temperature"),
            "INTENT_CLASSIFICATION_CONFIDENCE_THRESHOLD": ("intent_classification", "confidence_threshold"),
            # OpenAI 配置
            "OPENAI_API_KEY": ("openai", "api_key"),
            "OPENAI_BASE_URL": ("openai", "base_url"),
            "OPENAI_BASE_URL_EMBEDDING": ("openai", "base_url_embedding"),
            "OPENAI_MODEL": ("openai", "model"),
            # MySQL 配置
            "MYSQL_HOST": ("mysql", "host"),
            "MYSQL_NAME": ("mysql", "name"),
            "MYSQL_USER": ("mysql", "user"),
            "MYSQL_PASSWORD": ("mysql", "password"),
            "MYSQL_PORT": ("mysql", "port"),
        }

        for env_var, (section, key) in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # 获取当前值
                section_config = getattr(settings, section)
                current_value = getattr(section_config, key)

                # 尝试类型转换
                if type(current_value) is int:
                    value = int(value)
                elif type(current_value) is float:
                    value = float(value)
                elif isinstance(current_value, bool):
                    value = value.lower() in ("true", "yes", "1")

                # 设置新值
                setattr(section_config, key, value)
                setattr(settings, section, section_config)

        return settings

    def validate_query_chat_config(self) -> None:
        """验证 query_chat 配置，无效时记录告警并降级运行。"""
        logger = logging.getLogger(__name__)
        config = self.query_chat

        if not config.enabled:
            logger.info("Query Chat 功能已禁用（enabled=false）")
            return

        missing: list[str] = []
        if not (config.api_key or "").strip():
            missing.append("api_key")
        if not (config.base_url or "").strip():
            missing.append("base_url")

        if missing:
            logger.warning(
                "QUERY_CHAT 配置不完整（缺少: %s），q1 占位改写功能将降级运行",
                ", ".join(missing),
            )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Query Chat 配置检查: enabled=%s, base_url=%s, model=%s, timeout=%s, temperature=%s, api_key=%s",
                config.enabled,
                config.base_url,
                config.model,
                config.timeout,
                config.temperature,
                "***" if config.api_key else "",
            )

    def validate_intent_classification_config(self) -> None:
        """验证 intent_classification 配置，无效时记录告警并降级运行。"""
        logger = logging.getLogger(__name__)
        config = self.intent_classification

        if not config.enabled:
            logger.info("Intent Classification 功能已禁用（enabled=false）")
            return

        missing: list[str] = []
        if not (config.api_key or "").strip():
            missing.append("api_key")
        if not (config.base_url or "").strip():
            missing.append("base_url")
        if not (config.model or "").strip():
            missing.append("model")

        if missing:
            logger.warning(
                "INTENT_CLASSIFICATION 配置不完整（缺少: %s），分类功能将降级运行",
                ", ".join(missing),
            )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Intent Classification 配置检查: enabled=%s, base_url=%s, model=%s, timeout=%s, temperature=%s, confidence_threshold=%s, api_key=%s",
                config.enabled,
                config.base_url,
                config.model,
                config.timeout,
                config.temperature,
                config.confidence_threshold,
                "***" if config.api_key else "",
            )


# ============================================================
# 全局配置实例
# ============================================================


def _repo_dir() -> Path:
    """获取项目根目录（rag_stream 目录）"""
    return Path(__file__).resolve().parents[2]


def _load_env_files() -> None:
    """
    加载环境变量文件

    加载 rag_stream/.env - 包含 DIFY 相关配置
    """
    base_dir = _repo_dir()

    # 加载 rag_stream 的 .env 文件
    rag_stream_env_path = base_dir / ".env"
    if rag_stream_env_path.exists():
        load_dotenv(rag_stream_env_path, override=False)


def load_settings() -> Settings:
    """
    加载全局配置

    从项目根目录的 config.yaml 文件加载配置，并从 .env 文件加载环境变量

    Returns:
        Settings 实例
    """
    # 首先加载环境变量文件
    _load_env_files()

    base_dir = _repo_dir()
    yaml_path = base_dir / "config.yaml"

    loaded_settings = Settings.load_from_yaml_with_env_override(yaml_path)
    loaded_settings.validate_query_chat_config()
    loaded_settings.validate_intent_classification_config()
    return loaded_settings


# 全局配置实例
settings = load_settings()
