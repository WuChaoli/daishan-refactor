import logging
import os

import requests
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


logger = logging.getLogger(__name__)


class MySQLManager:
    @staticmethod
    def _print_full_sql(sql: str) -> None:
        if not isinstance(sql, str):
            return
        print(f"[DaiShanSQL FULL SQL] {sql}", flush=True)

    def __init__(self, config_file: str = ".env"):
        """
        初始化MySQL数据库管理器，从.env文件读取配置

        Args:
            config_file: 配置文件路径，默认为".env"
        """
        # 从环境变量获取数据库配置
        self.host = os.getenv("DB_HOST", "localhost")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.connection = None
        self.api_url_ds = os.getenv("SQL_DataBase")
        self.request_timeout = float(os.getenv("SQL_API_TIMEOUT", "15"))

    @staticmethod
    def _build_error_result(message: str, *, code: int = 500, **extra):
        result = {
            "code": code,
            "msg": message,
            "data": [],
        }
        result.update(extra)
        return result

    def request_api_sql(self, sql):
        self._print_full_sql(sql)

        if not self.api_url_ds:
            message = "SQL_DataBase is not configured"
            logger.error(message)
            return self._build_error_result(message)

        try:
            response = requests.post(
                self.api_url_ds,
                json={"sql": sql},
                timeout=self.request_timeout,
            )
        except requests.RequestException as error:
            message = f"request failed: {error}"
            logger.error(message)
            return self._build_error_result(message, error=str(error))

        try:
            outer_data = response.json()
        except ValueError as error:
            message = "invalid json response from SQL API"
            logger.error("%s: %s", message, error)
            return self._build_error_result(
                message,
                code=response.status_code or 500,
                error=str(error),
                response_text=(response.text or "")[:500],
            )

        if isinstance(outer_data, dict):
            normalized = dict(outer_data)
            normalized.setdefault("code", response.status_code or 200)
            normalized.setdefault("msg", "")
            normalized.setdefault("data", [])
            return normalized

        if isinstance(outer_data, list):
            return {
                "code": 200
                if response.status_code == 200
                else (response.status_code or 500),
                "msg": "ok",
                "data": outer_data,
            }

        message = f"unexpected response type: {type(outer_data).__name__}"
        logger.error(message)
        return self._build_error_result(
            message,
            code=response.status_code or 500,
            response_text=(response.text or "")[:500],
        )


if __name__ == "__main__":
    # main()
    db_manager = MySQLManager()
    # query = "SELECT TO_CHAR(park_added_value)111 AS added_value FROM v_ai_ipark_economic_operation WHERE TO_CHAR(report_month) = TO_CHAR(ADD_MONTHS(SYSDATE, -1), 'YYYY-MM');"
    params = {}
    params["year"] = "2025"
    params["month"] = "09"

    query = """
SELECT * FROM v_ai_ipark_sys_person
"""
    query = query.format_map(params)
    # query='SELECT TO_CHAR(park_name) AS "园区 名称", TO_CHAR(park_code) AS 园区编码 FROM v_ai_ipark_safety_park_basic_info'
    res = db_manager.request_api_sql(query)
    print(res)
