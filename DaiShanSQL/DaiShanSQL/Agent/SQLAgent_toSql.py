import traceback

from ..Utils.ProcessUtils import ProcessUtils
from ..MCP.Function import Function
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
from ..intent.api_intent import API_Embedding
from ..Utils.AsynchronousCall import AsynchronousCall

def find_most_frequent_table(data_list):
    # 提取所有待查询表
    tables = [item['待查询表'] for item in data_list]
    # 统计每个表的出现次数
    seen = set()
    final_table_list = []
    for table in tables:
        if table not in seen:
            final_table_list.append(table)
            seen.add(table)

    return final_table_list

def filter_table(table_list,tableName_list):
    res_table_list = []
    for table in table_list:
        table_name =table['待查询表']
        if table_name in tableName_list:
            continue
        else:
            res_table_list.append(table)
    return res_table_list

def replace_economic_zone(query):
    # 定义替换规则，先替换更具体的关键词，再替换通用关键词
    replace_rules = [
        ("岱山经开区", "岱山经济开发区"),
        ("经开区", "岱山经济开发区"),
        ("岱山经济开发区","岱山经济开发区")
    ]
    result = query
    for old_str, new_str in replace_rules:
        result = result.replace(old_str, new_str)
    
    return result

class SQLAgent:
    def __init__(self,sentence_origin_path):
        self.api_embed = API_Embedding(sentence_origin_path=sentence_origin_path)
        self.tools_manager = Function()  # 假设这是你的工具管理类
        self.prompt_utils=Prompt_Templete()
        self.process_utils=ProcessUtils()
        self.AsynchronousCall =AsynchronousCall()
        self.available_functions = {
            "information_sql":self.tools_manager.sql_query
        }
        self.sqlmanager = MySQLManager()


    #  普通聊天
    def chat(self,prompt,conversation=[],questions=[]):
            """
            处理用户的一轮对话，支持工具调用。
            """
            # 清理表，获取正确的表
            final_table_list=[]
            try:
                query=replace_economic_zone(prompt)
                tableData= self.api_embed.predict_table(questions[:5])
                table_list = find_most_frequent_table(tableData)
                final_table_list=self.process_utils.process_all(query,table_list)
                #根据表名，加载表的详细信息
                table_info=self.tools_manager.get_table_info(final_table_list)
                #获取修正后的问题及相关信息
                new_prompt_result = self.AsynchronousCall.ProcessQuerys(query,table_info)
                #获取基于修正后的问题生成的SQL
                new_sql = self.AsynchronousCall.ProcessSQL(query,new_prompt_result)

                sql_quer_result=[]
                for item in new_sql:
                    sql=item["result"]
                    sql_res=self.sqlmanager.request_api_sql(sql)['data']
                    sql_quer_result.append({"修正后问题":item["origin_user_query"],"数据库查询结果":sql_res,"sql语句":{sql},"针对的表":item["table"]['表名']})
                return sql_quer_result
            except Exception  as e:
                # 运行出错，返回空的结果
                print(f"{traceback.format_exc()}")
                return {
                    "数据库查询": "",
                    "数据库查询结果": "异常",
                    "筛选出的表":final_table_list
                }



if __name__ == '__main__':
    agent = SQLAgent()
    conversations = []
    questions = ["企业名称包含“制造”的公司有哪些AI报警记录？","能否按处理状态分类统计AI报警事件数量？","刘芳的工号是多少？","给我列出所有处理状态不是“已完成”的AI报警事件。"]
    rest=agent.chat(prompt=questions,conversation=conversations,questions=questions)
    print(rest)
