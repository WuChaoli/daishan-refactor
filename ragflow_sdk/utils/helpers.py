"""工具函数模块"""

from typing import Any, Dict


def deep_update(
    base_dict: Dict[str, Any], update_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    深度更新字典

    Args:
        base_dict: 基础字典
        update_dict: 更新字典

    Returns:
        更新后的字典
    """
    result = base_dict.copy()
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    return result


def ensure_url(url: str) -> str:
    """
    确保 URL 格式正确

    Args:
        url: 原始 URL

    Returns:
        格式化后的 URL
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
