# 猜你想问功能 - 测试用例设计

## 测试策略

### 测试层级
1. **单元测试**: 测试各个处理函数的逻辑
2. **集成测试**: 测试与IntentService的集成
3. **接口测试**: 测试完整的API接口

### 测试覆盖目标
- 单元测试覆盖率: ≥90%
- 集成测试覆盖率: ≥80%
- 整体覆盖率: ≥80%

## 单元测试用例

### 测试模块: guess_questions_service.py

#### 测试类: TestProcessType1

##### 测试用例1.1: 正常返回固定问题
**测试函数**: `test_process_type1_returns_fixed_questions`
**输入**:
```python
intent_result = {
    "type": 1,
    "query": "附近有哪些应急避难所？",
    "results": [],
    "similarity": 0.85,
    "database": "岱山-指令集"
}
```
**预期输出**:
```python
[
    {"guess_your_question": "如何查询应急资源？"},
    {"guess_your_question": "如何调度救援队伍？"},
    {"guess_your_question": "如何查看事故信息？"}
]
```
**验证点**:
- 返回列表长度为3
- 每个元素包含guess_your_question字段
- 问题内容符合预设模板

##### 测试用例1.2: 固定问题内容验证
**测试函数**: `test_process_type1_question_content`
**输入**: 同上
**预期输出**: 固定问题内容清晰易懂，符合业务场景
**验证点**:
- 问题1: "如何查询应急资源？"
- 问题2: "如何调度救援队伍？"
- 问题3: "如何查看事故信息？"

#### 测试类: TestProcessType2

##### 测试用例2.1: 正常提取第2-4个结果
**测试函数**: `test_process_type2_extracts_2_to_4`
**输入**:
```python
intent_result = {
    "type": 2,
    "query": "岱山有多少家化工企业？",
    "results": [
        {"question": "问题1", "similarity": 0.95},
        {"question": "问题2", "similarity": 0.90},
        {"question": "问题3", "similarity": 0.85},
        {"question": "问题4", "similarity": 0.80},
        {"question": "问题5", "similarity": 0.75}
    ],
    "similarity": 0.95,
    "database": "岱山-数据库问题"
}
```
**预期输出**:
```python
[
    {"guess_your_question": "问题2"},
    {"guess_your_question": "问题3"},
    {"guess_your_question": "问题4"}
]
```
**验证点**:
- 返回列表长度为3
- 提取的是索引1、2、3的元素（第2-4个）
- 正确提取question字段

##### 测试用例2.2: 结果只有3个元素
**测试函数**: `test_process_type2_with_3_results`
**输入**:
```python
intent_result = {
    "type": 2,
    "results": [
        {"question": "问题1", "similarity": 0.95},
        {"question": "问题2", "similarity": 0.90},
        {"question": "问题3", "similarity": 0.85}
    ]
}
```
**预期输出**:
```python
[
    {"guess_your_question": "问题2"},
    {"guess_your_question": "问题3"}
]
```
**验证点**:
- 返回列表长度为2
- 提取索引1、2的元素

##### 测试用例2.3: 结果只有2个元素
**测试函数**: `test_process_type2_with_2_results`
**输入**:
```python
intent_result = {
    "type": 2,
    "results": [
        {"question": "问题1", "similarity": 0.95},
        {"question": "问题2", "similarity": 0.90}
    ]
}
```
**预期输出**:
```python
[
    {"guess_your_question": "问题2"}
]
```
**验证点**:
- 返回列表长度为1
- 提取索引1的元素

##### 测试用例2.4: 结果只有1个元素
**测试函数**: `test_process_type2_with_1_result`
**输入**:
```python
intent_result = {
    "type": 2,
    "results": [
        {"question": "问题1", "similarity": 0.95}
    ]
}
```
**预期输出**:
```python
[]
```
**验证点**:
- 返回空列表
- 不会抛出异常

