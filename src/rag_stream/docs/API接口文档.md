# RAG流式回复API 接口文档

## 📋 接口概览

本文档详细描述了RAG流式回复API的所有接口，包括请求参数、响应格式、使用示例和错误处理。

**基础信息:**
- 服务地址: `http://localhost:11028`
- API文档: `http://localhost:11028/docs`
- 健康检查: `http://localhost:11028/health`
- 支持格式: JSON
- 认证方式: 无需认证

**接口分类:**
- 🔍 基础接口：健康检查、类别查询
- 💬 流式问答接口：法律法规、标准规范、应急知识、事故案例、MSDS、标准政策、通用问答
- 🏭 数字人接口：重大危险源预警、安全态势、双重预防、园区开停车、特殊作业、企业态势
- 🔄 会话管理接口：创建、查询、删除会话
- 🚨 应急调度接口：人员调度、资源调度
- 💡 推荐接口：猜你想问

---

## 🔍 基础接口

### 1. 健康检查

**接口地址:** `GET /health`

**功能描述:** 检查服务运行状态，返回服务健康信息和统计信息

**请求参数:** 无

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "active_sessions": 5,
  "active_users": 3
}
```

**响应字段说明:**
- `status`: 服务状态（healthy/unhealthy）
- `timestamp`: 检查时间戳
- `active_sessions`: 当前活跃会话数
- `active_users`: 当前活跃用户数

---

### 2. 获取支持的类别

**接口地址:** `GET /api/categories`

**功能描述:** 获取系统支持的所有问答类别和对应的chat_id

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "categories": [
      "法律法规",
      "标准规范", 
      "应急知识",
      "事故案例",
      "MSDS",
      "标准政策",
      "通用"
    ],
    "chat_ids": {
      "法律法规": "1b0abaca824a11f0bc900242ac140003",
      "标准规范": "f86efa8e824a11f09d290242ac140003",
      "应急知识": "530474c4824b11f09cc60242ac140003",
      "事故案例": "82e5a0e6824b11f08a5b0242ac140003",
      "MSDS": "a7eca95c824b11f081ea0242ac140003",
      "标准政策": "e0c339f8824b11f0863a0242ac140003",
      "通用": "29b17242824c11f08ae80242ac140003"
    }
  }
}
```

---

## 💬 流式问答接口

### 3. 法律法规问答

**接口地址:** `POST /api/laws`

**功能描述:** 针对安全生产法律法规相关问题进行流式问答

**请求参数:**
```json
{
  "question": "string",        // 必填，问题内容
  "user_id": "string",        // 必填，用户ID（用于会话绑定）
  "session_id": "string"      // 可选，会话ID（通常不需要提供）
}
```

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法规？",
    "user_id": "user001"
  }'
```

**响应格式:** Server-Sent Events (SSE)

**响应示例:**
```
data: {"code": 0, "data": {"sessionId": "abc123", "answer": "安全生产法规是指", "flag": 1, "wordId": 0}}

data: {"code": 0, "data": {"sessionId": "abc123", "answer": "国家制定的", "flag": 1, "wordId": 1}}

data: {"code": 0, "data": {"sessionId": "abc123", "answer": "关于安全生产的法律法规", "flag": 1, "wordId": 2}}

data: {"code": 0, "data": {"sessionId": "abc123", "answer": "", "flag": 0, "wordId": 3}}
```

---

### 4. 标准规范问答

**接口地址:** `POST /api/standards`

**功能描述:** 针对安全标准规范相关问题进行流式问答

**请求参数:** 同法律法规接口

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/standards" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "安全标准有哪些分类？",
    "user_id": "user001"
  }'
```

---

### 5. 应急知识问答

**接口地址:** `POST /api/emergency`

**功能描述:** 针对应急处理知识相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/emergency" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "发生火灾时应该怎么办？",
    "user_id": "user001"
  }'
```

---

### 6. 事故案例问答

**接口地址:** `POST /api/accidents`

**功能描述:** 针对安全事故案例分析相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/accidents" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "有哪些典型的安全事故案例？",
    "user_id": "user001"
  }'
```

---

### 7. MSDS问答

**接口地址:** `POST /api/msds`

**功能描述:** 针对化学品安全技术说明书相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/msds" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是MSDS？",
    "user_id": "user001"
  }'
