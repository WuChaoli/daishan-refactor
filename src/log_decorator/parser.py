"""对象解析模块

提供智能对象解析与日志值渲染功能，支持：
- 基础类型直接返回
- 紧凑模式：类对象显示为 <ClassName: N attrs>，字典显示为 <dict: N keys>
- 完整模式：容器类型递归解析，类实例展开为字典
- 日志模式：优先输出参数真实值，类对象优先调用 ``to_json``
- 深度控制：防止过深的递归
"""
from typing import Any, Dict


def parse_obj(obj: Any, compact: bool = True, max_depth: int = 3, _current_depth: int = 0) -> Any:
    """递归解析Python对象

    Args:
        obj: 任意Python对象
        compact: 是否使用紧凑格式（默认True）
        max_depth: 最大递归深度（默认3）
        _current_depth: 当前递归深度（内部使用）

    Returns:
        解析后的对象
        - compact=True: 类对象返回 "<ClassName: N attrs>"，字典返回 "<dict: N keys>"
        - compact=False: 完全展开对象（向后兼容）
    """
    # 基础类型直接返回
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    # 检查深度限制
    if _current_depth >= max_depth:
        return str(obj)

    # 紧凑模式
    if compact:
        # 字典：显示键数量
        if isinstance(obj, dict):
            return f"<dict: {len(obj)} keys>"

        # 列表：显示元素数量
        if isinstance(obj, list):
            return f"<list: {len(obj)} items>"

        # 元组：显示元素数量
        if isinstance(obj, tuple):
            return f"<tuple: {len(obj)} items>"

        # 类实例：显示类名和属性数量
        if hasattr(obj, "__dict__") and not callable(obj):
            attrs = obj.__dict__
            # 计算非内置属性数量
            attr_count = sum(1 for key in attrs.keys() if not key.startswith("__"))
            class_name = obj.__class__.__name__
            return f"<{class_name}: {attr_count} attrs>"

        # 其他类型转为字符串
        return str(obj)

    # 完整模式（向后兼容）
    # 列表或元组：递归解析每个元素
    if isinstance(obj, (list, tuple)):
        return type(obj)(
            parse_obj(item, compact=False, max_depth=max_depth, _current_depth=_current_depth + 1)
            for item in obj
        )

    # 字典：递归解析每个value
    if isinstance(obj, dict):
        return {
            key: parse_obj(value, compact=False, max_depth=max_depth, _current_depth=_current_depth + 1)
            for key, value in obj.items()
        }

    # 类实例：展开为字典（排除函数类型）
    if hasattr(obj, "__dict__") and not callable(obj):
        attrs = obj.__dict__.copy()
        # 过滤 __ 开头的内置属性
        filtered_attrs = {
            key: parse_obj(value, compact=False, max_depth=max_depth, _current_depth=_current_depth + 1)
            for key, value in attrs.items()
            if not key.startswith("__")
        }
        # 如果没有属性，转为字符串
        if not filtered_attrs:
            return str(obj)
        return filtered_attrs

    # 其他类型转为字符串
    return str(obj)


def render_log_value(obj: Any, max_depth: int = 5, _current_depth: int = 0) -> Any:
    """渲染日志值。

    规则：
    - ``int/float/str/bool/None``：原样输出
    - ``list/tuple/dict``：递归展开，尽量打印完整值
    - 类对象：优先调用 ``to_json``，失败或不存在时回退 ``str(obj)``
    """
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    if _current_depth >= max_depth:
        return str(obj)

    if isinstance(obj, list):
        return [
            render_log_value(item, max_depth=max_depth, _current_depth=_current_depth + 1)
            for item in obj
        ]

    if isinstance(obj, tuple):
        return tuple(
            render_log_value(item, max_depth=max_depth, _current_depth=_current_depth + 1)
            for item in obj
        )

    if isinstance(obj, dict):
        rendered: Dict[Any, Any] = {}
        for key, value in obj.items():
            rendered[key] = render_log_value(
                value,
                max_depth=max_depth,
                _current_depth=_current_depth + 1,
            )
        return rendered

    to_json = getattr(obj, "to_json", None)
    if callable(to_json):
        try:
            json_obj = to_json()
            return render_log_value(
                json_obj,
                max_depth=max_depth,
                _current_depth=_current_depth + 1,
            )
        except Exception:
            return str(obj)

    return str(obj)