##### 测试用例2.5: 结果为空列表
**测试函数**: `test_process_type2_with_empty_results`
**输入**:
```python
intent_result = {
    "type": 2,
    "results": []
}
```
**预期输出**:
```python
[]
```
**验证点**:
- 返回空列表
- 不会抛出异常

#### 测试类: TestProcessOtherTypes

##### 测试用例3.1: type=0返回空列表
**测试函数**: `test_process_type0_returns_empty`
**输入**:
```python
intent_result = {
    "type": 0,
    "query": "测试问题",
    "results": [],
    "similarity": 0.0,
    "database": ""
}
```
**预期输出**:
```python
[]
```
**验证点**:
- 返回空列表
- 不会抛出异常

##### 测试用例3.2: 未知type返回空列表
**测试函数**: `test_process_unknown_type_returns_empty`
**输入**:
```python
intent_result = {
    "type": 99,
    "query": "测试问题",
    "results": [],
    "similarity": 0.0,
    "database": ""
}
```
**预期输出**:
```python
[]
```
**验证点**:
- 返回空列表
- 不会抛出异常

## 集成测试用例

### 测试模块: test_guess_questions_integration.py

#### 测试类: TestGuessQuestionsAPI

##### 测试用例4.1: 类别1完整流程
**测试函数**: `test_guess_questions_type1_integration`
**前置条件**: Mock IntentService.process_query() 返回type=1的结果
**输入**:
```python
request = {
    "question": "附近有哪些应急避难所？"
}
```
**预期输出**:
```python
{
    "code": 0,
    "message": "成功",
    "data": [
        {"guess_your_question": "如何查询应急资源？"},
        {"guess_your_question": "如何调度救援队伍？"},
        {"guess_your_question": "如何查看事故信息？"}
    ]
}
```
**验证点**:
- HTTP状态码200
- 响应格式正确
- data包含3个问题

##### 测试用例4.2: 类别2完整流程
**测试函数**: `test_guess_questions_type2_integration`
**前置条件**: Mock IntentService.process_query() 返回type=2的结果
**输入**:
```python
request = {
    "question": "岱山有多少家化工企业？"
}
```
**预期输出**:
```python
{
    "code": 0,
    "message": "成功",
    "data": [
        {"guess_your_question": "岱山有多少家危化品企业？"},
        {"guess_your_question": "岱山化工园区的企业分布情况？"},
        {"guess_your_question": "岱山重大危险源有哪些？"}
    ]
}
```
**验证点**:
- HTTP状态码200
- 响应格式正确
- data包含提取的问题

##### 测试用例4.3: 空问题输入
**测试函数**: `test_guess_questions_empty_question`
**输入**:
```python
request = {
    "question": ""
}
```
**预期输出**:
```python
{
    "code": 1,
    "message": "问题不能为空",
    "data": []
}
```
**验证点**:
- HTTP状态码400或200（根据设计）
- 返回错误响应
- 错误信息清晰

##### 测试用例4.4: 问题过长
**测试函数**: `test_guess_questions_long_question`
**输入**:
```python
request = {
    "question": "a" * 1001  # 超过1000字符
}
```
**预期输出**:
```python
{
    "code": 1,
    "message": "问题长度不能超过1000字符",
    "data": []
}
```
**验证点**:
- 返回错误响应
- 错误信息清晰

##### 测试用例4.5: IntentService调用失败
**测试函数**: `test_guess_questions_intent_service_error`
**前置条件**: Mock IntentService.process_query() 抛出异常
**输入**:
```python
request = {
    "question": "测试问题"
}
```
**预期输出**:
```python
{
    "code": 1,
    "message": "意图识别服务暂时不可用",
    "data": []
}
```
**验证点**:
- 捕获异常
- 返回友好的错误信息
- 记录错误日志

##### 测试用例4.6: 数据格式错误
**测试函数**: `test_guess_questions_invalid_data_format`
**前置条件**: Mock IntentService.process_query() 返回格式错误的数据
**输入**:
```python
request = {
    "question": "测试问题"
}
```
**预期输出**:
```python
{
    "code": 1,
    "message": "数据格式错误",
    "data": []
}
```
**验证点**:
- 捕获数据格式异常
- 返回友好的错误信息

