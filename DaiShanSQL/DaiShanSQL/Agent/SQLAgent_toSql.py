
import copy
import traceback

from ..Utils.ProcessUtils import ProcessUtils
from ..MCP.Function import Function
from ..Utils.OpenAI_utils import OpenAIUtils
from ..Utils.Prompt_Templete import Prompt_Templete
from ..SQL.sql_utils import MySQLManager
from ..intent.api_intent import API_Embedding

def generat_error_prompt(sql,error_msg,table_info,query):
    prompt=f"""
    你是一位达梦数据库（DM Database）SQL 语法专家。请根据用户提供的 SQL 语句及其对应的语法错误信息，精准定位并修正该 SQL 语句中的语法问题。
    
    输入格式：  
    - 用户的提问：{query}  
    - 根据提问可提供的表单信息：{table_info}  
    - 查询的SQL语句：{sql}  
    - 查询的SQL语法错误信息：{error_msg}  
    
    你的任务：  
    仅输出修正后的、符合达梦数据库语法规范的完整 SQL 语句，不要包含任何解释、注释、前缀或后缀。
    
    输出格式要求：  
    【仅输出修正后的 SQL 语句】
"""
    return prompt

def find_most_frequent_table(data_list):
    """
    从给定的数据列表中找出待查询表出现次数最多的表，并返回去重后的表列表

    Args:
        data_list: 包含查询信息的字典列表，每个字典需包含键 '待查询表'

    Returns:
        tuple: (出现次数最多的表名, 出现次数, 去重后的表名列表)
    """
    # 提取所有待查询表，跳过不包含 '待查询表' 键的项
    tables = [item['待查询表'] for item in data_list if '待查询表' in item]
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
        if '待查询表' not in table:
            continue
        table_name = table['待查询表']
        if table_name in tableName_list:
            continue
        else:
            res_table_list.append(table)
    return res_table_list

class SQLAgent:
    def __init__(self,sentence_origin_path):
        self.api_embed = API_Embedding(sentence_origin_path=sentence_origin_path)
        self.tools_manager = Function()  # 假设这是你的工具管理类
        self.utils = OpenAIUtils()
        self.prompt_utils=Prompt_Templete()
        self.process_utils=ProcessUtils()
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
                query=prompt
                tableData= self.api_embed.predict_table(questions)
                table_list = find_most_frequent_table(tableData)
                final_table_list=self.process_utils.process_all(query,table_list)
                # 根据表名，加载表的详细信息
                #获取键
                table_info=self.tools_manager.get_table_info(final_table_list) 
                #构建提示词
                prompt=self.prompt_utils.gengerate_sql(query, table_info)
                current_conversation = copy.deepcopy(conversation)
                
                self.utils.add_user_messages(prompt, current_conversation)
                sql=self.utils.request(current_conversation)
                sql_res=self.sqlmanager.request_api_sql(sql.content)

                # 报错标识是10001,获取报错提示
                if sql_res["code"]==100001 or sql_res["code"]=="100001":
                    error_conversation=[]
                    count=0
                    error_msg=sql_res["msg"]
                    while count < 3: #最大三次循环重试
                        err_prompt=generat_error_prompt(sql,error_msg,table_info,query)
                        error_conversation.append({"role":"user","content":err_prompt})
                        sql = self.utils.request(error_conversation,model='glm-4.7')
                        sql_res = self.sqlmanager.request_api_sql(sql.content)
                        error_conversation.append({"role":"assistant","content":sql.content})
                        #  当前语句正确，就结束循环
                        if not (sql_res["code"]==100001 or sql_res["code"]=="100001"):
                            break
                        count+=1

                return {
                    "数据库查询":sql.content,
                    "数据库查询结果":sql_res['data'],
                    "筛选出的表":final_table_list
                }
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