```

---

### 8. 标准政策问答

**接口地址:** `POST /api/policies`

**功能描述:** 针对安全政策和标准相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "最新的安全政策是什么？",
    "user_id": "user001"
  }'
```

---

### 9. 通用问答

**接口地址:** `POST /api/general`

**功能描述:** 智能通用问答接口，使用意图识别自动路由到合适的知识库或数据源

**特性:**
- 自动识别问题意图
- 支持SQL查询结果增强
- 智能选择知识库

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/general" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何提高安全意识？",
    "user_id": "user001"
  }'
```

---

### 10. 重大危险源预警问答

**接口地址:** `POST /api/warn`

**功能描述:** 针对重大危险源预警相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/warn" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "当前有哪些重大危险源预警？",
    "user_id": "user001"
  }'
```

---

### 11. 当日安全态势问答

**接口地址:** `POST /api/safesituation`

**功能描述:** 针对当日安全态势相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/safesituation" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "今天的安全态势如何？",
    "user_id": "user001"
  }'
```

---

### 12. 双重预防机制效果问答

**接口地址:** `POST /api/prevent`

**功能描述:** 针对双重预防机制效果相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/prevent" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "双重预防机制的效果如何？",
    "user_id": "user001"
  }'
```

---

### 13. 园区开停车问答

**接口地址:** `POST /api/park`

**功能描述:** 针对园区开停车相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/park" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "园区今天有哪些开停车情况？",
    "user_id": "user001"
  }'
```

---

### 14. 园区特殊作业态势问答

**接口地址:** `POST /api/special`

**功能描述:** 针对园区特殊作业态势相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/special" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "园区有哪些特殊作业正在进行？",
    "user_id": "user001"
  }'
```

---

### 15. 园区企业态势问答

**接口地址:** `POST /api/firmsituation`

**功能描述:** 针对园区企业态势相关问题进行流式问答

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/firmsituation" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "园区企业的整体态势如何？",
    "user_id": "user001"
  }'
```

---

### 16. 通用聊天接口

**接口地址:** `POST /api/chat/{category}`

**功能描述:** 通用的聊天接口，通过路径参数指定类别

**请求参数:**
- `category`: 路径参数，类别名称（法律法规、标准规范等）
- `question`: 问题内容
- `user_id`: 用户ID
- `session_id`: 可选，会话ID

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/chat/法律法规" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "安全生产法的主要内容是什么？",
    "user_id": "user001"
  }'
```

---

## 🔄 会话管理接口

### 17. 创建会话

**接口地址:** `POST /api/sessions/{category}`

**功能描述:** 为指定类别创建会话

**请求参数:**
```json
{
  "name": "string",        // 必填，会话名称
  "user_id": "string"     // 可选，用户ID
}
```

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/sessions/法律法规" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "安全法规咨询",
    "user_id": "user001"
  }'
```

**响应示例:**
```json
{
  "code": 0,
  "message": "会话创建成功",
  "data": {
    "session_id": "abc123",
    "category": "法律法规",
    "name": "安全法规咨询",
    "user_id": "user001"
  }
}
```

---

### 18. 暂停/删除会话

**接口地址:** `POST /api/stop`

**功能描述:** 暂停或删除指定的会话，支持按session_id或user_id删除

**请求参数:**
```json
{
  "session_id": "string",  // 可选，会话ID（删除单个会话）
  "user_id": "string"      // 可选，用户ID（删除用户所有会话）
}
```

**请求示例:**
```bash
# 删除单个会话
curl -X POST "http://localhost:11028/api/stop" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123"
  }'

# 删除用户所有会话
curl -X POST "http://localhost:11028/api/stop" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001"
  }'
```

**响应示例:**
```
暂停成功
```

---

### 19. 获取用户会话信息

**接口地址:** `GET /api/user/{user_id}/sessions`

**功能描述:** 获取指定用户在所有类别的会话信息

**请求参数:**
- `user_id`: 路径参数，用户ID

**请求示例:**
```bash
curl -X GET "http://localhost:11028/api/user/user001/sessions"
```

**响应示例:**
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "user_id": "user001",
    "sessions": {
      "法律法规": {
        "session_id": "abc123",
        "name": "安全法规咨询",
        "create_time": "2024-01-15T10:30:00.123456",
        "last_activity": "2024-01-15T10:35:00.123456",
        "message_count": 3
      },
      "标准规范": {
        "session_id": "def456",
        "name": "标准规范咨询",
        "create_time": "2024-01-15T10:40:00.123456",
        "last_activity": "2024-01-15T10:42:00.123456",
        "message_count": 1
      }
    }
  }
}
```

