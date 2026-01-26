# 岱山项目文档索引

> 本文档是 AI 辅助开发的主要入口点。所有项目文档和架构信息都可以从这里访问。

## 项目概览

- **项目名称**：岱山 (daishan-master)
- **项目类型**：多部分 Backend API 项目
- **主要技术**：Python + FastAPI + Uvicorn
- **架构模式**：微服务架构 + API Gateway 模式
- **生成日期**：2026-01-26

## 快速参考

### Part 1: Digital Human Command Interface
- **类型**：Backend API
- **技术栈**：Python 3.x + FastAPI 0.104.1
- **端口**：11029
- **功能**：Dify AI 服务代理

### Part 2: RAG Stream
- **类型**：Backend API
- **技术栈**：Python 3.x + FastAPI 0.104.1
- **端口**：11027
- **功能**：RAGFlow 知识库服务代理

## 生成的文档

### 核心文档
- [项目概览](./project-overview.md) - 项目整体介绍和技术栈
- [源代码树分析](./source-tree-analysis.md) - 完整的目录结构和说明
- [集成架构](./integration-architecture.md) - 服务间通信和集成方式

### API 文档
- [API 合约 - Digital Human](./api-contracts-digital_human.md) - Digital Human API 端点和数据格式
- [API 合约 - RAG Stream](./api-contracts-rag_stream.md) - RAG Stream API 端点和数据格式

### 开发和部署
- [开发指南](./development-guide.md) - 本地开发环境设置和开发流程
- [部署指南](./deployment-guide.md) - 生产环境部署和运维指南

### 架构文档
- [架构 - Digital Human](./architecture-digital_human.md) _(To be generated)_
- [架构 - RAG Stream](./architecture-rag_stream.md) _(To be generated)_

## 现有文档

### 项目根目录
- [README.md](../README.md) - 项目主文档（包含部署和运行说明）
- [README.en.md](../README.en.md) - 英文版 README

### Digital Human Command Interface
- [接口文档](../Digital_human_command_interface/接口文档.md) - API 接口详细说明
- [运行文档](../Digital_human_command_interface/运行文档.md) - 运行和部署说明

### RAG Stream
- [README](../rag_stream/README.md) - RAG Stream 主文档
- [快速启动](../rag_stream/快速启动.md) - 快速启动指南
- [API 接口文档](../rag_stream/API接口文档.md) - API 接口详细说明
- [API 快速参考](../rag_stream/API快速参考.md) - API 快速参考卡片
- [运行文档](../rag_stream/运行文档.md) - 运行和部署说明
- [Chat ID 记录](../rag_stream/chatID记录.md) - Chat ID 管理文档
- [问答 API 接口文档](../rag_stream/问答API接口文档(1).md) - 问答 API 详细说明
- [Chat 文档](../rag_stream/chat.md) - Chat 功能说明

## 快速开始

### 开发环境设置

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动 Digital Human API**
   ```bash
   python Digital_human_command_interface/main.py
   ```
   访问：`http://localhost:11029/docs`

3. **启动 RAG Stream API**
   ```bash
   python rag_stream/main.py
   ```
   访问：`http://localhost:11027/docs`

### 生产环境部署

参考 [部署指南](./deployment-guide.md) 了解详细的生产环境部署步骤。

## 使用场景指南

### 场景 1：开发新的 API 端点
1. 阅读 [API 合约文档](./api-contracts-digital_human.md) 或 [API 合约文档](./api-contracts-rag_stream.md)
2. 参考 [开发指南](./development-guide.md) 设置开发环境
3. 查看 [源代码树分析](./source-tree-analysis.md) 了解代码组织

### 场景 2：理解服务间通信
1. 阅读 [集成架构](./integration-architecture.md)
2. 查看 [项目概览](./project-overview.md) 了解整体架构

### 场景 3：部署到生产环境
1. 阅读 [部署指南](./deployment-guide.md)
2. 参考 [README.md](../README.md) 中的部署说明

### 场景 4：添加新功能
1. 阅读 [项目概览](./project-overview.md) 了解项目结构
2. 查看相关的 API 合约文档
3. 参考 [开发指南](./development-guide.md) 进行开发

## 技术栈详情

### 核心框架
- **FastAPI 0.104.1**：现代异步 Web 框架
- **Uvicorn 0.24.0**：高性能 ASGI 服务器
- **Pydantic 2.5.0**：数据验证和序列化

### HTTP 客户端
- **httpx**：异步 HTTP 客户端
- **aiohttp 3.9.1**：异步 HTTP 客户端
- **requests 2.31.0**：同步 HTTP 客户端

### 其他依赖
- **python-multipart 0.0.6**：多部分表单数据处理
- **pydantic-settings 2.1.0**：配置管理
- **python-json-logger 2.0.7**：JSON 格式日志

## 架构模式

### 微服务架构
- 两个独立的服务
- 各自独立的端口和进程
- 无共享状态

### API Gateway 模式
- 作为外部 AI 服务的代理
- 统一的请求/响应格式
- 错误处理和重试机制

### 异步流式处理
- Server-Sent Events (SSE)
- 实时数据传输
- 打字机效果输出

## 部署环境

### 服务器
- **应用服务器**：172.16.11.60
- **模型服务器**：172.16.11.61
- **数据库服务器**：172.16.11.73

### 网络访问
- **VPN**：https://183.245.197.36:4430
- **内网**：172.16.11.0/24

## 维护和支持

### 日志文件
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

### 健康检查
- Digital Human：`GET http://localhost:11029/health`
- RAG Stream：`GET http://localhost:11027/health`

## 下一步

### 对于 Brownfield PRD
当准备规划新功能时，运行 PRD 工作流并提供此索引作为输入：
- 对于 UI 功能：参考相关的架构文档
- 对于 API 功能：参考 API 合约文档
- 对于全栈功能：参考集成架构文档

### 对于开发
1. 查看 [开发指南](./development-guide.md) 设置环境
2. 阅读相关的 API 合约文档
3. 参考 [源代码树分析](./source-tree-analysis.md) 了解代码结构

### 对于部署
1. 阅读 [部署指南](./deployment-guide.md)
2. 参考 [README.md](../README.md) 中的部署说明
3. 查看 [集成架构](./integration-architecture.md) 了解服务依赖

## 文档更新

本文档由 BMad Method document-project 工作流自动生成。

- **生成日期**：2026-01-26
- **工作流版本**：1.2.0
- **扫描级别**：深度扫描（Deep Scan）

---

**提示**：标记为 _(To be generated)_ 的文档可以通过重新运行 document-project 工作流并选择生成缺失文档来创建。
