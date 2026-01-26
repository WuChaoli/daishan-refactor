# API 合约文档 - RAG Stream 服务

## 文档信息

- **服务名称**: RAG Stream (rag_stream)
- **服务端口**: 11027
- **基础路径**: http://localhost:11027
- **API 版本**: 1.0.0
- **生成日期**: 2026-01-26

## 服务概述

RAG 流式回复服务，基于 RAGFlow 的流式问答服务，支持 13 个专业领域的智能问答，包括法律法规、标准规范、应急知识、事故案例、MSDS、标准政策、通用问答以及多个园区安全态势相关领域。

## 技术栈

- **框架**: FastAPI
- **Python 版本**: 3.12
- **主要依赖**:
  - aiohttp (异步 HTTP 客户端)
  - pydantic (数据验证)
  - uvicorn (ASGI 服务器)

## 核心功能

1. **多领域 RAG 问答**: 支持 13 个专业领域的知识问答
2. **流式响应**: 实时流式返回 AI 回答内容
3. **会话管理**: 自动创建和管理用户会话，支持会话过期清理
4. **智能路由**: 根据问题内容智能选择 RAGFlow 或 Dify 服务
5. **超时处理**: 15 秒超时保护机制

## API 端点列表

### 1. 健康检查

**端点**: `GET /health`

**描述**: 服务健康检查，返回服务状态和活跃会话统计

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T10:30:00",
  "active_sessions": 5,
  "active_users": 3
}
```

### 2. 获取支持的类别

**端点**: `GET /api/categories`

**描述**: 获取所有支持的问答类别和对应的 chat_id

**请求参数**: 无

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "categories": ["法律法规", "标准规范", "应急知识", "事故案例", "MSDS", "标准政策", "通用", "重大危险源预警", "当日安全态势", "双重预防机制效果", "园区开停车", "园区特殊作业态势", "园区企业态势"],
    "chat_ids": {
      "法律法规": "1b0abaca824a11f0bc900242ac140003",
      "标准规范": "f86efa8e824a11f09d290242ac140003",
      "应急知识": "530474c4824b11f09cc60242ac140003",
      "事故案例": "82e5a0e6824b11f08a5b0242ac140003",
      "MSDS": "a7eca95c824b11f081ea0242ac140003",
      "标准政策": "e0c339f8824b11f0863a0242ac140003",
      "通用": "29b17242824c11f08ae80242ac140003",
      "重大危险源预警": "3b4461ceafdb11f089700242ac140006",
      "当日安全态势": "29e0c8b4afdb11f0969f0242ac140006",
      "双重预防机制效果": "00b3d2f6afdb11f0b8570242ac140006",
      "园区开停车": "de9e7c48afda11f086900242ac140006",
      "园区特殊作业态势": "ae8d795aafda11f082c20242ac140006",
      "园区企业态势": "9a337ce8afda11f099390242ac140006"
    }
  }
}
```

### 3. 通用聊天接口（按类别）

**端点**: `POST /api/chat/{category}`

**描述**: 根据指定类别进行 RAG 问答，返回流式响应

**路径参数**:
- `category` (string, required): 问答类别，必须是支持的类别之一

