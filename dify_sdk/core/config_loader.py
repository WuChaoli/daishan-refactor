"""
Dify SDK 配置文件加载器

负责从 YAML 文件加载 Dify SDK 配置,支持多工作流、多环境、环境变量插值等功能。
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    加载并解析 YAML 配置文件，从 dify 节点读取配置

    Args:
        config_path: 配置文件路径 (config.yaml)

    Returns:
        dict: 解析后的 dify 配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: YAML 格式错误或配置验证失败
    """
    # 1. 检查文件存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    # 2. 读取并解析 YAML
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 格式错误: {str(e)}")

    # 3. 验证 dify 节点存在
    if "dify" not in config_data:
        raise ValueError("配置文件中缺少 'dify' 节点")

    dify_config = config_data["dify"]

    # 4. 展开环境变量 (递归处理)
    dify_config = expand_env_vars_recursive(dify_config)

    return dify_config


def find_config_file() -> Optional[str]:
    """
    自动查找配置文件

    查找位置: ./config.yaml

    Returns:
        str | None: 找到的配置文件路径,未找到返回 None
    """
    if os.path.exists("./config.yaml"):
        return "./config.yaml"

    return None


def _try_convert_type(value: str) -> Any:
    """
    尝试将字符串转换为适当的类型 (int, float, bool)

    Args:
        value: 字符串值

    Returns:
        转换后的值，如果无法转换则返回原字符串
    """
    # 尝试转换为整数
    try:
        return int(value)
    except ValueError:
        pass

    # 尝试转换为浮点数
    try:
        return float(value)
    except ValueError:
        pass

    # 尝试转换为布尔值
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    return value


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

        result = re.sub(pattern, replace, value)

        # 如果整个字符串都是环境变量替换的结果，尝试类型转换
        if result != value:
            return _try_convert_type(result)
        return result

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


def load_chat_config(
    config_path: Optional[str], chat_name: str, environment: str = "default"
) -> Dict[str, Any]:
    """
    从配置文件加载指定聊天应用的配置

    Args:
        config_path: 配置文件路径 (None 时自动查找 config.yaml)
        chat_name: 聊天应用名称 (如 'sql_result_formatter')
        environment: 环境名称 (已废弃,保留参数兼容性)

    Returns:
        dict: 聊天应用配置
            {
                'api_key': 'app-xxx',
                'base_url': 'http://...',
                'timeout': 30,
                'max_retries': 3
            }

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: chat_name 不存在或配置无效

    Example:
        >>> config = load_chat_config(None, 'sql_result_formatter')
        >>> print(config['api_key'])
        'app-xxx'
    """
    # 1. 自动查找配置文件 (如果未指定)
    if config_path is None:
        config_path = find_config_file()
        if config_path is None:
            raise FileNotFoundError(
                "未找到配置文件,请确保 config.yaml 存在于当前目录"
            )

    # 2. 加载 dify 配置
    dify_config = load_config_file(config_path=config_path)

    # 3. 验证 chats 节点存在
    if "chats" not in dify_config:
        raise ValueError(
            "配置文件中缺少 'dify.chats' 配置节点。"
            "请确保 config.yaml 包含 dify.chats 配置。"
        )

    chats_config = dify_config["chats"]

    # 4. 验证 chat_name 存在
    if chat_name not in chats_config:
        available = list(chats_config.keys())
        raise ValueError(
            f"聊天应用 '{chat_name}' 不存在。"
            f"可用的聊天应用: {', '.join(available)}"
        )

    # 5. 提取 chat 配置
    chat_config = chats_config[chat_name]

    # 6. 合并全局配置
    # 提取全局配置 (base_url, timeout, max_retries 等)
    global_config = {
        k: v
        for k, v in dify_config.items()
        if k != "chats" and k != "workflows" and not isinstance(v, dict)
    }

    # 7. 返回合并后的配置
    return {**global_config, **chat_config}


def load_workflow_config(
    config_path: Optional[str], workflow_name: str, environment: str = "default"
) -> Dict[str, Any]:
    """
    从配置文件加载指定工作流的配置

    Args:
        config_path: 配置文件路径 (None 时自动查找 config.yaml)
        workflow_name: 工作流名称 (如 'answer_summarize')
        environment: 环境名称 (已废弃,保留参数兼容性)

    Returns:
        dict: 工作流配置
            {
                'api_key': 'app-xxx',
                'base_url': 'http://...',
                'timeout': 30,
                'max_retries': 3
            }

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: workflow_name 不存在或配置无效

    Example:
        >>> config = load_workflow_config(None, 'answer_summarize')
        >>> print(config['api_key'])
        'app-xxx'
    """
    # 1. 自动查找配置文件 (如果未指定)
    if config_path is None:
        config_path = find_config_file()
        if config_path is None:
            raise FileNotFoundError(
                "未找到配置文件,请确保 config.yaml 存在于当前目录"
            )

    # 2. 加载 dify 配置
    dify_config = load_config_file(config_path=config_path)

    # 3. 验证 workflows 节点存在
    if "workflows" not in dify_config:
        raise ValueError(
            "配置文件中缺少 'dify.workflows' 配置节点。"
            "请确保 config.yaml 包含 dify.workflows 配置。"
        )

    workflows_config = dify_config["workflows"]

    # 4. 验证 workflow_name 存在
    if workflow_name not in workflows_config:
        available = list(workflows_config.keys())
        raise ValueError(
            f"工作流 '{workflow_name}' 不存在。"
            f"可用的工作流: {', '.join(available)}"
        )

    # 5. 提取 workflow 配置
    workflow_config = workflows_config[workflow_name]

    # 6. 合并全局配置
    # 提取全局配置 (base_url, timeout, max_retries 等)
    global_config = {
        k: v
        for k, v in dify_config.items()
        if k != "chats" and k != "workflows" and not isinstance(v, dict)
    }

    # 7. 返回合并后的配置
    return {**global_config, **workflow_config}


def validate_config(config: Dict[str, Any]) -> None:
    """
    验证配置的正确性和完整性

    Args:
        config: 配置字典

    Raises:
        ValueError: 配置验证失败
    """
    # 验证必需字段
    if "api_key" not in config or not config["api_key"]:
        raise ValueError("配置中缺少必需字段: api_key")

    # 验证字段类型和值范围
    if "timeout" in config:
        timeout = config["timeout"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"timeout 必须是正数,当前值: {timeout}")

    if "max_retries" in config:
        max_retries = config["max_retries"]
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError(f"max_retries 必须是非负整数,当前值: {max_retries}")

    if "base_url" in config:
        base_url = config["base_url"]
        if not isinstance(base_url, str) or not base_url:
            raise ValueError(f"base_url 必须是非空字符串,当前值: {base_url}")