## 接口测试用例

### 测试工具: Postman / pytest

#### 测试用例5.1: 接口可访问性
**请求**:
```
POST /api/guess-questions
Content-Type: application/json

{
    "question": "测试问题"
}
```
**预期**:
- HTTP状态码200
- 返回JSON格式响应

#### 测试用例5.2: 响应格式验证
**请求**: 同上
**预期**:
- 响应包含code、message、data字段
- code为整数
- message为字符串
- data为列表

#### 测试用例5.3: 日志记录验证
**操作**: 调用接口后查看日志文件
**预期**:
- 记录请求参数
- 记录意图识别结果
- 记录响应数据
- 日志格式符合规范

#### 测试用例5.4: 并发请求测试
**操作**: 同时发送10个请求
**预期**:
- 所有请求都能正常响应
- 响应时间<2秒
- 无数据混乱

## 性能测试用例

### 测试用例6.1: 响应时间测试
**测试方法**: 使用pytest-benchmark或locust
**测试场景**:
- 类别1请求100次
- 类别2请求100次
**预期**:
- 平均响应时间<2秒
- 95%请求响应时间<2.5秒

### 测试用例6.2: 并发性能测试
**测试方法**: 使用locust
**测试场景**:
- 10个并发用户
- 持续1分钟
**预期**:
- 无请求失败
- 平均响应时间<2秒
- 系统稳定运行

## 测试数据

### Mock数据: IntentService响应

#### Type 1 响应
```python
{
    "type": 1,
    "query": "附近有哪些应急避难所？",
    "results": [],
    "similarity": 0.85,
    "database": "岱山-指令集"
}
```

#### Type 2 响应（5个结果）
```python
{
    "type": 2,
    "query": "岱山有多少家化工企业？",
    "results": [
        {"question": "岱山化工企业总数是多少？", "similarity": 0.95},
        {"question": "岱山有多少家危化品企业？", "similarity": 0.90},
        {"question": "岱山化工园区的企业分布情况？", "similarity": 0.85},
        {"question": "岱山重大危险源有哪些？", "similarity": 0.80},
        {"question": "岱山化工企业的安全管理情况？", "similarity": 0.75}
    ],
    "similarity": 0.95,
    "database": "岱山-数据库问题"
}
```

#### Type 2 响应（2个结果）
```python
{
    "type": 2,
    "query": "测试问题",
    "results": [
        {"question": "问题1", "similarity": 0.90},
        {"question": "问题2", "similarity": 0.85}
    ],
    "similarity": 0.90,
    "database": "岱山-数据库问题"
}
```

#### Type 0 响应
```python
{
    "type": 0,
    "query": "测试问题",
    "results": [],
    "similarity": 0.0,
    "database": ""
}
```

## 测试执行计划

### 第一轮：单元测试
1. 测试process_type1函数
2. 测试process_type2函数
3. 测试process_other_types函数
4. 确保所有单元测试通过

### 第二轮：集成测试
1. 测试API接口与IntentService集成
2. 测试错误处理
3. 测试输入验证
4. 确保所有集成测试通过

### 第三轮：接口测试
1. 使用Postman测试接口
2. 验证响应格式
3. 验证日志记录
4. 验证并发处理

### 第四轮：性能测试
1. 测试响应时间
2. 测试并发性能
3. 生成性能报告

## 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| guess_questions_service.py | ≥90% |
| chat_routes.py (新增部分) | ≥85% |
| 整体 | ≥80% |

## 测试工具

- **pytest**: 单元测试和集成测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 测试覆盖率统计
- **pytest-mock**: Mock支持
- **httpx**: HTTP客户端测试
- **Postman**: 接口手动测试

## 测试环境

- Python 3.11+
- FastAPI测试客户端
- Mock IntentService
- 测试数据库（如需要）

---
**创建时间**: 2026-02-09
**创建人**: 鲁班（TDD开发工程师）
**版本**: 1.0