---

### 20. 获取会话信息

**接口地址:** `GET /api/sessions/{session_id}`

**功能描述:** 获取指定会话的详细信息

**请求参数:**
- `session_id`: 路径参数，会话ID

**请求示例:**
```bash
curl -X GET "http://localhost:11028/api/sessions/abc123"
```

**响应示例:**
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "id": "abc123",
    "chat_id": "1b0abaca824a11f0bc900242ac140003",
    "name": "安全法规咨询",
    "user_id": "user001",
    "category": "法律法规",
    "create_time": "2024-01-15T10:30:00.123456",
    "last_activity": "2024-01-15T10:35:00.123456",
    "message_count": 3,
    "rag_session_id": "rag_session_123"
  }
}
```

---

### 21. 获取所有会话

**接口地址:** `GET /api/sessions`

**功能描述:** 获取系统中所有活跃会话的信息

**请求参数:** 无

**请求示例:**
```bash
curl -X GET "http://localhost:11028/api/sessions"
```

**响应示例:**
```json
{
  "code": 0,
  "message": "获取成功",
  "data": [
    {
      "id": "abc123",
      "chat_id": "1b0abaca824a11f0bc900242ac140003",
      "name": "安全法规咨询",
      "user_id": "user001",
      "category": "法律法规",
      "create_time": "2024-01-15T10:30:00.123456",
      "last_activity": "2024-01-15T10:35:00.123456",
      "message_count": 3
    }
  ]
}
```

---

### 22. 删除会话

**接口地址:** `DELETE /api/sessions/{session_id}`

**功能描述:** 删除指定的会话

**请求参数:**
- `session_id`: 路径参数，会话ID

**请求示例:**
```bash
curl -X DELETE "http://localhost:11028/api/sessions/abc123"
```

**响应示例:**
```json
{
  "code": 0,
  "message": "会话删除成功",
  "data": null
}
```

---

## 🚨 应急调度接口

### 23. 人员调度

**接口地址:** `POST /ipark-ae/personnel-dispatch`

**功能描述:** 根据事故信息和语音文本，智能调度应急人员

**请求参数:**
```json
{
  "accidentId": "string",  // 必填，事故ID
  "voiceText": "string"    // 必填，语音识别文本
}
```

**请求示例:**
```bash
curl -X POST "http://localhost:11028/ipark-ae/personnel-dispatch" \
  -H "Content-Type: application/json" \
  -d '{
    "accidentId": "ACC20240115001",
    "voiceText": "需要调度消防人员和医疗人员到现场"
  }'
```

**响应示例:**
```json
[ 
  {"id": "1111"},
  {"id": "2222"}
]
```

**响应说明:**
- 返回 `List[Dict[str, str]]`，每个元素结构为 `{"id": "人员ID"}`
- 未匹配到人员或处理异常时返回 `[]`

---

### 24. 资源调度

**接口地址:** `POST /ipark-ae/source-dispatch`

**功能描述:** 根据事故信息、资源类型和语音文本，智能调度应急资源

**请求参数:**
```json
{
  "accidentId": "string",   // 必填，事故ID
  "sourceType": "string",   // 必填，资源类型（见下方枚举）
  "voiceText": "string"     // 可选，语音识别文本
}
```

**sourceType 可选值（固定枚举）:**
- `emergencySupplies`
- `rescueTeam`
- `emergencyExpert`
- `fireFightingFacilities`
- `shelter`
- `medicalInstitution`
- `rescueOrganization`
- `protectionTarget`

**请求示例:**
```bash
curl -X POST "http://localhost:11028/ipark-ae/source-dispatch" \
  -H "Content-Type: application/json" \
  -d '{
    "accidentId": "ACC20240115001",
    "sourceType": "fireFightingFacilities",
    "voiceText": "需要调度消防车和灭火器到现场"
  }'
```

**响应示例:**
```json
[
  {
    "id": "1111"
  },
  {
    "id": "2222"
  }
]
```

**响应说明:**
- 返回 `List[Dict[str, str]]`，典型结构为 `[{"id": "资源ID"}]`
- 未匹配到资源或处理异常时返回 `[]`

---

### 25. 猜你想问

**接口地址:** `POST /api/guess-questions`

**功能描述:** 根据用户当前问题进行意图识别，返回推荐问题列表

**请求参数:**
```json
{
  "question": "string"  // 必填，用户问题（1~1000字符）
}
```

**请求示例:**
```bash
curl -X POST "http://localhost:11028/api/guess-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "我想了解园区应急物资有哪些"
  }'
