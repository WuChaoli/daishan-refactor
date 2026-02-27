# RAG流式回复API

基于RAG（检索增强生成）的流式回复服务，支持7个专业领域的智能问答，具备智能会话管理功能。

## 独立服务启动（当前推荐）

- 仓库根目录启动：`uv run python -m rag_stream.main`
- 子项目目录启动：`cd src/rag_stream && uv run python -m rag_stream.main`

对外调用统一环境变量：

- `RAG_STREAM_BASE_URL`（示例：`http://127.0.0.1:11028`）
- `RAG_STREAM_TIMEOUT`（默认 `30` 秒）

健康检查接口：`GET /health`（返回 `200` + `{"status":"ok"}`）

## 功能特性

- 🚀 **流式回复**: 支持实时流式输出，提供更好的用户体验
- 🎯 **专业领域**: 涵盖法律法规、标准规范、应急知识、事故案例、MSDS、标准政策、通用等7个领域
- 🔄 **智能会话管理**: 自动绑定用户会话，支持连续对话，无需手动管理session_id
- 👤 **用户会话绑定**: 同一用户在同一类别中自动使用相同会话，实现上下文连续性
- 🌐 **RESTful API**: 标准的REST API设计，易于集成
- 📊 **实时监控**: 支持健康检查和状态监控
- ⏰ **自动过期管理**: 会话自动过期和清理，节省资源

## 支持的领域

| 领域     | 接口路径           | 说明                     |
| -------- | ------------------ | ------------------------ |
| 法律法规 | `/api/laws`      | 安全生产相关法律法规问答 |
| 标准规范 | `/api/standards` | 安全标准规范问答         |
| 应急知识 | `/api/emergency` | 应急处理知识问答         |
| 事故案例 | `/api/accidents` | 安全事故案例分析         |
| MSDS     | `/api/msds`      | 化学品安全技术说明书     |
| 标准政策 | `/api/policies`  | 安全政策和标准           |
| 通用     | `/api/general`   | 通用安全知识问答         |

## 快速开始

### 1. 安装依赖

```bash
cd src/rag_stream
uv sync
```

### 2. 配置环境

编辑 `config.py` 文件，配置RAG服务地址和API密钥：

```python
RAG_BASE_URL: str = "http://172.16.11.60:8081"
RAG_API_KEY: str = "your-api-key-here"
```

### 3. 启动服务

```bash
uv run python -m rag_stream.main
```

服务默认在 `http://0.0.0.0:11028` 启动（以 `config.yaml` 为准）。

### 4. 查看API文档

访问 `http://localhost:8000/docs` 查看交互式API文档。

## 核心功能说明

### 🎯 用户会话绑定

系统会自动为每个用户在每个类别中维护独立的会话，实现以下功能：

- **自动会话管理**: 用户只需提供`user_id`，系统自动创建或复用会话
- **上下文连续性**: 同一用户在同一类别中的连续提问会使用相同会话，保持对话上下文
- **多类别独立**: 不同类别使用独立会话，避免混淆
- **智能过期**: 会话自动过期和清理，节省资源

### 📝 使用示例

```bash
# 第一次提问 - 自动创建会话
curl -X POST "http://localhost:8000/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法规？",
    "user_id": "user001"
  }'

# 第二次提问 - 自动使用同一会话，保持上下文
curl -X POST "http://localhost:8000/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这些法规有哪些具体要求？",
    "user_id": "user001"
  }'
```

## API接口说明

### 流式问答

```http
POST /api/{category}
```

**参数:**
- `category`: 领域类别
- `question`: 问题内容
- `user_id`: 用户ID（必填，用于会话绑定）
- `session_id`: 会话ID（可选，通常不需要提供）

**示例:**
```bash
curl -X POST "http://localhost:8000/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法规？",
    "user_id": "user001"
  }'
```

### 创建会话

```http
POST /api/sessions/{category}
```

**参数:**
- `category`: 领域类别（法律法规、标准规范等）
- `name`: 会话名称
- `user_id`: 用户ID（可选）

### 获取用户会话信息

```http
GET /api/user/{user_id}/sessions
```

**功能**: 获取指定用户在所有类别的会话信息

### 流式响应格式

响应采用Server-Sent Events (SSE)格式：

```
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "部分回答", "flag": 1, "wordId": 0}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "更多回答", "flag": 1, "wordId": 1}}

data: {"code": 0, "data": {"sessionId": "xxx", "answer": "", "flag": 0, "wordId": 2}}
```

**字段说明:**
- `code`: 响应状态码（0表示成功）
- `sessionId`: 会话ID
- `answer`: 回答内容（增量）
- `flag`: 标志位（1=正常数据，0=结束标志）
- `wordId`: 词汇ID，用于排序

## 测试

运行测试客户端：

```bash
python test_client.py
```

测试将演示：
1. 用户会话绑定功能
2. 连续对话的上下文保持
3. 多类别会话管理
4. 会话信息查询

## 配置说明

### 配置文件（推荐）

- `config.yaml`：非敏感配置（按环境分段），用 `active_env` 切换 `development/production`
- `.env.development` / `.env.production`：敏感配置（至少包含 `RAG_BASE_URL`、`RAG_API_KEY`）

也支持通过系统环境变量覆盖配置（例如 `REQUEST_TIMEOUT`、`STREAM_TIMEOUT` 等）。

> 说明：历史遗留的 `rag_stream/.env` 仅为兼容保留，重构后的配置加载默认不再读取该文件。

## 部署说明

### 生产环境部署

```bash
# 使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 注意事项

1. **会话管理**: 系统自动管理会话，无需手动处理session_id
2. **用户ID**: 必须提供user_id以实现会话绑定
3. **错误处理**: 完善的错误处理和日志记录
4. **CORS支持**: 已配置跨域支持，可根据需要调整
5. **超时处理**: 支持长连接和超时配置
6. **自动清理**: 过期会话自动清理，节省内存资源

## 故障排除

### 常见问题

1. **连接超时**: 检查RAG服务是否正常运行，网络连接是否正常
2. **流式响应中断**: 检查超时配置和网络稳定性
3. **会话创建失败**: 验证API密钥和RAG服务状态
4. **会话丢失**: 检查会话过期时间配置

### 日志查看

服务运行时会输出详细日志，包括：
- 会话创建和管理状态
- 用户会话绑定信息
- 错误信息
- 性能指标

## 技术支持

如有问题，请检查：

1. 配置文件是否正确
2. RAG服务是否正常运行
3. 网络连接是否正常
4. 日志输出中的错误信息
5. 用户ID是否正确提供
