import os
from dotenv import load_dotenv
import requests
# 加载.env文件
load_dotenv()

class MySQLManager:
    def __init__(self, config_file: str = ".env"):
        """
        初始化MySQL数据库管理器，从.env文件读取配置

        Args:
            config_file: 配置文件路径，默认为".env"
        """
        # 从环境变量获取数据库配置
        self.host = os.getenv('DB_HOST', 'localhost')
        self.database = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.connection = None
        self.api_url_ds = os.getenv('SQL_DataBase')

    def request_api_sql(self,sql):
        try:
            response = requests.post(self.api_url_ds, json={"sql": sql})
            # print(response.json())
            outer_data = response.json()  # 第一层解析

            # print(outer_data)
            return outer_data # 现在是真正的 list of dict
        except:
            return []


if __name__ == "__main__":
    # main()
    db_manager = MySQLManager()
    #query = "SELECT TO_CHAR(park_added_value)111 AS added_value FROM v_ai_ipark_economic_operation WHERE TO_CHAR(report_month) = TO_CHAR(ADD_MONTHS(SYSDATE, -1), 'YYYY-MM');"
    params = {}
    params["year"] = '2025'
    params["month"] = '09'

    query = '''
SELECT
  TO_CHAR(park_name) AS 园区名称,
  TO_CHAR(riskTime) AS 统计月份,
  TO_CHAR(riskLevel) AS 园区每日最高风险等级
FROM
  v_ai_ipark_ra_park_daily_risk_summary_park
WHERE
  park_name = '岱山经济开发区'
  AND TO_CHAR(TO_DATE(riskTime, 'YYYY-MM-DD'), 'YYYY-MM') = '{year}-{month}'
ORDER BY
  TO_DATE(riskTime, 'YYYY-MM-DD');
'''
    query = query.format_map(params)
    #query='SELECT TO_CHAR(park_name) AS "园区 名称", TO_CHAR(park_code) AS 园区编码 FROM v_ai_ipark_safety_park_basic_info'
    res=db_manager.request_api_sql(query)
    print(res)








