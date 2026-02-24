from datetime import datetime
import json
import os
import traceback

from 岱山.sql_chater.intent.api_intent import client
from ..Utils.ProcessUtils import ProcessUtils
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
# from ..intent.api_intent import API_Embedding
from ..Utils.api_intent import API_Embedding
from ..Utils.AsynchronousCall import AsynchronousCall
from ..Utils.tools import Tool
from openai import OpenAI

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


def generat_sql_prompt(query, table_data,table_info):
    today = datetime.now().date()
    prompt = f"""
                你是一名Dameng DB专家，现在需要阅读并理解下面的【数据库schema】描述，以及可能用到的【参考信息】，并运用Dameng DB知识生成sql语句回答【用户问题】。
                注意：1、用户问题可能涉及简称，因此在查询时多使用LIKE语法，生成的SQL需严格符合达梦数据库语法规范。

                【用户问题】
                {query}

                【数据库schema】
                    {table_info}
                
                【SQL语句必须包含的字段信息】
                    {table_data['needField']}

                【参考信息】
                1. 当前时间：{today}
                2. 生成的SQL不应该包含时间计算公式，涉及时间的问题，需基于给出的当前时间手动推算出具体时间值，并严格符合字段的格式需求：
                - 时间推算规则：根据用户问题中的时间描述（如"近7天""本月""上一年"），以当前时间为基准计算出具体的时间范围/时间点，而非使用函数（如DATEADD、NOW()）；
                3.当用户需要的只是信息时，则返回符合条件的表的所有信息
    """

    return prompt

class SQLPlus():
    def __init__(self):
        self.api_embed = API_Embedding()
        self.tools_manager = Tool()  # 假设这是你的工具管理类
        self.prompt_utils = Prompt_Templete()
        self.process_utils = ProcessUtils()
        self.AsynchronousCall = AsynchronousCall()
        self.sqlmanager = MySQLManager()
        # 加载固定写死的表文件
        self.table_plus = read_jsonl_file(os.getenv("Table_plus_path"))
        self.Sql_client = OpenAI(
            base_url=os.getenv("TextToSQL_base_url"),
            api_key=os.getenv("TextToSQL_api_key"),
        )

    # 本函数供需要调用text——sql模型的接口函数
    def generate_sql(self, query):
            # 1、获取表的信息
            table_data = [data for data in self.table_plus if data['question'] == query][0]
            # 2、根据表信息，生成提问的提示词
            table_info=self.tools_manager.get_table_info([table_data['table']])[0]
            prompt = generat_sql_prompt(query, table_data,table_info)
            # 3、根据提示词生成sql
            sql = self.Sql_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=os.getenv("TextToSQL_model"),
            ).choices[0].message.content
            #  4、根据sql查询结果
            print("生成sql",sql)
            sql_res = self.sqlmanager.request_api_sql(sql)
            return sql_res

if __name__ == "__main__":
    client=OpenAI(
        base_url=os.getenv("OpenAI_BASE_URL"),
        api_key=os.getenv("OpenAI_API_KEY"),
    )
    agent=SQLPlus()
    while True:
        query=input("用户提问： > ")
        res=agent.generate_sql(query)
        prompt=f"用户提问：‘{query}’.回复结果中，必须详细介绍各字段详细。现在请基于以下数据库查询结果回答用户问题：‘{res}’"
        print(client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content)