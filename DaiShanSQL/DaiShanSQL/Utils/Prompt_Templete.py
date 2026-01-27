from datetime import datetime


class Prompt_Templete:
    def __init__(self):
        pass

    def check_sql(self,query,sql,table):
        prompt=f"""
                # Role
            你是一名资深的数据分析师和SQL优化专家。你的核心能力是理解业务意图、解析数据库mysql以及编写/修正高效、准确的SQL语句，你需要严格遵照提供的‘数据库表结构信息’修改和检查用户的sql语句，并使得sql语句能够满足用户的请求内容，而不是随意查询。
            
            # Context
            1. **用户请求（意图）**:'{query}'
            2. **待检查的SQL**: '{sql}'
            3. **数据库表结构信息**: '{table}'
            
            # Task
            请检查提供的SQL是否满足以下条件，并在必要时进行修改：
            1. **意图一致性**: SQL能否准确回答用户的请求？是否遗漏关键指标或筛选条件？
            2. **结构匹配性**: SQL中引用的表名、字段名是否存在于提供的表格中？如果字段不匹配，请严格根据提供的表格信息，修改对应字段名。
            3. **语法与逻辑修正**: 检查SQL是否有语法错误、逻辑漏洞（如笛卡尔积、聚合函数缺失等），并进行修正。
            
            # Constraints
            - 仅输出最终优化后的SQL语句，不要包含任何解释文字、Markdown代码块标记（如sql）或引号。
                如果原SQL完全正确且无优化空间，请直接原样输出。
                确保生成的SQL方言与上下文隐含的数据库类型（MySQL）兼容。
                
            Output:
                [仅返回修改检查后最终可以用于查询的sql语句]      
                """
        return prompt

    def gengerate_sql(self,query,table_info):
            today = datetime.now().date()
            prompt = f"""
            你是一名Dameng DB专家，现在需要阅读并理解下面的【数据库schema】描述，以及可能用到的【参考信息】，并运用Dameng DB知识生成sql语句回答【用户问题】。
            注意：每个问题只根据单表进行查询，不涉及多表，生成的SQL需严格符合达梦数据库语法规范。

            【用户问题】
            {query}

            【数据库schema】
            {table_info}

            【参考信息】
            1. 当前时间：{today}
            2. 生成的SQL不应该包含时间计算公式，涉及时间的问题，需基于给出的当前时间手动推算出具体时间值，并严格符合字段的格式需求：
            - 时间推算规则：根据用户问题中的时间描述（如"近7天""本月""上一年"），以当前时间为基准计算出具体的时间范围/时间点，而非使用函数（如DATEADD、NOW()）；
            3. SELECT子句中只保留字段本身，禁止使用AS关键字添加任何别名（包括中文别名、英文别名）
"""

            return prompt