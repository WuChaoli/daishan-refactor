"""
LogManager - 日志管理器
负责创建和管理分层日志系统

功能:
- 全局日志: info.log, error.log, debug.log, timing.log
- 功能模块日志: functions/*.log
- 终端输出: INFO → stdout (绿色), ERROR → stderr (红色)
- Error 汇聚: 所有模块的 ERROR 同步到全局 error.log
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.config import Config


class LogManager:
    """
    日志管理器

    日志结构:
    logs/
    ├── global/
    │   ├── info.log      # 全局 INFO 日志
    │   ├── error.log     # 全局 ERROR 日志 (汇聚所有模块的错误)
    │   ├── debug.log     # 全局 DEBUG 日志
    │   └── timing.log    # 请求执行时间日志
    ├── functions/        # 功能模块日志
    │   ├── api_interface.log
    │   ├── intent_judgment.log
    │   └── ...
    └── archive/          # 归档目录
    """

    def __init__(self, config: Config):
        """
        初始化日志系统

        Args:
            config: 应用配置
        """
        self.config = config
        self.log_dir = Path(config.log_dir)

        # 创建日志目录结构
        self._setup_log_directories()

        # 全局日志器
        self._info_logger: Optional[logging.Logger] = None
        self._debug_logger: Optional[logging.Logger] = None
        self._error_logger: Optional[logging.Logger] = None
        self._timing_logger: Optional[logging.Logger] = None

        # 功能级日志器缓存
        self._function_loggers: dict = {}

        # 初始化全局日志
        self._setup_global_loggers()

        # 设置终端输出 (INFO → stdout 绿色, ERROR → stderr 红色)
        self._setup_console_handlers()

    def _setup_console_handlers(self):
        """
        设置终端输出 handler
        - INFO 级别 → stdout (绿色)
        - ERROR 级别 → stderr (红色)
        """
        # ANSI 颜色码
        GREEN = "\033[32m"
        RED = "\033[31m"
        RESET = "\033[0m"

        # 创建一个根 logger 用于终端输出
        console_logger = logging.getLogger("console")
        console_logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if console_logger.handlers:
            return

        # INFO handler → stdout (绿色)
        class InfoFilter(logging.Filter):
            """只允许 INFO 及以下级别通过 (不包括 WARNING, ERROR)"""

            def filter(self, record):
                return record.levelno < logging.WARNING

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.addFilter(InfoFilter())
        stdout_formatter = logging.Formatter(
            f"{GREEN}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stdout_handler.setFormatter(stdout_formatter)
        console_logger.addHandler(stdout_handler)

        # ERROR handler → stderr (红色)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)
        stderr_formatter = logging.Formatter(
            f"{RED}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stderr_handler.setFormatter(stderr_formatter)
        console_logger.addHandler(stderr_handler)

        # 保存引用
        self._console_logger = console_logger

    def _setup_log_directories(self):
        """创建日志目录结构"""
        directories = [
            self.log_dir / "global",
            self.log_dir / "functions",
            self.log_dir / "archive",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_global_loggers(self):
        """初始化全局日志器"""
        # 创建全局 INFO 日志
        self._info_logger = self._create_logger(
            "global_info", self.log_dir / "global" / "info.log", logging.INFO
        )

        # 创建全局 DEBUG 日志
        self._debug_logger = self._create_logger(
            "global_debug", self.log_dir / "global" / "debug.log", logging.DEBUG
        )

        # 创建全局 ERROR 日志
        self._error_logger = self._create_logger(
            "global_error", self.log_dir / "global" / "error.log", logging.ERROR
        )

        # 创建全局 TIMING 日志 (用于记录请求执行时间)
        self._timing_logger = self._create_logger(
            "global_timing",
            self.log_dir / "global" / "timing.log",
            logging.INFO,
            format_str="%(asctime)s - %(message)s",  # 简化格式，只记录时间和消息
        )

        # 记录初始化成功
        self.log_info("日志系统初始化完成")

    def _create_logger(
        self,
        name: str,
        log_file: Path,
        level: int,
        format_str: Optional[str] = None,
    ) -> logging.Logger:
        """
        创建日志器

        Args:
            name: 日志器名称
            log_file: 日志文件路径
            level: 日志级别
            format_str: 自定义日志格式 (可选)

        Returns:
            配置好的日志器
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 避免重复添加 handler
        if logger.handlers:
            return logger

        # 使用 RotatingFileHandler 实现日志切片
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.log_max_bytes,
            backupCount=self.config.log_backup_count,
            encoding="utf-8",
        )

        # 设置日志格式
        if format_str is None:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        return logger

    def get_function_logger(self, name: str) -> logging.Logger:
        """
        获取功能级日志器
        
        功能日志器的 ERROR 会同时写入:
        1. 自己的功能日志文件 (functions/{name}.log)
        2. 全局 error.log (汇聚所有模块的错误)

        Args:
            name: 功能名称 (如 'ragflow_client', 'intent_judgment')

        Returns:
            功能级日志器
        """
        if name not in self._function_loggers:
            log_file = self.log_dir / "functions" / f"{name}.log"
            logger = self._create_function_logger(name, log_file)
            self._function_loggers[name] = logger

        return self._function_loggers[name]

    def _create_function_logger(self, name: str, log_file: Path) -> logging.Logger:
        """
        创建功能级日志器，ERROR 自动同步到全局 error.log

        Args:
            name: 日志器名称
            log_file: 日志文件路径

        Returns:
            配置好的功能级日志器
        """
        logger = logging.getLogger(f"func_{name}")
        logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if logger.handlers:
            return logger

        # Handler 1: 功能日志文件 (所有级别)
        func_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.log_max_bytes,
            backupCount=self.config.log_backup_count,
            encoding="utf-8",
        )
        func_handler.setLevel(logging.DEBUG)
        func_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        func_handler.setFormatter(func_formatter)
        logger.addHandler(func_handler)

        # Handler 2: 全局 error.log (只有 ERROR 级别)
        # 使用全局 error.log 的路径
        global_error_file = self.log_dir / "global" / "error.log"
        error_handler = RotatingFileHandler(
            global_error_file,
            maxBytes=self.config.log_max_bytes,
            backupCount=self.config.log_backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)  # 只捕获 ERROR 及以上
        error_formatter = logging.Formatter(
            "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

        return logger

    def log_info(self, message: str):
        """记录全局 INFO 日志"""
        if self._info_logger:
            self._info_logger.info(message)

    def log_debug(self, message: str):
        """记录全局 DEBUG 日志"""
        if self._debug_logger:
            self._debug_logger.debug(message)

    def log_error(self, message: str, exc_info: bool = False):
        """记录全局 ERROR 日志

        Args:
            message: 错误消息
            exc_info: 是否包含异常堆栈信息
        """
        if self._error_logger:
            self._error_logger.error(message, exc_info=exc_info)

    def log_function(self, module: str, level: str, message: str, **kwargs):
        """
        记录功能级日志

        Args:
            module: 功能模块名称
            level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        logger = self.get_function_logger(module)
        log_func = getattr(logger, level.lower(), logger.info)

        # 添加额外上下文
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context}"

        log_func(message)

    def check_total_size(self) -> int:
        """
        检查当前日志总大小

        Returns:
            总大小（字节）
        """
        total_size = 0

        for log_file in self.log_dir.rglob("*.log"):
            if log_file.is_file():
                total_size += log_file.stat().st_size

        return total_size

    def cleanup_old_logs(self):
        """清理旧日志直到容量在限制内"""
        total_size = self.check_total_size()
        limit = self.config.log_total_size_limit

        if total_size <= limit:
            return

        self.log_warning(
            f"日志容量超限: {total_size / (1024 * 1024):.2f}MB > {limit / (1024 * 1024):.2f}MB"
        )

        # 获取所有日志文件并按修改时间排序
        log_files = []
        for log_file in self.log_dir.rglob("*.log"):
            if log_file.is_file():
                log_files.append((log_file, log_file.stat().st_mtime))

        # 按修改时间升序排序（最旧的在前）
        log_files.sort(key=lambda x: x[1])

        # 删除最旧的日志文件
        for log_file, mtime in log_files:
            if total_size <= limit:
                break

            file_size = log_file.stat().st_size
            log_file.unlink()
            total_size -= file_size

            self.log_info(f"已删除旧日志文件: {log_file}")

        self.log_info(f"日志清理完成，当前容量: {total_size / (1024 * 1024):.2f}MB")

    def log_warning(self, message: str):
        """记录全局 WARNING 日志"""
        if self._info_logger:
            self._info_logger.warning(message)

    def log_timing(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        extra: Optional[str] = None,
    ):
        """
        记录请求执行时间到 timing.log

        Args:
            endpoint: 请求端点 (如 '/intent')
            method: HTTP 方法 (如 'POST')
            duration_ms: 执行时间 (毫秒)
            status_code: HTTP 状态码
            extra: 额外信息 (可选)
        """
        if self._timing_logger:
            msg = f"{method} {endpoint} | {duration_ms:.2f}ms | {status_code}"
            if extra:
                msg += f" | {extra}"
            self._timing_logger.info(msg)

    def log_to_console(self, level: str, message: str):
        """
        输出到终端 (带颜色)

        Args:
            level: 日志级别 ('INFO', 'ERROR', 'DEBUG', 'WARNING')
            message: 日志消息
        """
        if hasattr(self, "_console_logger") and self._console_logger:
            log_func = getattr(self._console_logger, level.lower(), self._console_logger.info)
            log_func(message)
