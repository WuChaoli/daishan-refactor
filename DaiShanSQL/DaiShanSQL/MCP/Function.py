from datetime import datetime
import json
import os
import sys
from ..SQL.sql_utils import MySQLManager
from .tools import Tool

class Function:

    def __init__(self):
        self.sql_manager = MySQLManager()
        self.tools = Tool()
        self.now_time = datetime.now()

    def get_table_info(self,tables):
        matched_tables = []
        for target_name in tables:
            # 遍历解析后的表信息，匹配表名
            for table_info in self.tools.tableInfoMap:
                if table_info["表名"] == target_name:
                    matched_tables.append(table_info)
                    break  # 完全匹配后跳出内层循环，避免重复匹配（表名唯一）
        return matched_tables

    def get_all_tool(self,tables,sql_info):
        table_info = []
        for tableName in tables:
            table_info.append(self.tools.aviable_table[tableName])
        all_tool = [
            {
                "type": "function",
                "function": {
                    "name": "information_sql",
                    "description": "用户询问任何问题时，都需要调用该工具，以查询数据库信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "list",
                                "description": f"""请访问参数table_information中提供的列表信息，生成一个SQL SELECT 查询语句列表。注意，当涉及到查询所有信息时，需要限制最多查询20条信息，用limit限制;sql查询的列名严格按照当前函数提供的表单信息查询对应的列，不得虚假造列名;对于条件查询语句，其他一般情况下都使用like拼接查询条件以进行模糊查询。
                                          """
                            },
                            "query_type": {
                                "type": "string",
                                "description": f"""
                                              用户的操作类型（增删改查）,返回结果为['insert','delete','update','select']
                                              """,
                                'enum': ['insert', 'delete', 'update', 'select']
                            },
                            "table_information": {
                                "type": "string",
                                "description": f"""用于给query提供详细表单信息的内容。
                                                ## 可用的表名是：{tables},
                                                ## 可用的列表信息是:{table_info}
                                                ##  可参考的用户问题及sql是:{sql_info}
                                                
        """,
                            },
                        },
                        "required": ["query", "query_type"]
                    }
                }
            }
        ]
        return all_tool

    def sql_query(self,query,query_type,**kwargs):
        if query_type == "select":
            # res=self.sql_manager.select_by_query(query)
            result = []
            for sql in query:
                print(f"当前sql={sql}")
                res = self.sql_manager.request_api_sql(sql=sql)
                result.append(res)

            return result
        else:
            return ["用户请求失败，不得进行数据库信息修改"]
        
if __name__ == "__main__":
    function = Function()
    tables = ["v_ai_ipark_sys_person","v_ai_ipark_hm_craft"]
    res = function.get_table_info(tables)
    print(res)