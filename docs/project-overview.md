# 岱山项目概览

## 项目信息

- **项目名称**：岱山 (daishan-master)
- **项目类型**：多部分 Backend API 项目
- **主要技术**：Python + FastAPI + Uvicorn
- **架构模式**：微服务架构 + API Gateway 模式

## 执行摘要

岱山项目是一个基于 Python FastAPI 的微服务系统，由两个独立的 API 服务组成，分别作为 Dify 和 RAGFlow AI 服务的代理网关。项目采用异步流式响应架构，支持实时对话和知识库问答功能。

## 项目结构

### 仓库类型
多部分项目（Multi-part），包含两个独立的 Backend API 服务。

### 服务组成

#### 1. Digital Human Command Interface（数字人命令接口）
- **路径**：`/Digital_human_command_interface/`
- **端口**：11029
- **功能**：Dify AI 服务的流式代理接口
- **主要特性**：
  - 流式聊天响应（SSE 格式）
  - 打字机效果输出
  - 重试机制和超时处理
  - 健康检查端点

#### 2. RAG Stream（RAG 流处理）
- **路径**：`/rag_stream/`
- **端口**：11027
- **功能**：RAGFlow 知识库服务的流式代理接口
- **主要特性**：
  - 多领域知识库问答（7个专业领域）
  - 会话管理
  - 流式响应
  - API 文档完善

## 技术栈概览

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.x | 主要编程语言 |
| Web 框架 | FastAPI | 0.104.1 | 异步 Web 框架 |
| ASGI 服务器 | Uvicorn | 0.24.0 | 高性能服务器 |
| HTTP 客户端 | httpx | latest | 异步 HTTP 客户端 |
| HTTP 客户端 | aiohttp | 3.9.1 | 异步 HTTP 客户端 |
| HTTP 客户端 | requests | 2.31.0 | 同步 HTTP 客户端 |
| 数据验证 | Pydantic | 2.5.0 | 数据验证和序列化 |
| 配置管理 | pydantic-settings | 2.1.0 | 配置管理 |
| 日志 | python-json-logger | 2.0.7 | JSON 格式日志 |

## 架构特点

### 微服务架构
- 两个独立部署的服务
- 各自独立的端口和进程
- 无共享状态和数据库

### API Gateway 模式
- 作为外部 AI 服务的代理
- 统一的请求/响应格式
- 错误处理和重试机制

### 异步流式处理
- 使用 asyncio 异步编程
- Server-Sent Events (SSE) 流式响应
- 实时数据传输

## 部署环境

### 服务器配置

**应用服务器（172.16.11.60）**
- Digital Human API
- RAG Stream API
- Dify 服务（端口 80）
- RAGFlow 服务（端口 8081）

**模型服务器（172.16.11.61）**
- vLLM 模型服务

**数据库服务器（172.16.11.73）**
- 达梦数据库（端口 5236）

### 网络访问
- VPN：`https://183.245.197.36:4430`
- 内网环境：172.16.11.0/24

## 文档资源

### 生成的文档
- [API 合约 - Digital Human](./api-contracts-digital_human.md)
- [API 合约 - RAG Stream](./api-contracts-rag_stream.md)
- [源代码树分析](./source-tree-analysis.md)
- [开发指南](./development-guide.md)
- [部署指南](./deployment-guide.md)
- [集成架构](./integration-architecture.md)

### 现有文档
- [项目 README](../README.md)
- [Digital Human 接口文档](../Digital_human_command_interface/接口文档.md)
- [Digital Human 运行文档](../Digital_human_command_interface/运行文档.md)
- [RAG Stream README](../rag_stream/README.md)
- [RAG Stream API 文档](../rag_stream/API接口文档.md)
- [RAG Stream 快速启动](../rag_stream/快速启动.md)

## 快速开始

### 前置要求
- Python 3.x
- pip 包管理器
- 访问内网环境（通过 VPN）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务

**Digital Human API：**
```bash
python Digital_human_command_interface/main.py
```

**RAG Stream API：**
```bash
python rag_stream/main.py
```

### 访问文档
- Digital Human API 文档：`http://localhost:11029/docs`
- RAG Stream API 文档：`http://localhost:11027/docs`

## 关键特性

### 1. 流式响应
- 实时数据传输
- 打字机效果
- 低延迟体验

### 2. 错误处理
- 自动重试机制
- 超时保护
- 详细错误信息

### 3. 异步架构
- 高并发支持
- 非阻塞 I/O
- 资源高效利用

### 4. CORS 支持
- 跨域请求支持
- 灵活的配置选项

## 开发工作流

1. **本地开发**：使用 `uvicorn` 启动服务
2. **测试**：通过 `/docs` 端点测试 API
3. **部署**：使用 `nohup` 后台运行
4. **监控**：查看日志文件

## 维护和支持

### 日志位置
- Digital Human：`Digital_human_command_interface/main.log`
- RAG Stream：`rag_stream/main.log`

### 进程管理
```bash
# 查找进程
lsof -t -i:11029  # Digital Human
lsof -t -i:11027  # RAG Stream

# 停止服务
lsof -t -i:11029 | xargs kill -9
lsof -t -i:11027 | xargs kill -9
```

## 未来规划

### 短期目标
1. 添加单元测试和集成测试
2. 实现会话持久化（Redis）
3. 添加监控和告警

### 长期目标
1. 容器化部署（Docker）
2. Kubernetes 编排
3. 服务网格集成
4. 分布式追踪

## 联系信息

- **项目位置**：`/home/wuchaoli/codespace/daishan-master`
- **文档位置**：`/home/wuchaoli/codespace/daishan-master/docs`

## 相关链接

- Dify 服务：`http://172.16.11.60/apps`
- RAGFlow 服务：`http://172.16.11.60:8081/knowledge`
- VPN 访问：`https://183.245.197.36:4430`
