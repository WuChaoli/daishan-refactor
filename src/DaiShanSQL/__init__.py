"""
DaiShanSQL - 岱山 SQL 查询包

提供基于自然语言的 SQL 查询功能
"""

# 从内层包重新导出主要类
from DaiShanSQL.DaiShanSQL.api_server import Server
from DaiShanSQL.DaiShanSQL.SQL.SQLAgent_toSql import SQLAgent
from DaiShanSQL.DaiShanSQL.SQL.sql_utils import MySQLManager
from DaiShanSQL.DaiShanSQL.SQL.sql_fixed import SQLFixed

__version__ = "0.2.1"
__all__ = ['Server', 'SQLAgent', 'MySQLManager', 'SQLFixed']
