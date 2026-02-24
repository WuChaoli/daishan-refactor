
import json
import os
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
from ..Utils.tools import Tool
from openai import OpenAI
import copy
import re


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

class SQLPlus():
    def __init__(self):
        self.tools_manager = Tool()  
        self.prompt_utils = Prompt_Templete()
        self.sqlmanager = MySQLManager()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        Table_path = os.path.join(current_dir,"data/岱山固定查询.jsonl")
        
        self.table_plus = read_jsonl_file(Table_path)
        self.chat_client = OpenAI(
            base_url=os.getenv("Qwen2.5_7B_base_url"),
            api_key=os.getenv("Qwen2.5_7B_api_key"),
        )
    
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
            # print("模型原始返回内容:")
            # print(content)
            # 清洗内容 - 提取JSON部分（处理模型返回多余文字的情况）
            # 匹配最外层的 {} 包裹的JSON内容
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                clean_content = json_match.group(0)
            else:
                clean_content = content
            
            json_obj = json.loads(clean_content)
            return json_obj

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: 返回内容不是合法的JSON格式。错误详情: {str(e)}")
            # print(f"原始返回内容: {content if 'content' in locals() else '无'}")
            # 返回空字典作为兜底，避免程序崩溃
            return {}
    def FixSQL(self,query,table_data,params):
        '''
        处理固定SQL
        :param query: 用户问题
        :param table_data: 对应SQL
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
                result = self.sqlmanager.request_api_sql(formatted_sql)['data']
                results.append(result)
            except KeyError as e:
                # 捕获format_map时参数缺失的错误
                error_msg = f"SQL参数格式化失败: 缺少参数 {e}，原始SQL: {item}"
                print(f"[ERROR] {error_msg}")  # 打印错误日志
        sql_res.append({"问题":query,"数据库查询结果":results})
        return sql_res
    def judgeQuery(self,query,returnQuestion):
        # 获取表的信息
        table_data = copy.deepcopy(next(data for data in self.table_plus if data['question'] == returnQuestion))

        # 定义字段映射配置：key是extractItem中的标识，value是处理规则
        # 格式：(prompt方法名, 结果键名, params键名, 格式化函数)
        field_configs = {
            "NeedPark": ("extractPark", "park", "parkName", lambda x: x),
            "NeedYear": ("extractTime", "year", "year_value", lambda x: x),
            "NeedMonth": ("extractTime", "month", "month_value", lambda x: f"{x:02d}"),
            "NeedCompany": ("extractCompany", "company", "company_name", lambda x: x),
            "NeedWeek": ("extractWeek", "week", "week_value", lambda x: x),
        }

        params = {}
        extract_items = table_data.get("extractItem", [])
        # 遍历配置，统一处理所有字段
        for item_key, (prompt_method, res_key, param_key, formatter) in field_configs.items():
            if item_key in extract_items:
                try:
                    # 获取prompt
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
    SQLplus.judgeQuery("岱山经开区（岱山经济开发区）园区负责人联系方式")