```

**响应示例:**
```json
[
  {"question": "园区有哪些应急物资储备？"},
  {"question": "应急物资的调用流程是什么？"},
  {"question": "最近的应急仓库在哪里？"}
]
```

**响应说明:**
- 返回 `List[Dict[str, str]]`，每个元素结构为 `{"question": "推荐问题"}`
- 无推荐结果或处理异常时返回 `[]`

---

## 📊 响应格式说明

### 流式响应格式

所有问答接口都采用Server-Sent Events (SSE)格式返回流式数据：

```
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "部分回答", "flag": 1, "wordId": 0}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "更多回答", "flag": 1, "wordId": 1}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "", "flag": 0, "wordId": 2}}
```

**字段说明:**
- `code`: 响应状态码（0=成功，1=错误）
- `sessionId`: 会话ID
- `answer`: 回答内容（增量）
- `flag`: 标志位（1=正常数据，0=结束标志）
- `wordId`: 词汇ID，用于排序

### 标准响应格式

非流式接口返回标准JSON格式：

```json
{
  "code": 0,           // 状态码（0=成功，非0=错误）
  "message": "string", // 响应消息
  "data": {}           // 响应数据
}
```

---

## ⚠️ 错误处理

### 错误响应格式

```json
{
  "code": 102,
  "message": "错误描述信息",
  "data": null
}
```

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式和必填字段 |
| 404 | 资源不存在 | 检查会话ID或类别是否正确 |
| 500 | 服务器内部错误 | 检查服务状态和日志 |

---

## 🧪 完整使用示例

### 示例1: 连续对话（法律法规）

```bash
# 第一步：创建会话并提问
curl -X POST "http://localhost:11028/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法规？",
    "user_id": "user001"
  }'

# 第二步：继续提问（使用同一会话）
curl -X POST "http://localhost:11028/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这些法规有哪些具体要求？",
    "user_id": "user001"
  }'

# 第三步：再次提问（继续同一会话）
curl -X POST "http://localhost:11028/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "违反这些法规会有什么后果？",
    "user_id": "user001"
  }'
```

### 示例2: 多类别对话

```bash
# 在法律法规类别提问
curl -X POST "http://localhost:11028/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "安全生产法的主要内容是什么？",
    "user_id": "user002"
  }'

# 在标准规范类别提问（独立会话）
curl -X POST "http://localhost:11028/api/standards" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "安全标准有哪些分类？",
    "user_id": "user002"
  }'

# 在应急知识类别提问（独立会话）
curl -X POST "http://localhost:11028/api/emergency" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "火灾应急处理流程是什么？",
    "user_id": "user002"
  }'
```

### 示例3: 会话管理

```bash
# 查看用户所有会话
curl -X GET "http://localhost:11028/api/user/user001/sessions"

# 查看特定会话信息
curl -X GET "http://localhost:11028/api/sessions/abc123"

# 删除会话
curl -X DELETE "http://localhost:11028/api/sessions/abc123"
```

---

## 🔧 配置说明

### 会话管理配置

```python
# 会话过期时间（小时）
SESSION_EXPIRE_HOURS: int = 1

# 每个用户最大会话数
MAX_SESSIONS_PER_USER: int = 5
```

### 超时配置

```python
# 请求超时时间（秒）
REQUEST_TIMEOUT: int = 300

# 流式响应超时时间（秒）
STREAM_TIMEOUT: int = 300
```

---

## 📝 注意事项

1. **用户ID必填**: 所有问答接口都必须提供`user_id`以实现会话绑定
2. **会话自动管理**: 系统自动创建、复用和清理会话，无需手动管理
3. **流式响应**: 问答接口返回SSE格式的流式数据，需要特殊处理
4. **会话过期**: 会话默认1小时后自动过期，可通过配置调整
5. **错误处理**: 建议实现完善的错误处理机制
6. **并发支持**: 支持多用户、多类别并发使用

---

## 🚀 快速测试

使用提供的测试客户端进行完整测试：

```bash
python test_client.py
```

测试将演示所有核心功能，包括用户会话绑定、连续对话、多类别管理等。
