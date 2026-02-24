
import json
import os
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
from ..Utils.tools import Tool
from openai import OpenAI
import copy


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

    def unFixSQL(self,query,table_data,params):
        ParkOverview_time=["园区今年工业总产值","园区规上工业总产值","园区今年亩均产值","园区今年亩均税收","园区某月规上工业产值同比增速"]
        sql_res = []
        if table_data['question'] in ParkOverview_time:
            #处理园区总览中涉及时间相关语句
            prompt = self.prompt_utils.extractTime(query)
            time = self.extractItem(prompt)
            params["year_value"] = (time["year"])
            if table_data['question'] == "园区某月规上工业产值同比增速":
                month = time["month"]                
                params["month_value"] = f"{month:02d}"
            results = []
            for item in table_data['SQL']:
                item=item.format_map(params)
                print(item)
                result = self.sqlmanager.request_api_sql(item)['data']
                results.append(result)
        sql_res.append({"问题":query,"数据库查询结果":results})
        return sql_res
    
    def extractItem(self,prompt):
        '''
        基于用户问题抽取对应内容
        '''
        item = self.chat_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv("Qwen2.5_7B_model"),
        )
        json_obj=json.loads(item.choices[0].message.content)
        print(item.choices[0].message.content)
        return json_obj
    
    def FixSQL(self,query,table_data,params):
        '''
        处理固定SQL
        :param query: 用户问题
        :param table_data: 对应SQL
        '''
        SQLs= table_data["SQL"]
        results = []
        sql_res = []
        for item in SQLs:
            if params:
                item = item.format_map(params)
            result = self.sqlmanager.request_api_sql(item)['data']
            results.append(result)
        sql_res.append({"问题":query,"数据库查询结果":results})
        return sql_res
    def judgeQuery(self,query,returnQuestion):
        # 1、获取表的信息
        table_data = copy.deepcopy([data for data in self.table_plus if data['question'] == returnQuestion][0])

        # 2、获取对应园区
        params = {}
        if "NeedPark" in table_data["extractItem"]:
            prompt = self.prompt_utils.extractPark(query)
            park = self.extractItem(prompt) 
            params["parkName"] = park["park"]
        if "NeedYear" in table_data["extractItem"]:
            prompt = self.prompt_utils.extractTime(query)
            time = self.extractItem(prompt)
            params["year_value"] = (time["year"])
        if "NeedMonth" in table_data["extractItem"]:
            prompt = self.prompt_utils.extractTime(query)
            time = self.extractItem(prompt)
            month = time["month"]                
            params["month_value"] = f"{month:02d}"
        if "NeedCompany" in table_data["extractItem"]:
            prompt = self.prompt_utils.extractCompany(query)
            company = self.extractItem(prompt)
            params["company_name"] = company["company"]
        if "NeedWeek" in table_data["extractItem"]:
            prompt = self.prompt_utils.extractWeek(query)
            company = self.extractItem(prompt)
            params["week_value"] = company["week"]
        res = self.FixSQL(query,table_data,params)
        return res
if __name__ == '__main__':
    SQLplus = SQLPlus()
    SQLplus.judgeQuery("岱山经开区（岱山经济开发区）园区负责人联系方式")