**请求体**:
```json
{
  "question": "什么是安全生产法？",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**请求模型字段**:
- `question` (string, required): 用户问题
- `session_id` (string, optional): 会话 ID，如果不提供则自动创建
- `user_id` (string, optional): 用户 ID，用于会话管理

**响应类型**: `text/event-stream` (Server-Sent Events)

**响应格式**:
```
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "增量文本", "flag": 1, "wordId": 0, "end": 0}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "增量文本", "flag": 1, "wordId": 1, "end": 0}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "", "flag": 0, "wordId": 2, "end": 1}}
```

**响应字段说明**:
- `code`: 状态码，0 表示成功，1 表示错误
- `sessionId`: 会话 ID
- `answer`: 增量回答内容
- `flag`: 标志位，1 表示有内容，0 表示结束
- `wordId`: 词汇序号
- `end`: 结束标志，1 表示流式响应结束

**错误响应**:
```json
{
  "code": 1,
  "message": "当前网络异常，请稍后再试。",
  "data": {
    "sessionId": "xxx",
    "answer": "当前网络异常，请稍后再试。",
    "flag": 1,
    "wordId": 0,
    "end": 0
  }
}
```

### 4. 专业领域问答接口

以下是各专业领域的专用接口，均使用相同的请求/响应格式：

#### 4.1 法律法规
**端点**: `POST /api/laws`

#### 4.2 标准规范
**端点**: `POST /api/standards`

#### 4.3 应急知识
**端点**: `POST /api/emergency`

#### 4.4 事故案例
**端点**: `POST /api/accidents`

#### 4.5 MSDS
**端点**: `POST /api/msds`

#### 4.6 标准政策
**端点**: `POST /api/policies`

#### 4.7 通用问答
**端点**: `POST /api/general`

**特殊说明**: 此接口会根据问题内容智能路由：
- 如果问题匹配园区介绍、企业介绍、安全状况等关键词，则路由到 Dify 服务
- 否则路由到 RAGFlow 通用服务

**路由规则关键词**:
- 介绍.*园区
- 园区.*介绍
- 介绍一下园区
- 园区.*情况
- 园区.*信息
- 介绍.*企业
- 介绍.*公司
- 企业.*介绍
- 介绍.*园区.*安全
- 园区.*安全.*状况
- 园区.*是否安全
- 园区安全.*介绍
- .*安全状况

#### 4.8 重大危险源预警
**端点**: `POST /api/warn`

#### 4.9 当日安全态势
**端点**: `POST /api/safesituation`

#### 4.10 双重预防机制效果
**端点**: `POST /api/prevent`

#### 4.11 园区开停车
**端点**: `POST /api/park`

#### 4.12 园区特殊作业态势
**端点**: `POST /api/special`

#### 4.13 园区企业态势
**端点**: `POST /api/firmsituation`

### 5. 会话管理接口

#### 5.1 创建会话
**端点**: `POST /api/sessions/{category}`

**描述**: 为指定类别创建新会话

**路径参数**:
- `category` (string, required): 问答类别

**请求体**:
```json
{
  "name": "会话名称",
  "user_id": "optional-user-id"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "会话创建成功",
  "data": {
    "session_id": "uuid-session-id",
    "category": "法律法规",
    "name": "会话名称",
    "user_id": "user-123"
  }
}
```

#### 5.2 获取用户所有会话
**端点**: `GET /api/user/{user_id}/sessions`

**描述**: 获取指定用户的所有会话信息

**路径参数**:
- `user_id` (string, required): 用户 ID

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "user_id": "user-123",
    "sessions": {
      "法律法规": {
        "session_id": "uuid-1",
        "name": "法律法规_session_20260126_103000",
        "create_time": "2026-01-26T10:30:00",
        "last_activity": "2026-01-26T10:35:00",
        "message_count": 5
      },
      "标准规范": {
        "session_id": "uuid-2",
        "name": "标准规范_session_20260126_110000",
        "create_time": "2026-01-26T11:00:00",
        "last_activity": "2026-01-26T11:05:00",
        "message_count": 3
      }
    }
  }
}
```

#### 5.3 获取单个会话信息
**端点**: `GET /api/sessions/{session_id}`

**描述**: 获取指定会话的详细信息

**路径参数**:
- `session_id` (string, required): 会话 ID

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "id": "uuid-session-id",
    "chat_id": "1b0abaca824a11f0bc900242ac140003",
    "name": "法律法规_session_20260126_103000",
    "user_id": "user-123",
    "category": "法律法规",
    "create_time": "2026-01-26T10:30:00",
    "last_activity": "2026-01-26T10:35:00",
    "message_count": 5,
    "rag_session_id": "rag-uuid"
  }
}
```

#### 5.4 获取所有会话
**端点**: `GET /api/sessions`

**描述**: 获取系统中所有活跃会话

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": [
    {
      "id": "uuid-1",
      "chat_id": "1b0abaca824a11f0bc900242ac140003",
      "name": "法律法规_session_20260126_103000",
      "user_id": "user-123",
      "category": "法律法规",
      "create_time": "2026-01-26T10:30:00",
      "last_activity": "2026-01-26T10:35:00",
      "message_count": 5
    }
  ]
}
```

#### 5.5 删除会话
**端点**: `DELETE /api/sessions/{session_id}`

**描述**: 删除指定会话

**路径参数**:
- `session_id` (string, required): 会话 ID

**响应示例**:
```json
{
  "code": 0,
  "message": "会话删除成功",
  "data": null
}
```

## 数据模型

### ChatRequest
```python
{
  "question": str,        # 必填，用户问题
  "session_id": str,      # 可选，会话 ID
  "user_id": str          # 可选，用户 ID
}
```

### SessionRequest
```python
{
  "name": str,            # 必填，会话名称
  "user_id": str          # 可选，用户 ID
}
```

### ChatResponse
```python
{
  "code": int,            # 状态码，0=成功，1=失败
  "message": str,         # 响应消息
  "data": dict            # 响应数据
}
```

### StreamChunk (流式响应数据块)
```python
{
  "sessionId": str,       # 会话 ID
  "answer": str,          # 增量回答内容
  "flag": int,            # 1=有内容，0=结束
  "wordId": int,          # 词汇序号
  "end": int              # 1=流结束，0=继续
}
```

