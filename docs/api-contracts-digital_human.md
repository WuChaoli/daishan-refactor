# API 合约文档 - Digital Human Command Interface

## 文档信息

- **服务名称**: Digital Human Command Interface (数字人指令接口)
- **服务端口**: 11029
- **基础路径**: http://localhost:11029
- **API 版本**: 1.0.0
- **生成日期**: 2026-01-26

## 服务概述

基于 FastAPI 封装的流式聊天接口，作为 Dify AI 服务的代理层，提供标准 SSE (Server-Sent Events) 格式的流式输出，保留打字机效果，用于数字人交互场景。

## 技术栈

- **框架**: FastAPI
- **Python 版本**: 3.12
- **主要依赖**:
  - httpx (异步 HTTP 客户端)
  - pydantic (数据验证)
  - uvicorn (ASGI 服务器)

## 核心功能

1. **流式聊天**: 实时流式返回 AI 回答，支持打字机效果
2. **事件驱动**: 标准 SSE 格式，支持多种事件类型
3. **超时保护**: 15 秒超时机制，自动重试
4. **错误处理**: 完善的错误处理和重试机制
5. **CORS 支持**: 跨域资源共享配置

## API 端点列表

### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查服务是否正常运行

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "service": "Streaming Chat FastAPI",
  "version": "1.0.0"
}
```

### 2. 流式聊天接口

**端点**: `POST /api/stream-chat`

**描述**: 接收用户输入，返回标准 SSE 格式的流式输出，支持打字机效果

**请求体**:
```json
{
  "text_input": "请介绍贵公司",
  "user_id": "user_001"
}
```

**请求模型字段**:
- `text_input` (string, required): 用户输入文本，不能为空
- `user_id` (string, optional): 用户标识，默认为 "fastapi_client_user"

**响应类型**: `text/event-stream` (Server-Sent Events)

**响应头**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Cache-Control
```

**SSE 事件类型**:

#### 2.1 start 事件
流式输出开始标志
```
event: start
data: {"message": "开始流式输出"}

```

#### 2.2 message 事件
消息内容片段，每次输出 3 个字符
```
id: 1
event: message
data: {"content": "请介", "type": "chunk"}

id: 2
event: message
data: {"content": "绍贵", "type": "chunk"}

```

**字段说明**:
- `content`: 文本片段内容（每次 3 个字符）
- `type`: 固定为 "chunk"

**打字机效果**: 每个片段之间延迟 0.02 秒（20ms）

#### 2.3 complete 事件
流式输出完成标志
```
event: complete
data: {"message": "流式输出已完成"}

```

#### 2.4 error 事件
错误信息
```
event: error
data: {"error": "错误描述信息"}

```

**常见错误**:
- API 请求失败（状态码非 200）
- 请求超时（超过 15 秒）
- 网络连接错误
- JSON 解析失败

#### 2.5 warning 事件
警告信息
```
event: warning
data: {"warning": "警告描述信息"}

```

**常见警告**:
- 流式数据解析失败
- 数据格式异常

#### 2.6 end 事件
流结束标志
```
event: end
data: [DONE]

```

### 超时响应格式

当请求超过 15 秒未收到响应时，返回超时错误：

```
data: {"code": 1, "message": "当前网络异常，请稍后再试。", "data": {"answer": "当前网络异常，请稍后再试。", "flag": 1, "wordId": 0, "end": 0}}

data: {"code": 1, "data": {"answer": "", "flag": 0, "wordId": 1, "end": 1}}

```

## 数据模型

### ChatInput (请求模型)
```python
{
  "text_input": str,      # 必填，用户输入文本
  "user_id": str          # 可选，用户标识，默认 "fastapi_client_user"
}
```

### SSE 事件数据格式

#### Start Event
```json
{
  "message": "开始流式输出"
}
```

#### Message Event
```json
{
  "content": "文本片段",
  "type": "chunk"
}
```

#### Complete Event
```json
{
  "message": "流式输出已完成"
}
```

#### Error Event
```json
{
  "error": "错误描述信息"
}
```

#### Warning Event
```json
{
  "warning": "警告描述信息"
}
```

## 外部服务依赖

### Dify AI 服务
- **基础 URL**: http://172.16.11.60/v1
- **端点**: /chat-messages
- **API Key**: app-Dkzi2px4Gg8F7vaUdn22Z3VL
- **超时配置**: 30 秒
- **响应模式**: streaming

