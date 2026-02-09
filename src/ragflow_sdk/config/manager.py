"""
配置管理模块

设计原则：
- 支持多种配置源（YAML 文件、环境变量、代码参数）
- 配置优先级：代码参数 > 环境变量 > 配置文件 > 默认值
- 提供配置验证
- 友好的错误提示
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import yaml

from ..utils.helpers import deep_update

# 延迟导入：避免循环导入问题
# ConfigurationError 在运行时通过函数内导入获取
if TYPE_CHECKING:
    from ..core.exceptions import ConfigurationError


class ConfigManager:
    """
    配置管理器

    支持从多个来源加载和合并配置：
    1. YAML 配置文件
    2. 环境变量
    3. 运行时参数

    优先级：运行时参数 > 环境变量 > 配置文件 > 默认值
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "api": {
            "base_url": "",
            "api_key": "",
            "timeout": 30,
            "max_retries": 3,
            "verify_ssl": True,
        },
        "request": {
            "default_page_size": 10,
            "max_page_size": 1000,
        },
        "logging": {
            "enabled": False,
            "level": "INFO",
        },
    }

    # 支持的环境变量映射
    ENV_VAR_MAPPING = {
        "RAGFLOW_BASE_URL": "api.base_url",
        "RAGFLOW_API_KEY": "api.api_key",
        "RAGFLOW_TIMEOUT": "api.timeout",
        "RAGFLOW_MAX_RETRIES": "api.max_retries",
        "RAGFLOW_VERIFY_SSL": "api.verify_ssl",
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置

        Returns:
            配置字典
        """
        # 从默认配置开始
        config = self.DEFAULT_CONFIG.copy()

        # 如果指定了配置文件，加载并合并
        if self.config_path:
            file_config = self._load_from_file(self.config_path)
            config = deep_update(config, file_config)

        # 从环境变量合并
        env_config = self._load_from_env()
        config = deep_update(config, env_config)

        return config

    def _load_from_file(self, config_path: str) -> Dict[str, Any]:
        """
        从 YAML 文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典

        Raises:
            ConfigurationError: 配置文件加载失败时抛出
        """
        from ..core.exceptions import ConfigurationError  # 延迟导入

        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(
                message=f"配置文件不存在: {config_path}",
                details={"config_path": config_path},
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

            if not isinstance(file_config, dict):
                raise ConfigurationError(
                    message="配置文件格式错误：根节点必须是字典",
                    details={
                        "config_path": config_path,
                        "actual_type": type(file_config).__name__,
                    },
                )

            return file_config

        except yaml.YAMLError as e:
            raise ConfigurationError(
                message=f"配置文件 YAML 格式错误: {str(e)}",
                details={"config_path": config_path},
                original_error=e,
            )
        except Exception as e:
            raise ConfigurationError(
                message=f"加载配置文件失败: {str(e)}",
                details={"config_path": config_path},
                original_error=e,
            )

    def _load_from_env(self) -> Dict[str, Any]:
        """
        从环境变量加载配置

        Returns:
            配置字典
        """
        config = {}

        for env_var, config_path in self.ENV_VAR_MAPPING.items():
            value = os.environ.get(env_var)
            if value is not None:
                # 根据目标路径设置值
                self._set_nested_value(
                    config, config_path, self._parse_env_value(value)
                )

        return config

    def _parse_env_value(self, value: str) -> Any:
        """
        解析环境变量值

        Args:
            value: 环境变量值

        Returns:
            解析后的值
        """
        # 尝试解析为布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 尝试解析为整数
        try:
            return int(value)
        except ValueError:
            pass

        # 尝试解析为浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 返回字符串
        return value

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """
        设置嵌套配置值

        Args:
            config: 配置字典
            path: 配置路径（例如：api.base_url）
            value: 配置值
        """
        keys = path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持嵌套路径）

        Args:
            key: 配置键，支持点号分隔的嵌套路径（例如：api.base_url）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值（支持嵌套路径）

        Args:
            key: 配置键
            value: 配置值
        """
        self._set_nested_value(self.config, key, value)

    def update(self, **kwargs):
        """
        批量更新配置

        Args:
            **kwargs: 配置项键值对
        """
        for key, value in kwargs.items():
            self.set(key, value)

    # 便捷方法：获取常用配置
    def get_base_url(self) -> str:
        """获取 API 基础 URL"""
        return self.get("api.base_url", "")

    def get_api_key(self) -> str:
        """获取 API 密钥"""
        return self.get("api.api_key", "")

    def get_timeout(self) -> int:
        """获取请求超时时间"""
        return self.get("api.timeout", 30)

    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return self.get("api.max_retries", 3)

    def get_verify_ssl(self) -> bool:
        """获取是否验证 SSL 证书"""
        return self.get("api.verify_ssl", True)

    def validate(self) -> bool:
        """
        验证配置是否完整

        Returns:
            是否验证通过

        Raises:
            ConfigurationError: 配置验证失败时抛出
        """
        from ..core.exceptions import ConfigurationError  # 延迟导入

        # 检查必需的配置项
        base_url = self.get_base_url()
        if not base_url:
            raise ConfigurationError(
                message="缺少必需的配置项: api.base_url",
                details={
                    "suggestion": "请在配置文件中设置 api.base_url，或通过环境变量 RAGFLOW_BASE_URL 指定"
                },
            )

        api_key = self.get_api_key()
        if not api_key:
            raise ConfigurationError(
                message="缺少必需的配置项: api.api_key",
                details={
                    "suggestion": "请在配置文件中设置 api.api_key，或通过环境变量 RAGFLOW_API_KEY 指定"
                },
            )

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典

        Returns:
            配置字典的副本
        """
        return self.config.copy()

    def save(self, path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            path: 保存路径，如果为 None，则使用原配置文件路径
        """
        from ..core.exceptions import ConfigurationError  # 延迟导入

        save_path = path or self.config_path

        if not save_path:
            raise ConfigurationError(
                message="未指定保存路径",
                details={"suggestion": "请提供保存路径，或在初始化时指定配置文件路径"},
            )

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.config,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
        except Exception as e:
            raise ConfigurationError(
                message=f"保存配置文件失败: {str(e)}",
                details={"save_path": save_path},
                original_error=e,
            )
