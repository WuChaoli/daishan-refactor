
from .Agent.SQLAgent_toSql import SQLAgent
import os
from .SQL.sql_fixed import SQLFixed
class Server:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sentence_path = os.path.join(current_dir, "intent", "data", "岱山生成问题与SQL.jsonl")
        self.agent = SQLAgent(sentence_origin_path=sentence_path)
        self.sqlFixed = SQLFixed()
        print(sentence_path)

    def get_sql_result(self,query,history,questions):
        sql_result=self.agent.chat(prompt=query,conversation=history,questions=questions)
        return sql_result

server = Server()

if __name__=="__main__":
    # server=Server()
    print(server.sqlFixed.sql_ChemicalCompanyInfo())
    print(server.sqlFixed.sql_companyInfo())
    print(server.sqlFixed.sql_SecuritySituation())
    # while True:
    #     conversations = []
    #     prompt = input("\n\n用户提示词:  ")
    #     res = server.get_sql_result(prompt, conversations,
    #                      ["园区人员和企业人员各有多少人？","ABC公司的员工都在哪个园区工作？"])
    #     print(res)