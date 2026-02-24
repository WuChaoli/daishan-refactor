"""配置加载模块

提供日志装饰器的配置加载功能，支持：
- 从yaml文件加载配置
- 默认配置
- 配置验证和合并
"""
import os
import logging
from typing import Dict, Any, Optional
import yaml

# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "format": "%(asctime)s - %(levelname)-7s - %(message)s",  # -7s 表示固定7个字符宽度，左对齐
    "time_format": "%Y-%m-%d %H:%M:%S",
    "level": "INFO",
    "encoding": "utf-8",
    "log_dir": "logs",
    "entry_log_dir": "entries",
    "global_log_file": "global.log",
    "console_enabled": True,
    "mermaid_enabled": False,
    "mermaid_dir": "mermaid",
    "mermaid_max_size_mb": 10,
    "args_max_len": 100,
    "result_max_len": 100,
    "icon_theme": "default",
    "icon_themes": {
        "default": {
            "function": {
                "log": "🔵",
                "entry": "🟢",
                "end": "🟣",
            },
            "section": {
                "args": "🧩",
                "returns": "🧪",
            },
        },
        "minimal": {
            "function": {
                "log": "◽",
                "entry": "◻",
                "end": "◼",
            },
            "section": {
                "args": "▫",
                "returns": "▪",
            },
        },
    },
}

# 有效日志级别
VALID_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件

    查找顺序：
    1. 指定的config_path
    2. 项目根目录的log_config.yaml（用户自定义配置）
    3. log_decorator目录的log_config.yaml（默认配置）
    4. 代码中的DEFAULT_CONFIG

    Args:
        config_path: 配置文件路径，如果指定则直接使用

    Returns:
        配置字典
    """
    # 确定配置文件路径
    if config_path is None:
        package_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(package_dir)

        # 查找顺序：项目根目录 -> log_decorator目录
        config_paths = [
            os.path.join(project_root, "log_config.yaml"),  # 用户自定义
            os.path.join(package_dir, "log_config.yaml")    # 默认配置
        ]

        # 找到第一个存在的配置文件
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break

        # 如果都不存在，返回默认配置
        if config_path is None:
            return DEFAULT_CONFIG.copy()

    # 如果指定的配置文件不存在，返回默认配置
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()

    # 读取配置文件
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
    except Exception as e:
        logging.warning(f"配置文件加载失败: {e}，使用默认配置")
        return DEFAULT_CONFIG.copy()

    # 提取logging节点
    if not user_config or "logging" not in user_config:
        return DEFAULT_CONFIG.copy()

    logging_config = user_config["logging"]

    # 合并配置
    config = merge_config(DEFAULT_CONFIG, logging_config)

    # 验证配置
    config = validate_config(config)

    # 确保日志目录存在
    ensure_log_dir(config["log_dir"])

    return config


def merge_config(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """合并用户配置和默认配置

    Args:
        default: 默认配置
        user: 用户配置

    Returns:
        合并后的配置
    """
    config = default.copy()
    if user:
        config.update(user)
    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """验证配置项

    Args:
        config: 配置字典

    Returns:
        验证后的配置
    """
    validated = config.copy()

    # 验证日志级别
    if not isinstance(validated.get("level"), str):
        validated["level"] = DEFAULT_CONFIG["level"]
    elif validated["level"] not in VALID_LEVELS:
        validated["level"] = DEFAULT_CONFIG["level"]

    # 验证console_enabled
    if not isinstance(validated.get("console_enabled"), bool):
        validated["console_enabled"] = DEFAULT_CONFIG["console_enabled"]

    # 验证字符串类型
    for key in [
        "format",
        "time_format",
        "encoding",
        "log_dir",
        "entry_log_dir",
        "global_log_file",
        "icon_theme",
    ]:
        if not isinstance(validated.get(key), str):
            validated[key] = DEFAULT_CONFIG[key]

    # 验证图标主题配置
    icon_themes = validated.get("icon_themes")
    if not isinstance(icon_themes, dict) or not icon_themes:
        validated["icon_themes"] = DEFAULT_CONFIG["icon_themes"]
        icon_themes = validated["icon_themes"]

    if "default" not in icon_themes or not isinstance(icon_themes.get("default"), dict):
        icon_themes["default"] = DEFAULT_CONFIG["icon_themes"]["default"]

    selected_theme = validated.get("icon_theme")
    if selected_theme not in icon_themes:
        validated["icon_theme"] = "default"

    # 验证长度配置
    for key in ["args_max_len", "result_max_len"]:
        value = validated.get(key)
        if not isinstance(value, int) or value <= 0:
            validated[key] = DEFAULT_CONFIG[key]

    return validated


def ensure_log_dir(log_dir: str) -> None:
    """确保日志目录存在

    Args:
        log_dir: 日志目录路径
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)
    full_path = os.path.join(project_root, log_dir)

    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)


# 导出
__all__ = ["load_config", "DEFAULT_CONFIG", "VALID_LEVELS"]
