"""
函数调用追踪器
用于追踪函数的调用路径、参数、返回值和执行时间
"""

import json
import time
import functools
import inspect
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, asdict


@dataclass
class FunctionCallRecord:
    """函数调用记录"""
    timestamp: str
    function_name: str
    module_name: str
    args: dict
    kwargs: dict
    return_value: Any
    execution_time_ms: float
    error: Optional[str] = None
    logs: Optional[list] = None  # 新增：捕获的日志

    def to_yaml_str(self) -> str:
        """转换为 YAML 字符串"""
        import yaml
        
        record_dict = asdict(self)
        # 处理不可序列化的对象
        record_dict['return_value'] = self._serialize_value(record_dict['return_value'])
        record_dict['args'] = {k: self._serialize_value(v) for k, v in record_dict['args'].items()}
        record_dict['kwargs'] = {k: self._serialize_value(v) for k, v in record_dict['kwargs'].items()}
        
        # 构建紧凑的第一行：时间戳和函数名
        first_line = f"{record_dict['timestamp']} - {record_dict['function_name']}"
        
        # 移除timestamp和function_name，它们已经在第一行了
        output_dict = {
            'module': record_dict['module_name'],
            'execution_time_ms': record_dict['execution_time_ms'],
            'args': record_dict['args'],
        }
        
        if record_dict['kwargs']:
            output_dict['kwargs'] = record_dict['kwargs']
        
        if record_dict['return_value'] is not None:
            output_dict['return_value'] = record_dict['return_value']
        
        if record_dict['error']:
            output_dict['error'] = record_dict['error']
        
        if record_dict['logs']:
            output_dict['logs'] = record_dict['logs']
        
        # 生成YAML，使用更紧凑的格式
        yaml_content = yaml.dump(output_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return f"{first_line}\n{yaml_content}"

    @staticmethod
    def _serialize_value(value: Any, max_depth: int = 3, current_depth: int = 0) -> Any:
        """序列化值，处理不可序列化的对象"""
        # 基本类型直接返回，不受深度限制
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value

        # 防止无限递归
        if current_depth >= max_depth:
            return f"<{type(value).__name__}...>"

        if isinstance(value, (list, tuple)):
            return [FunctionCallRecord._serialize_value(v, max_depth, current_depth + 1) for v in value]
        if isinstance(value, dict):
            return {k: FunctionCallRecord._serialize_value(v, max_depth, current_depth + 1) for k, v in value.items()}

        # 对于有 __dict__ 的对象，提取其属性
        if hasattr(value, '__dict__'):
            try:
                obj_dict = {}
                for k, v in value.__dict__.items():
                    # 跳过私有属性和方法
                    if not k.startswith('_'):
                        obj_dict[k] = FunctionCallRecord._serialize_value(v, max_depth, current_depth + 1)
                return {
                    '_type': type(value).__name__,
                    '_attrs': obj_dict
                }
            except Exception:
                return f"<{type(value).__name__} object>"

        # 其他情况转换为字符串
        return str(value)


import logging
from io import StringIO


class LogCapture(logging.Handler):
    """日志捕获器，用于捕获函数执行期间的日志"""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    
    def emit(self, record):
        """捕获日志记录"""
        try:
            msg = self.format(record)
            self.logs.append(msg)
        except Exception:
            pass
    
    def get_logs(self):
        """获取捕获的日志"""
        return self.logs


class FunctionTracer:
    """函数追踪器，负责记录函数调用信息到日志文件"""

    def __init__(self, log_file_path: str):
        """
        初始化函数追踪器

        Args:
            log_file_path: 日志文件路径
        """
        self.log_file_path = Path(log_file_path)
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """确保日志文件和目录存在"""
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file_path.exists():
            self.log_file_path.touch()

    def write_record(self, record: FunctionCallRecord):
        """
        写入函数调用记录到日志文件（从上往下，最新的在最上面）

        Args:
            record: 函数调用记录
        """
        try:
            # 读取现有内容
            existing_content = ""
            if self.log_file_path.exists() and self.log_file_path.stat().st_size > 0:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # 写入新记录在最前面
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(record.to_yaml_str())
                f.write('\n' + '='*80 + '\n')
                if existing_content:
                    f.write(existing_content)
        except Exception as e:
            print(f"写入追踪日志失败: {e}")


# 全局追踪器实例
_global_tracer: Optional[FunctionTracer] = None


def get_tracer() -> FunctionTracer:
    """获取全局追踪器实例"""
    global _global_tracer
    if _global_tracer is None:
        log_path = Path(__file__).parent.parent.parent / "logs" / "function_trace.log"
        _global_tracer = FunctionTracer(str(log_path))
    return _global_tracer


def trace_function(func: Callable) -> Callable:
    """
    函数追踪装饰器

    用法:
        @trace_function
        async def my_function(arg1, arg2):
            return result
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        tracer = get_tracer()
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 精确到秒

        # 获取函数签名和参数名
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # 构建参数字典
        args_dict = dict(bound_args.arguments)

        # 设置日志捕获
        log_capture = LogCapture()
        root_logger = logging.getLogger()
        root_logger.addHandler(log_capture)

        error_msg = None
        return_value = None

        try:
            # 执行函数
            return_value = await func(*args, **kwargs)
            return return_value
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            raise
        finally:
            # 移除日志捕获器
            root_logger.removeHandler(log_capture)
            captured_logs = log_capture.get_logs()
            
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 创建记录
            record = FunctionCallRecord(
                timestamp=timestamp,
                function_name=func.__name__,
                module_name=func.__module__,
                args=args_dict,
                kwargs={},
                return_value=return_value,
                execution_time_ms=round(execution_time, 2),
                error=error_msg,
                logs=captured_logs if captured_logs else None
            )

            # 写入日志
            tracer.write_record(record)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tracer = get_tracer()
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 精确到秒

        # 获取函数签名和参数名
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # 构建参数字典
        args_dict = dict(bound_args.arguments)

        # 设置日志捕获
        log_capture = LogCapture()
        root_logger = logging.getLogger()
        root_logger.addHandler(log_capture)

        error_msg = None
        return_value = None

        try:
            # 执行函数
            return_value = func(*args, **kwargs)
            return return_value
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            raise
        finally:
            # 移除日志捕获器
            root_logger.removeHandler(log_capture)
            captured_logs = log_capture.get_logs()
            
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 创建记录
            record = FunctionCallRecord(
                timestamp=timestamp,
                function_name=func.__name__,
                module_name=func.__module__,
                args=args_dict,
                kwargs={},
                return_value=return_value,
                execution_time_ms=round(execution_time, 2),
                error=error_msg,
                logs=captured_logs if captured_logs else None
            )

            # 写入日志
            tracer.write_record(record)

    # 根据函数类型返回对应的包装器
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
