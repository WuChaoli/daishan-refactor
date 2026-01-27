
import json
import os
from datetime import date, datetime, time
from dotenv import load_dotenv
import requests
# 加载.env文件
load_dotenv()
import re



class DateTimeEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，用于处理日期时间类型
    """

    def default(self, obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return super().default(obj)


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
        self.api_url_ds = "http://192.168.1.231/hzfj-ai-dm/api/dataQuery/query001"

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
    query = "SELECT TO_CHAR(park_added_value)111 AS added_value FROM v_ai_ipark_economic_operation WHERE TO_CHAR(report_month) = TO_CHAR(ADD_MONTHS(SYSDATE, -1), 'YYYY-MM');"
    query = '''
SELECT 
    CURRENT_DATE AS 当前时间,
    park_name AS 园区名称,
    riskTime AS 风险统计时间,
    riskValue AS 园区风险值,
    riskLevel AS 园区风险等级
FROM 
    v_ai_ipark_ra_park_daily_risk_summary_park
-- 按风险统计时间降序排序，取最新的一条
ORDER BY 
    riskTime DESC
LIMIT 1;
'''
    
    res=db_manager.request_api_sql(query)
    print(res)








