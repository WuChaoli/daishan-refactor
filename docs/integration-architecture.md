# 集成架构文档

## 项目概述

岱山项目由两个独立的 FastAPI 微服务组成，分别作为不同 AI 服务的代理网关。

## 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端应用                              │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
        ┌───────────▼──────────┐  ┌─────▼──────────────┐
        │  Digital Human API   │  │   RAG Stream API   │
        │   (端口: 11029)      │  │   (端口: 11027)    │
        │                      │  │                    │
        │  FastAPI + Uvicorn   │  │  FastAPI + Uvicorn │
        └───────────┬──────────┘  └─────┬──────────────┘
                    │                    │
                    │                    │
        ┌───────────▼──────────┐  ┌─────▼──────────────┐
        │    Dify 服务         │  │  RAGFlow 服务      │
        │  (172.16.11.60)      │  │  (172.16.11.60)    │
        └──────────────────────┘  └────────────────────┘
```

## 集成点

### 1. Digital Human Command Interface → Dify

**集成类型：** HTTP REST API 代理

**通信方式：**
- 协议：HTTP/HTTPS
- 方法：POST
- 端点：`http://172.16.11.60/v1/chat-messages`
- 认证：Bearer Token (`app-Dkzi2px4Gg8F7vaUdn22Z3VL`)

**数据流：**
1. 客户端发送请求到 `/api/stream-chat`（端口 11029）
2. Digital Human API 转发请求到 Dify 服务
3. Dify 返回流式响应（SSE 格式）
4. Digital Human API 处理并转发流式数据到客户端

**请求格式：**
```json
{
  "text_input": "用户输入文本",
  "user_id": "用户标识"
}
```

**响应格式：** Server-Sent Events (SSE)
- 事件类型：start, message, complete, error, warning, end

### 2. RAG Stream → RAGFlow

**集成类型：** HTTP REST API 代理

**通信方式：**
- 协议：HTTP/HTTPS
- 方法：POST/GET
- 基础 URL：配置在 `config.py` 中
- 认证：API Key

**数据流：**
1. 客户端发送请求到 RAG Stream API（端口 11027）
2. RAG Stream API 调用 RAGFlow 知识库服务
3. RAGFlow 返回流式响应
4. RAG Stream API 处理并转发到客户端

**支持的操作：**
- 创建会话
- 流式问答
- 会话管理
- 知识库查询

## 服务间通信

### 独立部署

两个服务完全独立部署，没有直接的服务间通信：

- **Digital Human API**：独立进程，端口 11029
- **RAG Stream API**：独立进程，端口 11027

### 共享资源

- **无共享数据库**：两个服务都不使用持久化数据库
- **无共享缓存**：各自管理内存中的会话状态
- **独立配置**：各自的配置文件和环境变量

## 部署架构

### 服务器配置

**主服务器（172.16.11.60）：**
- Digital Human API：`/home/server02/ai/Digital_human_command_interface/`
- RAG Stream API：`/home/server02/ai/rag_stream/`
- Dify 服务：端口 80
- RAGFlow 服务：端口 8081

**模型服务器（172.16.11.61）：**
- AI 模型服务（vLLM）

### 启动方式

**Digital Human API：**
```bash
nohup python /home/server02/ai/Digital_human_command_interface/main.py \
  >/home/wuchaoli/codespace/daishan-master/Digital_human_command_interface/main.log 2>&1 &
```

**RAG Stream API：**
```bash
nohup python /home/server02/ai/rag_stream/main.py \
  >/home/server02/ai/rag_stream/main.log 2>&1 &
```

## 网络拓扑

```
Internet
    │
    ▼
VPN (183.245.197.36:4430)
    │
    ▼
内网 (172.16.11.0/24)
    │
    ├─ 172.16.11.60 (应用服务器)
    │   ├─ Digital Human API (11029)
    │   ├─ RAG Stream API (11027)
    │   ├─ Dify (80)
    │   └─ RAGFlow (8081)
    │
    ├─ 172.16.11.61 (模型服务器)
    │   └─ vLLM 模型服务
    │
    └─ 172.16.11.73 (数据库服务器)
        └─ 达梦数据库 (5236)
```

## 安全考虑

### 认证机制

1. **Digital Human API**
   - 使用固定的 API Key 访问 Dify
   - CORS 配置：允许所有来源（开发环境）

2. **RAG Stream API**
   - 使用配置文件中的 API Key
   - CORS 配置：允许所有来源

### 网络安全

- VPN 访问：通过 VPN 访问内网服务
- 内网隔离：服务部署在内网环境
- 端口管理：特定端口对外暴露

## 监控和日志

### 日志记录

两个服务都使用 Python logging 模块：
- 日志级别：INFO
- 日志格式：时间戳 + 日志级别 + 消息
- 日志输出：标准输出 + 文件

### 健康检查

**Digital Human API：**
- 端点：`GET /health`
- 响应：`{"status": "healthy", "service": "...", "version": "..."}`

**RAG Stream API：**
- 端点：`GET /health`（如果实现）

## 扩展性考虑

### 水平扩展

- 两个服务都是无状态的（会话存储在内存中）
- 可以通过负载均衡器部署多个实例
- 需要考虑会话持久化方案（如 Redis）

### 垂直扩展

- 增加服务器资源（CPU、内存）
- 调整 Uvicorn workers 数量

## 故障处理

### 重试机制

**Digital Human API：**
- 最大重试次数：2 次
- 重试延迟：1 秒（指数退避）
- 超时时间：30 秒

### 错误处理

- HTTP 错误：返回标准错误响应
- 超时错误：返回超时提示
- 流式错误：通过 SSE 事件传递错误信息

## 性能优化

### 异步处理

- 使用 `asyncio` 和 `httpx.AsyncClient`
- 流式响应避免内存积累
- 异步 HTTP 客户端复用

### 连接管理

- HTTP 客户端生命周期管理
- 连接池复用
- 超时配置优化

## 未来改进建议

1. **服务发现**：引入服务注册和发现机制
2. **配置中心**：统一配置管理
3. **分布式追踪**：添加链路追踪（如 OpenTelemetry）
4. **会话持久化**：使用 Redis 存储会话状态
5. **API 网关**：统一入口和路由管理
6. **容器化**：使用 Docker 和 Kubernetes 部署
