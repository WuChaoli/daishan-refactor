"""
ConfigManager - 配置管理器
负责加载、验证和管理应用配置
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class Config:
    """应用配置数据类"""

    # RAGFlow 配置
    ragflow_api_key: str
    ragflow_base_url: str

    # 知识库映射: 知识库名 → 意图类型
    database_mapping: Dict[str, int]

    # 意图判断参数
    similarity_threshold: float = 0.4
    top_k_per_database: int = 3
    default_type: int = 0

    # 服务器配置
    server_host: str = "0.0.0.0"
    server_port: int = 11029

    # 日志配置
    log_dir: str = "logs"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    log_total_size_limit: int = 524288000  # 500MB

    # 流式聊天配置
    stream_chat_api_key: str = ""
    stream_chat_base_url: str = ""
    stream_chat_endpoint: str = "/chat-messages"
    stream_chat_timeout: float = 30.0
    stream_chat_max_retry: int = 2
    stream_chat_retry_delay: float = 1.0

    def get_databases(self) -> List[str]:
        """获取所有知识库名称"""
        return list(self.database_mapping.keys())

    def get_type_mapping(self, db_name: str) -> int:
        """
        获取知识库对应的意图类型

        Args:
            db_name: 知识库名称

        Returns:
            意图类型

        Raises:
            KeyError: 知识库不存在
        """
        if db_name not in self.database_mapping:
            raise KeyError(f"知识库 '{db_name}' 不在配置的 database_mapping 中")
        return self.database_mapping[db_name]


def expand_env_vars(value: Any) -> Any:
    """
    展开环境变量引用

    支持的格式:
    - ${VAR_NAME}              - 必需引用
    - ${VAR_NAME:-default}      - 可选引用,带默认值

    Args:
        value: 任意值 (字符串、数字、字典、列表等)

    Returns:
        展开环境变量后的值
    """
    if isinstance(value, str):
        # 匹配 ${VAR_NAME} 或 ${VAR_NAME:-default}
        pattern = r"\$\{([^}:]+)(:-([^}]*))?\}"

        def replace(match):
            var_name = match.group(1)
            default_value = match.group(3) if match.group(2) else ""
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replace, value)

    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]

    return value


def expand_env_vars_recursive(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归展开字典中所有环境变量引用

    Args:
        data: 配置字典

    Returns:
        展开环境变量后的配置字典
    """
    return expand_env_vars(data)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        """
        加载并验证配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        config_data = expand_env_vars_recursive(config_data)

        if not config_data:
            raise ValueError("配置文件为空")

        # 验证并创建 Config 对象
        # 提取配置部分
        ragflow_config = config_data.get("ragflow", {})
        intent_config = config_data.get("intent", {})
        server_config = config_data.get("server", {})
        logging_config = config_data.get("logging", {})
        stream_chat_config = config_data.get("stream_chat", {})

        # 转换 database_mapping 值为整数
        database_mapping = ragflow_config.get("database_mapping", {})
        converted_database_mapping = {}
        for db_name, type_value in database_mapping.items():
            if isinstance(type_value, str):
                try:
                    converted_database_mapping[db_name] = int(type_value)
                except ValueError:
                    raise ValueError(
                        f"database_mapping 中知识库 '{db_name}' 的类型值必须为整数, 当前值: {type_value}"
                    )
            else:
                converted_database_mapping[db_name] = int(type_value)

        self._config = Config(
            ragflow_api_key=ragflow_config.get("api_key", ""),
            ragflow_base_url=ragflow_config.get("base_url", ""),
            database_mapping=converted_database_mapping,
            similarity_threshold=float(intent_config.get("similarity_threshold", 0.4)),
            top_k_per_database=int(intent_config.get("top_k_per_database", 3)),
            default_type=int(intent_config.get("default_type", 0)),
            server_host=server_config.get("host", "0.0.0.0"),
            server_port=int(server_config.get("port", 11029)),
            log_dir=logging_config.get("log_dir", "logs"),
            log_max_bytes=int(logging_config.get("max_bytes", 10485760)),
            log_backup_count=int(logging_config.get("backup_count", 5)),
            log_total_size_limit=int(logging_config.get("total_size_limit", 524288000)),
            stream_chat_api_key=stream_chat_config.get("api_key", ""),
            stream_chat_base_url=stream_chat_config.get("base_url", ""),
            stream_chat_endpoint=stream_chat_config.get("endpoint", "/chat-messages"),
            stream_chat_timeout=float(stream_chat_config.get("timeout", 30.0)),
            stream_chat_max_retry=int(stream_chat_config.get("max_retry_attempts", 2)),
            stream_chat_retry_delay=float(stream_chat_config.get("retry_delay", 1.0)),
        )

        # 验证配置完整性
        self._validate_config()

    def _validate_config(self):
        """验证配置完整性"""
        if self._config is None:
            raise ValueError("Config not initialized")

        errors = []

        # 验证 RAGFlow API Key
        if not self._config.ragflow_api_key:
            errors.append("RAGFlow API Key 不能为空")

        # 验证 BASE_URL 格式
        if not self._config.ragflow_base_url.startswith(("http://", "https://")):
            errors.append("RAGFlow BASE_URL 格式错误，必须以 http:// 或 https:// 开头")

        # 验证 database_mapping 不为空
        if not self._config.database_mapping:
            errors.append("database_mapping 不能为空")

        # 验证 similarity_threshold 在有效范围
        if not (0 <= self._config.similarity_threshold <= 1):
            errors.append("similarity_threshold 必须在 [0, 1] 范围内")

        # 验证端口号
        if not (1024 <= self._config.server_port <= 65535):
            errors.append("server_port 必须在 [1024, 65535] 范围内")

        # 验证日志目录可写
        log_dir = Path(self._config.log_dir)
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建日志目录 {self._config.log_dir}: {str(e)}")
        elif not log_dir.is_dir():
            errors.append(f"log_dir 不是一个目录: {self._config.log_dir}")

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"配置验证失败:\n{error_msg}")

    def get_config(self) -> Optional[Config]:
        """获取配置对象"""
        return self._config

    def get_databases(self) -> List[str]:
        """获取所有知识库名称"""
        if self._config is None:
            return []
        return list(self._config.database_mapping.keys())

    def get_type_mapping(self, db_name: str) -> int:
        """
        获取知识库对应的意图类型

        Args:
            db_name: 知识库名称

        Returns:
            意图类型

        Raises:
            KeyError: 知识库不存在
        """
        if self._config is None:
            raise KeyError("Config not initialized")
        if db_name not in self._config.database_mapping:
            raise KeyError(f"知识库 '{db_name}' 不在配置的 database_mapping 中")
        return self._config.database_mapping[db_name]

    def validate_config(self) -> bool:
        """验证配置完整性（已集成到构造函数中）"""
        return self._config is not None
