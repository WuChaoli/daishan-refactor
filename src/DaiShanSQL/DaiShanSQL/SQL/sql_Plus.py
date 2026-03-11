
import json
import os
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
from ..Utils.tools import Tool
from openai import OpenAI
import copy
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import calendar

def read_jsonl_file(file_path: str):
    data_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                data_list.append(data)
            except json.JSONDecodeError as e:
                print(f"警告：第{line_num}行JSON格式错误，已跳过 - {e}")

    return data_list

class TimeWeekExtractor:
    def __init__(self):
        # 定义常见时间词匹配规则（覆盖园区场景高频表述）
        self.time_patterns = {
            # 基础时间词
            '上个月': r'上个月|上个月份|上一个月|上一个月份',
            '本月': r'本月|这个月|这个月份',
            '上上个月': r'上上个月|两个月前|2个月前|两月前|2月前',
            '三个月前': r'三个月前|3个月前|三月前|3月前',
            '昨天': r'昨天',
            '今天': r'今天',
            '上周': r'上周',
            '本周': r'本周|这个周',
            '上上周': r'上上周|两周前|2周前',
            '三周前': r'3周前|三周前',
            '去年': r'去年',
            '今年': r'今年',
            '上季度': r'上季度|上个季度',
            '本季度': r'本季度'
        }
        
    def extract_time_word(self, sentence):
        """
        从句子中抽取匹配的时间词（优先匹配长词，避免歧义）
        :param sentence: 用户输入的句子
        :return: 匹配到的时间词（如"上个月"），无则返回None
        """
        sorted_patterns = sorted(self.time_patterns.items(), key=lambda x: len(x[1]), reverse=True)
        
        for time_word, pattern in sorted_patterns:
            if re.search(pattern, sentence):
                return time_word
        return None
    
    def get_year_week(self, date):
        """
        计算指定日期对应的【年份】和【周数】
        规则：按ISO标准（周一为一周起始，一年至少52周），兼容国内常用的周日起始规则
        :param date: datetime对象
        :return: (year, week) 元组，如(2026, 10)
        """
        # ISO周（推荐，国际通用）：返回 (ISO年, ISO周数)
        isoyear, isoweek, _ = date.isocalendar()
        # 若需要国内常用的“周日为一周起始”，可取消下面注释并调整
        # week = (date.day - date.weekday() - 1) // 7 + 1
        return isoyear, isoweek
    
    def calculate_year_week(self, query, base_date=None):
        """
        根据时间词和基准日期，计算对应时间的【年份+周数】
        :param time_word: 抽取到的时间词
        :param base_date: 基准日期（默认当前日期）
        :return: 字典 {"year": 年份, "week": 周数}，无匹配则返回None
        """
        time_word = self.extract_time_word(query)

        if base_date is None:
            base_date = datetime.now()  # 默认用当前系统时间
        
        target_date = None
        # 核心日期计算逻辑（先确定目标日期，再转成周数）
        if time_word == '上个月':
            # 上个月 → 取上个月最后一天的周数
            target_date = base_date - relativedelta(months=1)
            # target_date = self.get_last_day_of_month(target_date)
        
        elif time_word == '本月':
            # 本月 → 取当前日期的周数
            target_date = base_date
        
        elif time_word == '上上个月':
            target_date = base_date - relativedelta(months=2)
        elif time_word == '三个月前':
            target_date = base_date - relativedelta(months=3)
            # target_date = self.get_last_day_of_month(target_date)
        
        elif time_word == '昨天':
            target_date = base_date - timedelta(days=1)
        
        elif time_word == '今天':
            target_date = base_date
        
        elif time_word == '上周':
            target_date = base_date - timedelta(days=base_date.weekday() + 2)
        elif time_word == '上上周':
            target_date = base_date - timedelta(days=base_date.weekday() + 3)
        elif time_word == '三周前':
            target_date = base_date - timedelta(days=base_date.weekday() + 3)
        
        elif time_word == '本周':
            target_date = base_date
        
        elif time_word == '去年':
            # 去年 → 取去年同一天的周数
            target_date = base_date - relativedelta(years=1)
        elif time_word == '上季度':
            # 上季度 → 取上季度最后一天的周数
            quarter = (base_date.month - 1) // 3
            last_month_of_last_quarter = quarter * 3
            if last_month_of_last_quarter == 0:
                last_month_of_last_quarter = 12
                target_year = base_date.year - 1
            else:
                target_year = base_date.year
            target_date = datetime(target_year, last_month_of_last_quarter, 1)
            # target_date = self.get_last_day_of_month(target_date)
        
        elif time_word == '本季度':
            # 本季度 → 取本季度第一天的周数
            quarter = (base_date.month - 1) // 3
            first_month_of_quarter = quarter * 3 + 1
            target_date = datetime(base_date.year, first_month_of_quarter, 1)
        
        # 计算年份和周数
        if target_date:
            year, week = self.get_year_week(target_date)
            return {"year": year, "week": week}
        else:
            return None
    
    def get_last_day_of_month(self, date):
        """辅助函数：获取指定日期所在月份的最后一天"""
        next_month = date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    