def format_args_multiline(args: tuple, kwargs: dict, named_args: dict | None = None) -> str:
    """格式化参数为多行缩进格式

    Args:
        args: 位置参数元组
        kwargs: 关键字参数字典

    Returns:
        多行缩进格式的字符串
        格式示例：
        【入参】
          - args[0]: <ClassName: N attrs>
          - kwargs.key: value
    """
    lines = ["【入参】"]

    if named_args is not None:
        for key, value in named_args.items():
            parsed = render_log_value(value)
            lines.append(f"  - {key}: {parsed}")
    else:
        for i, arg in enumerate(args):
            parsed = render_log_value(arg)
            lines.append(f"  - args[{i}]: {parsed}")

        for key, value in kwargs.items():
            parsed = render_log_value(value)
            lines.append(f"  - kwargs.{key}: {parsed}")

    return "\n".join(lines)


def format_result_multiline(result: Any, duration_ms: float = None) -> str:
    """格式化返回值为多行缩进格式

    Args:
        result: 函数返回值
        duration_ms: 执行时间（毫秒），可选

    Returns:
        多行缩进格式的字符串
        格式示例：
        【出参】
          - result: <ClassName: N attrs>
          - 执行时间: 234.56ms
    """
    lines = ["【出参】"]

    # 格式化返回值
    parsed = render_log_value(result)
    lines.append(f"  - result: {parsed}")

    # 添加执行时间（如果提供）
    if duration_ms is not None:
        lines.append(f"  - 执行时间: {duration_ms}ms")

    return "\n".join(lines)


# 敏感信息脱敏规则
def _sanitize_api_key(value: str) -> str:
    """脱敏API密钥"""
    if not isinstance(value, str):
        return "***"
    # 查找分隔符（- 或 _）
    for sep in ["-", "_"]:
        if sep in value:
            prefix = value.split(sep)[0]
            return f"{prefix}-***"
    # 没有分隔符，长度>8显示前8位
    if len(value) > 8:
        return f"{value[:8]}***"
    return "***"


def _sanitize_token(value: str) -> str:
    """脱敏Token"""
    if not isinstance(value, str):
        return "***"
    if len(value) > 10:
        return f"{value[:6]}...{value[-4:]}"
    return "***"


SENSITIVE_PATTERNS = {
    "api_key": _sanitize_api_key,
    "password": lambda v: "***",
    "token": _sanitize_token,
    "secret": lambda v: "***",
    "key": _sanitize_api_key,  # 使用与api_key相同的规则
}



def sanitize_sensitive_data(data: Any) -> Any:
    """脱敏敏感信息

    Args:
        data: 任意数据

    Returns:
        脱敏后的数据
    """
    # 基础类型直接返回
    if data is None or isinstance(data, (int, float, bool)):
        return data

    # 字符串直接返回（不在字典中无法判断是否敏感）
    if isinstance(data, str):
        return data

    # 列表：递归处理每个元素
    if isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]

    # 元组：递归处理每个元素
    if isinstance(data, tuple):
        return tuple(sanitize_sensitive_data(item) for item in data)

    # 字典：检查键名并脱敏
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 检查键名是否匹配敏感模式（大小写不敏感）
            key_lower = key.lower()
            is_sensitive = False
            sanitizer = None

            for pattern, sanitize_func in SENSITIVE_PATTERNS.items():
                if pattern in key_lower:
                    is_sensitive = True
                    sanitizer = sanitize_func
                    break

            if is_sensitive:
                # 应用脱敏规则
                if isinstance(value, str):
                    result[key] = sanitizer(value)
                else:
                    # 非字符串敏感值统一返回 "***"
                    result[key] = "***"
            elif isinstance(value, (dict, list, tuple)):
                # 递归处理嵌套结构
                result[key] = sanitize_sensitive_data(value)
            else:
                # 非敏感数据保持不变
                result[key] = value

        return result

    # 其他类型直接返回
    return data


# 导出
__all__ = [
    "parse_obj",
    "render_log_value",
    "format_args_multiline",
    "format_result_multiline",
    "sanitize_sensitive_data",
]