### Dify 请求参数
```json
{
  "query": "用户输入",
  "inputs": {},
  "response_mode": "streaming",
  "user": "用户ID",
  "conversation_id": "",
  "auto_generate_name": true,
  "files": []
}
```

## 错误处理机制

### 重试机制
- **最大重试次数**: 2 次
- **重试延迟**: 1 秒（指数退避）
- **适用场景**: 请求超时

### 超时处理
- **超时时间**: 15 秒（首次响应）
- **超时响应**: 返回网络异常提示
- **自动终止**: 超时后自动结束流式响应

### 错误类型

#### 1. HTTP 错误
- **状态码非 200**: 返回 error 事件，包含状态码和响应详情
- **示例**: `{"error": "API请求失败，状态码: 500, 响应: ..."}`

#### 2. 超时错误
- **请求超时**: 超过 30 秒未响应
- **首次响应超时**: 超过 15 秒未收到首个数据块
- **重试**: 自动重试最多 2 次

#### 3. 网络错误
- **连接失败**: 无法连接到 Dify 服务
- **请求异常**: httpx.RequestError
- **示例**: `{"error": "请求发生错误: ..."}`

#### 4. 数据解析错误
- **JSON 解析失败**: 返回 warning 事件
- **继续处理**: 跳过错误数据，继续处理后续流

#### 5. 输入验证错误
- **空输入**: HTTP 400 错误
- **错误详情**: `{"detail": "text_input 字段不能为空"}`

## CORS 配置

服务已配置 CORS 中间件，允许所有来源访问：
- `allow_origins`: ["*"]
- `allow_credentials`: True
- `allow_methods`: ["*"]
- `allow_headers`: ["*"]

## 配置说明

### 核心配置
```python
FIXED_API_KEY = "app-Dkzi2px4Gg8F7vaUdn22Z3VL"
FIXED_BASE_URL = "http://172.16.11.60/v1"
DIFY_ENDPOINT = "/chat-messages"
DIFY_TIMEOUT = 30.0  # 秒
FIXED_PORT = 11029
MAX_RETRY_ATTEMPTS = 2
RETRY_DELAY = 1.0  # 秒
```

### 打字机效果配置
```python
chunk_size = 3  # 每次输出 3 个字符
delay = 0.02  # 每个片段延迟 20ms
```

## 使用示例

### Python 示例
```python
import requests
import json

url = "http://localhost:11029/api/stream-chat"
data = {
    "text_input": "请介绍贵公司",
    "user_id": "user_001"
}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line_text = line.decode('utf-8')
        print(line_text)

        # 解析 SSE 格式
        if line_text.startswith('event: '):
            event_type = line_text.split(': ')[1]
            print(f"Event: {event_type}")
        elif line_text.startswith('data: '):
            data_str = line_text.split(': ', 1)[1]
            if data_str != '[DONE]':
                data_obj = json.loads(data_str)
                print(f"Data: {data_obj}")
```

### JavaScript 示例
```javascript
const eventSource = new EventSource('http://localhost:11029/api/stream-chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text_input: '请介绍贵公司',
    user_id: 'user_001'
  })
});

// 监听 start 事件
eventSource.addEventListener('start', (event) => {
  const data = JSON.parse(event.data);
  console.log('开始:', data.message);
});

// 监听 message 事件
eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  console.log('内容:', data.content);
  // 将内容追加到页面
  document.getElementById('output').textContent += data.content;
});

// 监听 complete 事件
eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('完成:', data.message);
});

// 监听 error 事件
eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('错误:', data.error);
  eventSource.close();
});

// 监听 end 事件
eventSource.addEventListener('end', (event) => {
  console.log('流结束');
  eventSource.close();
});
```

### cURL 示例
```bash
curl -X POST http://localhost:11029/api/stream-chat \
  -H "Content-Type: application/json" \
  -d '{
    "text_input": "请介绍贵公司",
    "user_id": "user_001"
  }' \
  --no-buffer
```

## 性能特性

