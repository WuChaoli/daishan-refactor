# chat_general_service.py 架构设计文档

## 系统架构概览

```mermaid
graph TD
    A[用户提问] --> B[chat_general_service.handle_chat_general]
    B --> C[意图识别: IntentService]
    C --> D{识别类型}

    D -->|Type1| E[Type1处理器]
    D -->|Type2| F[Type2处理器]
    D -->|Type3| G[Type3处理器]

    E --> H[sqlFixed提取SQL]
    H --> I[DaiShanSQL执行查询]
    I --> J[专属RAGFLOW模板]
    J --> K[返回结果]

    G --> L[RAGFLOW查询"指令集-固定问题"]
    L --> M[提取answer(提示词)]
    M --> N[提取return_question(SQL选择器)]
    N --> O[DaiShanSQL.judgeQuery]
    O --> P[返回查询结果]
    P --> Q[通用RAGFLOW]
    Q --> R[返回结果]

    F --> S[server.get_sql_result]
    S --> T[自动生成SQL+执行]
    T --> U[通用RAGFLOW]
    U --> V[返回结果]

    D -->|错误/未知| W[通用RAGFLOW兜底]
    W --> X[返回结果]
```

---

## 二、三种意图类型详解

| 类型 | 名称 | 业务场景 | 提示词来源 | SQL来源 | RAGFLOW | 典型问题 |
|------|------|----------|------------|---------|---------|----------|
| **Type1** | 指令集(硬编码) | 固定查询,格式固定 | 固定模板 | sqlFixed提取 | **专属RAGFLOW** | 今日安全态势、园区开停车状态 |
| **Type3** | 半固定输出 | 固定SQL,动态提示词 | RAGFLOW answer | judgeQuery选择 | **通用RAGFLOW** | 园区介绍(需特定话术) |
| **Type2** | 自由问题 | 完全自由提问 | 固定模板 | 自动生成 | **通用RAGFLOW** | 园区有多少化工企业 |

---

## 三、核心处理流程

### **Type1: 硬编码指令集**

```python
# 输入: "查询今日安全态势"
# 1. 意图识别返回 Type1 + kb_name="当日安全态势"
# 2. 根据kb_name选择固定SQL
sql = server.sqlFixed.sql_SecuritySituation()  # 返回SQL字符串
# 3. DaiShanSQL执行查询
result = execute_sql(sql)  # 在DaiShanSQL内部完成
# 4. 注入专属RAGFLOW模板
prompt = f"{固定模板}\n\n{result}\n\n{用户问题}"
# 5. 调用当日安全态势专属RAGFLOW
response = ragflow.chat("当日安全态势", prompt)
```

**特点**: 每个Type1问题有**独立RAGFLOW知识库**,用于格式化输出

---

### **Type3: 半固定输出(猜你想问)**

```python
# 输入: "介绍一下园区"
# 1. 意图识别查询"岱山-指令集-固定问题"知识库
result_dict = {
    "type": 3,
    "answer": "请你介绍园区的园区名称、园区简称、园区地址，优先考虑数据库召回的内容",  # 专属提示词
    "results": [{
        "question": "Question: 查询园区基本信息的SQL语句\tAnswer: ...",
        "similarity": 0.95
    }]
}

# 2. 提取两个关键信息
answer_text = "请你介绍园区的园区名称..."  # 提示词模板
return_question = "查询园区基本信息的SQL语句"  # SQL选择器

# 3. 调用judgeQuery: SQL选择 + 执行 + 返回结果
# judgeQuery内部:
#   - 根据return_question匹配固定SQL
#   - 执行SQL查询达梦数据库
#   - 返回查询结果
judge_result = server.judgeQuery(
    "介绍一下园区",  # 原始问题
    "查询园区基本信息的SQL语句"  # SQL选择器
)
# judge_result = "查询结果: 岱山经开区,地址:XX..."

# 4. 构建prompt: 提示词 + 查询结果 + 用户问题
prompt = f"{answer_text}\n\n{judge_result}\n\n{用户问题}"
# = "请你介绍园区...<br>查询结果:岱山经开区...<br>介绍一下园区"

# 5. 调用通用RAGFLOW
response = ragflow.chat("通用", prompt)
```

**特点**:
- **动态提示词**: 从RAGFLOW知识库获取,每个问题不同
- **复合judgeQuery**: 集SQL选择、执行、结果返回于一体

---

### **Type2: 自由问题**

```python
# 输入: "园区有多少化工企业"
# 1. 意图识别返回 Type2
# 2. 从results提取问题列表 (用于SQL生成)
questions = _extract_questions_for_sql(text_input, result_items)
# questions = ["园区企业数量", "化工企业定义", ...]

# 3. 自动生成SQL + 执行
sql_result = server.get_sql_result(
    query="园区有多少化工企业",
    questions=questions
)
# get_sql_result内部:
#   - 调用LLM生成SQL
#   - 执行SQL查询
#   - 返回结果

# 4. 构建prompt: 固定提示词 + SQL结果 + 用户问题
prompt = f"{固定模板}\n\n{sql_result}\n\n{用户问题}"

# 5. 调用通用RAGFLOW
response = ragflow.chat("通用", prompt)
```

**特点**: SQL完全由LLM自动生成,不需要预先定义

---