## 会话管理机制

### 会话生命周期
1. **自动创建**: 首次请求时自动创建会话
2. **用户绑定**: 支持按 user_id 和 category 绑定会话
3. **活动更新**: 每次交互自动更新活动时间
4. **自动过期**: 1 小时无活动自动过期
5. **自动清理**: 健康检查时清理过期会话

### 会话存储结构
```python
{
  "id": "本地会话 ID",
  "chat_id": "RAGFlow chat ID",
  "rag_session_id": "RAGFlow session ID",
  "name": "会话名称",
  "user_id": "用户 ID",
  "category": "问答类别",
  "create_time": "创建时间",
  "last_activity": "最后活动时间",
  "message_count": "消息数量"
}
```

## 外部服务依赖

### RAGFlow 服务
- **基础 URL**: http://172.16.11.60:8081
- **API Key**: ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm
- **用途**: 主要的 RAG 问答服务
- **超时配置**: 300 秒

### Dify 服务
- **基础 URL**: http://172.16.11.60/v1/chat-messages
- **API Key**: app-dNlklapL8Mpm5VOTsiIGwSDE
- **用途**: 园区介绍、企业介绍等特定场景
- **响应模式**: streaming

## 错误处理

### 超时处理
- **超时时间**: 15 秒
- **超时响应**:
```json
{
  "code": 1,
  "message": "当前网络异常，请稍后再试。",
  "data": {
    "sessionId": "xxx",
    "answer": "当前网络异常，请稍后再试。",
    "flag": 1,
    "wordId": 0,
    "end": 0
  }
}
```

### 常见错误码
- `400`: 不支持的类别
- `404`: 会话不存在
- `500`: 服务器内部错误

## CORS 配置

服务已配置 CORS 中间件，允许所有来源访问：
- `allow_origins`: ["*"]
- `allow_credentials`: True
- `allow_methods`: ["*"]
- `allow_headers`: ["*"]

## 配置说明

### 环境变量
可通过 `.env` 文件配置以下参数：
- `RAG_BASE_URL`: RAGFlow 服务地址
- `RAG_API_KEY`: RAGFlow API 密钥
- `REQUEST_TIMEOUT`: 请求超时时间（秒）
- `STREAM_TIMEOUT`: 流式响应超时时间（秒）
- `SESSION_EXPIRE_HOURS`: 会话过期时间（小时）
- `MAX_SESSIONS_PER_USER`: 每用户最大会话数

### 默认配置
```python
RAG_BASE_URL = "http://172.16.11.60:8081"
RAG_API_KEY = "ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm"
REQUEST_TIMEOUT = 300
STREAM_TIMEOUT = 300
SESSION_EXPIRE_HOURS = 1
MAX_SESSIONS_PER_USER = 5
```

## 使用示例

### Python 示例
```python
import requests
import json

# 1. 获取支持的类别
response = requests.get("http://localhost:11027/api/categories")
print(response.json())

# 2. 发起问答请求（流式）
url = "http://localhost:11027/api/laws"
data = {
    "question": "什么是安全生产法？",
    "user_id": "user-123"
}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        line_text = line.decode('utf-8')
        if line_text.startswith('data: '):
            data_str = line_text[6:]
            chunk = json.loads(data_str)
            print(chunk)

# 3. 获取用户会话
response = requests.get("http://localhost:11027/api/user/user-123/sessions")
print(response.json())
```

### JavaScript 示例
```javascript
// 使用 EventSource 接收流式响应
const eventSource = new EventSource('http://localhost:11027/api/laws', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: '什么是安全生产法？',
    user_id: 'user-123'
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);

  if (data.data && data.data.end === 1) {
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('Error:', error);
  eventSource.close();
};
```

## 性能特性

- **异步处理**: 使用 aiohttp 实现异步 HTTP 请求
- **流式响应**: 实时返回 AI 生成内容，降低首字延迟
- **会话复用**: 同一用户同一类别自动复用会话
- **自动清理**: 定期清理过期会话，避免内存泄漏
- **超时保护**: 15 秒超时机制，防止长时间等待

## 注意事项

1. **会话管理**: 会话在内存中管理，服务重启后会话数据丢失
2. **API 密钥**: 生产环境应通过环境变量配置，避免硬编码
3. **超时设置**: 15 秒超时适用于大多数场景，特殊场景可能需要调整
4. **并发限制**: 未设置并发限制，高并发场景需要额外配置
5. **日志记录**: 使用 Python logging 模块，日志级别为 INFO

## 更新日志

### v1.0.0 (2026-01-26)
- 初始版本
- 支持 13 个专业领域问答
- 实现流式响应
- 实现会话管理
- 支持智能路由（RAGFlow/Dify）
- 添加超时保护机制