- **异步处理**: 使用 httpx.AsyncClient 实现异步 HTTP 请求
- **流式响应**: 实时返回 AI 生成内容，降低首字延迟
- **打字机效果**: 每次输出 3 个字符，延迟 20ms，模拟打字效果
- **连接复用**: 应用生命周期内复用 HTTP 客户端
- **自动重试**: 超时自动重试，最多 2 次
- **超时保护**: 15 秒首次响应超时保护

## 应用生命周期管理

### 启动阶段
1. 初始化日志系统
2. 创建异步 HTTP 客户端
3. 配置 CORS 中间件
4. 启动 FastAPI 应用

### 运行阶段
1. 接收客户端请求
2. 验证输入参数
3. 转发请求到 Dify 服务
4. 流式处理响应
5. 发送 SSE 事件到客户端

### 关闭阶段
1. 关闭异步 HTTP 客户端
2. 清理资源
3. 记录关闭日志

## 日志记录

### 日志级别
- **INFO**: 正常操作日志
- **WARNING**: 警告信息（如数据解析失败）
- **ERROR**: 错误信息（如请求失败）
- **EXCEPTION**: 异常堆栈（完整异常信息）

### 日志格式
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 关键日志点
1. 应用启动/关闭
2. API 请求发送
3. 流式输出完成
4. 错误和异常
5. 重试操作

## 注意事项

1. **API 密钥安全**: 生产环境应通过环境变量配置，避免硬编码
2. **单进程运行**: 流式处理建议使用单进程模式（workers=1）
3. **超时设置**: 15 秒首次响应超时，30 秒总超时
4. **重试策略**: 仅对超时错误进行重试，其他错误直接返回
5. **打字机效果**: 延迟时间可根据需求调整（当前 20ms）
6. **CORS 配置**: 生产环境应限制允许的来源域名
7. **缓冲禁用**: 设置 X-Accel-Buffering: no 禁用 nginx 缓冲

## 部署建议

### 开发环境
```bash
python main.py
```

### 生产环境
```bash
uvicorn main:app --host 0.0.0.0 --port 11029 --workers 1
```

### Docker 部署
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11029", "--workers", "1"]
```

### 环境变量（建议）
```bash
DIFY_API_KEY=app-Dkzi2px4Gg8F7vaUdn22Z3VL
DIFY_BASE_URL=http://172.16.11.60/v1
DIFY_TIMEOUT=30.0
APP_PORT=11029
MAX_RETRY_ATTEMPTS=2
```

## API 文档

FastAPI 自动生成的交互式 API 文档：
- **Swagger UI**: http://localhost:11029/docs
- **ReDoc**: http://localhost:11029/redoc

## 监控指标

### 建议监控项
1. **请求成功率**: 成功请求 / 总请求
2. **平均响应时间**: 首字延迟和总响应时间
3. **超时率**: 超时请求 / 总请求
4. **重试率**: 重试次数 / 总请求
5. **错误率**: 错误请求 / 总请求
6. **并发连接数**: 当前活跃的流式连接

### 健康检查
定期调用 `/health` 端点检查服务状态

## 故障排查

### 问题 1: 请求超时
**症状**: 15 秒后返回超时错误
**原因**: Dify 服务响应慢或网络延迟
**解决**:
- 检查 Dify 服务状态
- 增加超时时间配置
- 检查网络连接

### 问题 2: 流式输出中断
**症状**: 输出到一半停止
**原因**: 网络连接中断或 Dify 服务异常
**解决**:
- 检查网络稳定性
- 查看日志中的错误信息
- 检查 Dify 服务日志

### 问题 3: 打字机效果不流畅
**症状**: 输出卡顿或延迟不均匀
**原因**: 服务器负载高或网络抖动
**解决**:
- 调整 chunk_size 和 delay 参数
- 优化服务器性能
- 使用 CDN 或负载均衡

### 问题 4: CORS 错误
**症状**: 浏览器报跨域错误
**原因**: CORS 配置不正确
**解决**:
- 检查 allow_origins 配置
- 确认请求头包含正确的 Origin
- 检查浏览器控制台错误详情

## 更新日志

### v1.0.0 (2026-01-26)
- 初始版本
- 实现流式聊天接口
- 支持标准 SSE 格式
- 实现打字机效果
- 添加超时保护和重试机制
- 完善错误处理
- 配置 CORS 支持

## 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Server-Sent Events 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [httpx 文档](https://www.python-httpx.org/)
- [Dify API 文档](https://docs.dify.ai/)