class SQLPlus():
    def __init__(self):
        self.tools_manager = Tool()  
        self.prompt_utils = Prompt_Templete()
        self.sqlmanager = MySQLManager()
        self.weekExtractor = TimeWeekExtractor()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        Table_path = os.path.join(current_dir,"data/岱山固定查询.jsonl")
        
        self.table_plus = read_jsonl_file(Table_path)
        self.chat_client = OpenAI(
            base_url=os.getenv("Qwen2.5_7B_base_url"),
            api_key=os.getenv("Qwen2.5_7B_api_key"),
        )
        self._last_execution_log = []

    def _record_execution(self, sql_text, result=None, error=""):
        self._last_execution_log.append(
            {
                "sql_text": str(sql_text or ""),
                "result": result,
                "error": str(error or ""),
            }
        )

    def consume_last_execution_log(self):
        logs = list(self._last_execution_log)
        self._last_execution_log = []
        return logs
    
    def extractItem(self, prompt):
        '''
        基于用户问题抽取对应内容
        '''
        try:
            item = self.chat_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=os.getenv("Qwen2.5_7B_model"),
            )
            content = item.choices[0].message.content
            # 清洗内容 - 提取JSON部分（处理模型返回多余文字的情况）
            # 匹配最外层的 {} 包裹的JSON内容
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                clean_content = json_match.group(0)
            else:
                clean_content = content
            # print(clean_content)
            json_obj = json.loads(clean_content)
            return json_obj

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: 返回内容不是合法的JSON格式。错误详情: {str(e)}")
            return {}
    def FixSQL(self,query,table_data,params):
        '''
        处理固定SQL
        :param query: 用户问题
        :param table_data: 对应SQL
        :param params: 格式化参数
        '''
        SQLs = table_data.get("SQL", [])
        results = []
        sql_res = []
        for item in SQLs:
            try:
                if params:
                    formatted_sql = item.format_map(params)
                else:
                    formatted_sql = item
                content = self.sqlmanager.request_api_sql(formatted_sql)
                print("sql:",formatted_sql)
                if content:
                    self._record_execution(formatted_sql, content.get('data'))
                    results.append(content['data'])
                else:
                    self._record_execution(formatted_sql, ["数据库查询失败"])
                    results.append(["数据库查询失败"])
            except KeyError as e:
                # 捕获format_map时参数缺失的错误
                error_msg = f"SQL参数格式化失败: 缺少参数 {e}，原始SQL: {item}"
                print(f"[ERROR] {error_msg}")  # 打印错误日志
        sql_res.append({"问题":query,"数据库查询结果":results})
        return sql_res
    
    def getTableData(self,query,returnQuestion):
        '''
        处理因为相似度太高导致的错误匹配
        '''    
        params = {}
        stop_keywords = ["信息"]
        qualifications = ["安全生产知识和管理考核能力合格证书", "安全生产知识和管理能力考核合格证书", "安全生产知识和管理能力考核合格证", "安全生产知识和管理能力考核证书", "安全生产知识和管理能力", "化工自动化控制仪表作业", "快开门式压力容器操作", "锅炉压力管道管理", "厂内机动车辆作业", "注册安全工程师证书", "注册安全工程师证", "安全管理人员证书", "主要负责人证书", "特种设备操作证", "高压电工作业", "低压电工作业", "特种设备安全管理", "注册安全工程师", "工业锅炉司炉", "G1工业锅炉司炉", "聚合工艺作业", "加氢工艺作业", "氧化工艺作业", "高级工程师", "N1叉车司机", "电工作业", "气瓶充装", "锅炉水处理", "工程师", "安全管理", "电工", "工程"]
        for keyword in stop_keywords:
            if keyword in query:
                for qualification in qualifications:
                    if qualification in query:
                        params['qualification_type'] = qualification
                        return params,copy.deepcopy(next(data for data in self.table_plus if data['question'] == "某许可证详细信息"))

        return params,copy.deepcopy(next(data for data in self.table_plus if data['question'] == returnQuestion))
  
    def judgeQuery(self,query,returnQuestion):
        '''
        主要函数
        :param query: 用户问题
        :param returnQuestion: 匹配到的最相似问题
        ''' 
        # 获取表的信息
        params,table_data = self.getTableData(query,returnQuestion)
        print(returnQuestion)
        print(table_data)

        # 定义字段映射配置：key是extractItem中的标识，value是处理规则
        # 格式：(prompt方法名, 结果键名, params键名, 格式化函数)
        field_configs = {
            "NeedPark": ("extractPark", "park", "parkName", lambda x: x),
            "NeedYear": ("extractTime", "year", "year_value", lambda x: x),
            "NeedMonth": ("extractTime", "month", "month_value", lambda x: f"{x:02d}"),
            "NeedCompany": ("extractCompany", "company", "company_name", lambda x: x),
            "NeedWeek": ("extractWeek", "week", "week_value", lambda x: x),
            "NeedPersonName": ("extractPersonName", "person", "person_name", lambda x: x),
            "NeedRiskLevel": ("extractRiskLevel", "riskLevel", "riskLevel_value", lambda x: x),
            # "NeedQualification": ("extractQualification", "qualification", "qualification_type", lambda x: x) NeedQualification在getTableData时特殊处理
        }
        extract_items = table_data.get("extractItem", [])
        # 遍历配置，统一处理所有字段
        for item_key, (prompt_method, res_key, param_key, formatter) in field_configs.items():
            if item_key in extract_items:
                try:
                    # 获取prompt
                    if item_key == "NeedWeek":
                        year_week = self.weekExtractor.calculate_year_week(query)
                        if year_week:
                            year_value = year_week['year']
                            week_value = year_week['week']
                        else:
                            year_value = 'None'
                            week_value = 'None'
                        params['year_value'] = year_value
                        params['week_value'] = week_value
                    else:
                        prompt = getattr(self.prompt_utils, prompt_method)(query)
                        extract_result = self.extractItem(prompt)
                        if extract_result and isinstance(extract_result, dict) and res_key in extract_result:
                            raw_value = extract_result[res_key]
                            # 对原始值进行None判断，避免格式化None值
                            if raw_value is not None:
                                params[param_key] = formatter(raw_value)
                        
                except (TypeError, AttributeError, KeyError) as e:
                    # 捕获格式化、属性访问、键缺失等异常
                    print(f"处理 {item_key} 时发生错误：{str(e)}，已跳过该字段处理")
                    continue

        res = self.FixSQL(query, table_data, params)
        return res
if __name__ == '__main__':
    SQLplus = SQLPlus()
