import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 DaiShanSQL 模块的 .env 文件
_module_dir = Path(__file__).resolve().parent
_env_path = _module_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)

from .api_server import Server
from .SQL.SQLAgent_toSql import SQLAgent
from .SQL.sql_utils import MySQLManager
from .SQL.sql_fixed import SQLFixed

__version__ = "0.2.1"
__all__ = ['Server', 'SQLAgent', 'MySQLManager', 'SQLFixed']