## 四、DaiShanSQL服务核心函数

```python
class Server:
    # ============= 固定SQL提取 =============
    class sqlFixed:
        """Type1和Type3的固定SQL提取"""
        def sql_ChemicalCompanyInfo() -> str:
            """返回查询化工企业信息的SQL"""
            return "SELECT * FROM chemical_companies WHERE ..."

        def sql_SecuritySituation() -> str:
            """返回查询安全态势的SQL"""
            return "SELECT * FROM security_stats WHERE ..."

    # ============= 自动生成SQL =============
    def get_sql_result(
        self,
        query: str,
        history: list,
        questions: list[str]
    ) -> str:
        """
        Type2专用: 自动生成SQL并执行查询

        步骤:
        1. 基于query和questions调用LLM生成SQL
        2. 连接达梦数据库执行SQL
        3. 将结果格式化为字符串返回
        """
        pass

    # ============= SQL选择 + 执行 =============
    def judgeQuery(
        self,
        origin_question: str,
        sql_selector_question: str
    ) -> str:
        """
        Type3专用: SQL选择 + 执行 + 结果返回

        步骤:
        1. 根据sql_selector_question匹配对应的固定SQL
        2. 连接达梦数据库执行SQL
        3. 将结果格式化为字符串返回
        """
        pass
```

---

## 五、Prompt构建对比

| 类型 | Prompt结构 | 示例 |
|------|-----------|------|
| **Type1** | `固定RAG模板 + SQL结果 + 用户问题` | (由专属RAGFLOW内部处理) |
| **Type3** | `RAGFLOW answer(提示词) + judgeQuery结果 + 用户问题` | `请你介绍园区...<br>查询结果:岱山经开区...<br>介绍一下园区` |
| **Type2** | `固定提示词 + SQL结果 + 用户问题` | `你是一个分析师...<br>查询结果:共有123家...<br>园区有多少企业` |

---

## 六、降级与容错策略

```python
handle_chat_general()
    ↓
意图识别失败 → 通用RAGFLOW兜底
    ↓
[Type1/2/3处理]
    ↓
处理失败/返回None → 通用RAGFLOW兜底
    ↓
ImportError → 通用RAGFLOW兜底
    ↓
其他Exception → 通用RAGFLOW兜底
```

**兜底原则**: 任何环节失败都路由到通用RAGFLOW,保证系统可用性

---

## 七、关键函数索引

| 函数 | 文件位置 | 职责 | 调用场景 |
|------|----------|------|----------|
| `handle_chat_general` | chat_general_service.py:232 | 主入口 | 所有通用问答请求 |
| `_post_process_and_route_type1` | chat_general_service.py:125 | Type1处理 | 硬编码指令集 |
| `_post_process_and_route_type3` | chat_general_service.py:177 | Type3处理 | 半固定输出 |
| `_post_process_and_route_type2` | chat_general_service.py:160 | Type2处理 | 自由问题 |
| `server.judgeQuery` | DaiShanSQL.api_server | SQL选择+执行 | Type3专用 |
| `server.get_sql_result` | DaiShanSQL.api_server | SQL生成+执行 | Type2专用 |
| `intent_service.process_query` | intent_service.py:32 | 意图识别 | 所有请求 |

---

## 八、设计总结

**核心设计哲学**:
1. **分层处理**: 意图识别 → SQL处理 → RAGFLOW问答
2. **灵活性与确定性折中**:
   - Type1: 完全确定(固定SQL+固定RAG模板)
   - Type3: 半确定(固定SQL+动态提示词)
   - Type2: 完全灵活(自动SQL+固定提示词)
3. **知识库驱动**: Type3的提示词来自RAGFLOW,便于运营调整
4. **容错优先**: 多层兜底保障,任何失败都能响应用户

**无DIFY介入**: 当前设计完全基于DaiShanSQL+RAGFLOW,人员调度的DIFY是独立模块

---

## 九、术语表

| 术语 | 含义 |
|------|------|
| **DaiShanSQL** | SQL生成/提取与执行服务,连接达梦数据库 |
| **RAGFLOW** | 基于RAG的问答系统,用于最终答案生成 |
| **judgeQuery** | Type3专用函数,完成SQL选择+执行+结果返回 |
| **sqlFixed** | 固定SQL提取类,Type1/3用 |
| **通用RAGFLOW** | 兜底知识库,处理Type2/3和降级场景 |
| **专属RAGFLOW** | Type1专用知识库,每个问题独立配置 |
| **提示词模板** | 指导LLM如何基于数据回答问题的指令 |

---

## 十、维护与扩展指南

### 新增Type1问题
1. 在sqlFixed中添加SQL方法
2. 在RAGFLOW中创建专属知识库
3. 在意图映射中添加类型1配置

### 新增Type3问题
1. 在RAGFLOW"岱山-指令集-固定问题"中添加问答对
   - Question: SQL选择器问题
   - Answer: 提示词模板
2. 在sqlFixed中添加对应SQL方法
3. 在意图映射中添加类型3配置

### 调整Type2行为
1. 修改get_sql_result的prompt模板
2. 调整问题提取逻辑 `_extract_questions_for_sql`

---

**文档版本**: v1.0
**创建日期**: 2026-02-24
**最后更新**: 2026-02-24
**维护者**: AI Assistant
