
from .SQL.SQLAgent_toSql import SQLAgent
from .SQL.sql_fixed import SQLFixed
from .SQL.sql_utils import MySQLManager

import os
class Server:
    def __init__(self):
        self.agent = SQLAgent()
        self.sqlFixed = SQLFixed()
        self.mysqlQuery = MySQLManager()

    def get_sql_result(self,query,history,questions):
        return self.agent.chat(prompt=query,conversation=history,questions=questions)
    def QueryBySQL(self,sql):
        return(self.mysqlQuery.request_api_sql(sql))
    def QueryByTable(self,query,tables):
        '''
        :param query(用户问题): 字符串
        :param tables(用户指定表): 列表
        '''
        tables = [item.lower() for item in tables]
        return self.agent.QuerySpecificTable(query,tables)
if __name__=="__main__":
    server=Server()
    print(server.QueryBySQL())
    #介绍企业基本信息
    # print(server.sqlFixed.sql_companyInfo())
    # #介绍化工企业
    # print(server.sqlFixed.sql_ChemicalCompanyInfo())
    # #介绍安全态势
    # print(server.sqlFixed.sql_SecuritySituation())
    # # while True:
    # #     conversations = []
    # #     prompt = input("\n\n用户提示词:  ")
    # #     res = server.get_sql_result(prompt, conversations,
    # #                      ["园区人员和企业人员各有多少人？","ABC公司的员工都在哪个园区工作？"])
    # #     print(res)