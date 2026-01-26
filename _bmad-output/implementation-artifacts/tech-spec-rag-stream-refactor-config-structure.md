---
title: 'rag_stream 项目重构 - 配置管理和代码结构优化'
slug: 'rag-stream-refactor-config-structure'
created: '2026-01-26'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['FastAPI==0.104.1', 'pydantic==2.5.0', 'pydantic-settings==2.1.0', 'aiohttp==3.9.1', 'uvicorn==0.24.0', 'PyYAML']
files_to_modify: ['rag_stream/config.py', 'rag_stream/main.py', 'rag_stream/.env', 'rag_stream/models.py']
files_to_create: ['rag_stream/config.yaml', 'rag_stream/.env.development', 'rag_stream/.env.production', 'rag_stream/src/config/settings.py', 'rag_stream/src/models/schemas.py', 'rag_stream/src/routes/chat_routes.py', 'rag_stream/src/services/rag_service.py', 'rag_stream/src/services/dify_service.py', 'rag_stream/src/utils/session_manager.py']
code_patterns: ['异步编程(async/await)', 'SSE流式响应', '依赖注入(Depends)', 'Pydantic数据验证', '内存会话管理']
test_patterns: ['手动测试脚本', '无单元测试框架']
---

# Tech-Spec: rag_stream 项目重构 - 配置管理和代码结构优化

**Created:** 2026-01-26

## Overview

### Problem Statement

当前 rag_stream 项目存在以下问题：
1. 配置信息硬编码在 config.py 中，不方便调整
2. 缺少测试和生产环境的配置分离（包括敏感信息）
3. 路由和业务逻辑混在 main.py 中（847行），代码结构不清晰
4. 缺少环境切换机制

### Solution

实现多环境配置管理和模块化代码结构：
1. 使用 .env.development 和 .env.production 分别管理测试和生产环境的敏感信息
2. 使用 config.yaml 管理非敏感配置，支持多环境配置
3. 重构代码结构，将 main.py 拆分为 routes、services、models、utils 等模块
4. 通过 active_env 开关实现环境切换

### Scope

**In Scope:**
- 创建 .env.development 和 .env.production 文件
- 创建 config.yaml 配置文件，包含测试和生产两套配置
- 重构 config.py 以支持多环境 .env + YAML 混合加载
- 将 main.py 拆分为多个模块（routes, services, models, utils）
- 创建 src 目录结构
- 更新 main.py 为应用入口
- 确保所有功能正常工作

**Out of Scope:**
- 修改业务逻辑本身
- 添加新功能
- 修改 API 接口定义
- 数据库迁移或持久化改造

## Context for Development

### Codebase Patterns

**当前架构：**
- FastAPI 0.104.1 框架，采用 pydantic_settings 2.1.0 进行配置管理
- 异步编程模式（async/await），使用 aiohttp 3.9.1 进行异步 HTTP 请求
- SSE（Server-Sent Events）流式响应，支持实时数据推送
- 内存会话管理（SessionManager 类），无持久化存储
- 依赖注入模式（FastAPI Depends）
- 类型注解和 Pydantic 数据验证

**业务特点：**
- 支持 13 个不同类别的聊天助手（法律法规、标准规范、应急知识等）
- 集成 RAG 服务（http://172.16.11.60:8081）和 Dify Chatflow
- 会话自动过期机制（默认1小时）
- 超时处理（15秒无响应返回错误）
- 增量文本流式传输

**代码组织：**
- main.py（847行）：包含所有路由、业务逻辑、会话管理
- config.py（38行）：配置管理，硬编码配置值
- models.py（45行）：Pydantic 数据模型
- test.py/test_client.py：手动测试脚本

### Files to Reference

| File | Purpose | Lines | Key Components |
| ---- | ------- | ----- | -------------- |
| rag_stream/config.py | 配置管理模块 | 38 | Settings类, CHAT_IDS字典, 超时配置 |
| rag_stream/main.py | 主应用文件 | 847 | FastAPI应用, 16个路由, SessionManager, 流式响应函数 |
| rag_stream/models.py | 数据模型定义 | 45 | ChatType枚举, 5个Pydantic模型 |
| rag_stream/.env | 环境变量 | 2 | RAG_BASE_URL, RAG_API_KEY |
| rag_stream/requirements.txt | 依赖清单 | 8 | FastAPI, pydantic, aiohttp等 |
| rag_stream/test.py | 测试脚本 | 64 | 流式响应测试 |

### Technical Decisions

**1. 配置文件方案：**
   - **.env.development / .env.production**：存储敏感信息
     - RAG_BASE_URL（RAG 服务地址）
     - RAG_API_KEY（RAG API 密钥）

   - **config.yaml**：存储非敏感配置，包含 development 和 production 两个环境段
     ```yaml
     active_env: development  # 环境开关

     environments:
       development:
         request_timeout: 300
         stream_timeout: 300
         session_expire_hours: 1
         max_sessions_per_user: 5
         dify_api_url: "http://172.16.11.60/v1/chat-messages"
         dify_api_key: "app-dNlklapL8Mpm5VOTsiIGwSDE"
         chat_ids:
           法律法规: "1b0abaca824a11f0bc900242ac140003"
           # ... 其他13个聊天助手ID

       production:
         # 生产环境配置（不同的超时、CHAT_IDS等）
     ```

**2. 目录结构重构：**
   ```
   rag_stream/
   ├── src/
   │   ├── __init__.py
   │   ├── config/
   │   │   ├── __init__.py
   │   │   └── settings.py          # 配置加载模块（支持环境切换）
   │   ├── models/
   │   │   ├── __init__.py
   │   │   └── schemas.py           # 数据模型（从models.py迁移）
   │   ├── routes/
   │   │   ├── __init__.py
   │   │   └── chat_routes.py       # 路由定义（16个端点）
   │   ├── services/
   │   │   ├── __init__.py
   │   │   ├── rag_service.py       # RAG流式响应服务
   │   │   └── dify_service.py      # Dify流式响应服务
   │   └── utils/
   │       ├── __init__.py
   │       └── session_manager.py   # 会话管理类
   ├── config.yaml                  # 配置文件
   ├── .env.development             # 开发环境敏感信息
   ├── .env.production              # 生产环境敏感信息
   ├── main.py                      # 应用入口（简化）
   ├── requirements.txt             # 依赖（需添加PyYAML）
   └── test.py                      # 测试脚本
   ```

**3. 模块拆分策略：**
   - **src/config/settings.py**：
     - 从 config.py 迁移 Settings 类
     - 新增 YAML 配置加载逻辑
     - 根据 active_env 加载对应的 .env 文件
     - 合并 .env 和 YAML 配置

   - **src/models/schemas.py**：
     - 从 models.py 迁移所有 Pydantic 模型
     - 从 main.py 迁移 ChatRequest, SessionRequest 等模型

   - **src/utils/session_manager.py**：
     - 从 main.py 提取 SessionManager 类（约80行）

   - **src/services/rag_service.py**：
     - 从 main.py 提取 stream_chat_response 函数
     - 从 main.py 提取 create_rag_session 函数
     - 从 main.py 提取 get_or_create_session 函数

   - **src/services/dify_service.py**：
     - 从 main.py 提取 stream_dify_chatflow_response 函数
     - 从 main.py 提取 should_use_dify 函数

   - **src/routes/chat_routes.py**：
     - 从 main.py 提取所有16个路由端点
     - 保持路由装饰器和依赖注入

   - **main.py**（重构后）：
     - FastAPI 应用初始化
     - CORS 中间件配置
     - 路由注册
     - 应用启动入口

**4. 保持向后兼容：**
   - 所有 API 端点路径不变
   - 请求/响应格式不变
   - 业务逻辑不变
   - 仅重构代码组织结构

## Implementation Plan

### Tasks

**阶段1：准备配置文件**

- [ ] Task 1: 创建 config.yaml 配置文件模板
  - File: `rag_stream/config.yaml`
  - Action: 创建包含 development 和 production 两个环境配置段的 YAML 文件
  - Notes: 包含 active_env 开关、超时配置、会话配置、Dify 配置、CHAT_IDS 字典

- [ ] Task 2: 创建 .env.development 文件
  - File: `rag_stream/.env.development`
  - Action: 创建开发环境敏感信息文件，包含 RAG_BASE_URL 和 RAG_API_KEY
  - Notes: 用户将填写测试环境的配置

- [ ] Task 3: 创建 .env.production 文件
  - File: `rag_stream/.env.production`
  - Action: 创建生产环境敏感信息文件，包含 RAG_BASE_URL 和 RAG_API_KEY
  - Notes: 迁移当前 .env 的生产环境配置

**阶段2：创建模块结构**

- [ ] Task 4: 创建 src 目录结构和 __init__.py 文件
  - File: `rag_stream/src/__init__.py`, `rag_stream/src/config/__init__.py`, `rag_stream/src/models/__init__.py`, `rag_stream/src/routes/__init__.py`, `rag_stream/src/services/__init__.py`, `rag_stream/src/utils/__init__.py`
  - Action: 创建所有子目录和空的 __init__.py 文件
  - Notes: 确保 Python 包结构正确

- [ ] Task 5: 创建 src/config/settings.py
  - File: `rag_stream/src/config/settings.py`
  - Action: 创建配置加载模块，支持 .env 和 YAML 混合加载
  - Notes: 实现环境切换逻辑，根据 active_env 加载对应配置

- [ ] Task 6: 创建 src/models/schemas.py
  - File: `rag_stream/src/models/schemas.py`
  - Action: 迁移 models.py 的所有 Pydantic 模型和枚举
  - Notes: 迁移 ChatType 枚举和5个数据模型

**阶段3：迁移业务逻辑**

- [ ] Task 7: 创建 src/utils/session_manager.py
  - File: `rag_stream/src/utils/session_manager.py`
  - Action: 从 main.py 提取 SessionManager 类（约80行）
  - Notes: 包含会话创建、查询、更新、清理等方法

- [ ] Task 8: 创建 src/services/rag_service.py
  - File: `rag_stream/src/services/rag_service.py`
  - Action: 从 main.py 提取 RAG 相关业务函数
  - Notes: 包含 stream_chat_response, create_rag_session, get_or_create_session_get_rag_client 函数

- [ ] Task 9: 创建 src/services/dify_service.py
  - File: `rag_stream/src/services/dify_service.py`
  - Action: 从 main.py 提取 Dify 相关业务函数
  - Notes: 包含 stream_dify_chatflow_response, should_use_dify 函数

**阶段4：创建路由模块**

- [ ] Task 10: 创建 src/routes/chat_routes.py
  - File: `rag_stream/src/routes/chat_routes.py`
  - Action: 从 main.py 提取所有16个路由端点
  - Notes: 包含聊天接口、会话管理接口、健康检查接口等

**阶段5：重构主入口**

- [ ] Task 11: 重构 main.py
  - File: `rag_stream/main.py`
  - Action: 简化为应用入口，从新模块导入组件
  - Notes: FastAPI 初始化、CORS 配置、路由注册、启动入口

- [ ] Task 12: 更新 requirements.txt
  - File: `rag_stream/requirements.txt`
  - Action: 添加 PyYAML 依赖
  - Notes: 添加 `pyyaml==6.0.1`

- [ ] Task 13: 备份旧文件
  - File: `rag_stream/config.py`, `rag_stream/models.py`
  - Action: 重命名为 config.py.bak 和 models.py.bak
  - Notes: 保留备份以便回滚

**阶段6：验证**

- [ ] Task 14: 验证配置加载
  - File: `rag_stream/src/config/settings.py`
  - Action: 测试配置正确加载，环境切换正常
  - Notes: 手动测试开发环境和生产环境切换

- [ ] Task 15: 运行测试脚本
  - File: `rag_stream/test.py`
  - Action: 运行现有测试脚本，确保所有功能正常
  - Notes: 测试流式响应、会话管理等核心功能

### Acceptance Criteria

**配置管理验收标准：**

- [ ] AC 1: Given config.yaml 存在且 active_env 设置为 development, when 应用启动, then 加载 .env.development 的配置
- [ ] AC 2: Given config.yaml 存在且 active_env 设置为 production, when 应用启动, then 加载 .env.production 的配置
- [ ] AC 3: Given .env.development 文件缺失, when 应用启动, then 抛出明确的错误提示缺少的环境配置文件
- [ ] AC 4: Given config.yaml 中 active_env 指定的环境不存在, when 应用启动, then 抛出错误提示无效的环境名称
- [ ] AC 5: Given 测试环境和生产环境配置不同, when 切换 active_env, then 应用加载对应环境的 CHAT_IDS 和超时配置

**代码结构验收标准：**

- [ ] AC 6: Given main.py 被重构后, when 查看文件, then main.py 只包含应用初始化、CORS 配置和路由注册（不超过100行）
- [ ] AC 7: Given src 目录结构创建完成, when 查看, then 存在 config/, models/, routes/, services/, utils/ 子目录
- [ ] AC 8: Given 所有模块创建完成, when 导入, then 所有模块可以正确导入无循环依赖
- [ ] AC 9: Given 模块拆分完成, when 运行应用, then FastAPI 应用启动成功

**功能验证验收标准：**

- [ ] AC 10: Given 用户发送聊天请求到 /api/laws, when 请求处理, then 返回流式响应，格式与重构前一致
- [ ] AC 11: Given 用户发送聊天请求到 /api/general, when 问题匹配 should_use_dify 的模式, then 调用 Dify 服务返回流式响应
- [ ] AC 12: Given 用户创建会话, when 调用 /api/sessions/{category}, then 会话创建成功并返回 session_id
- [ ] AC 13: Given 用户查询会话信息, when 调用 /api/sessions/{session_id}, then 返回正确的会话信息
- [ ] AC 14: Given 调用健康检查 /health, when 请求处理, then 返回包含 active_sessions 和 active_users 的状态信息
- [ ] AC 15: Given 用户发送多个聊天请求, when 使用同一 user_id, then 会话被复用且消息计数递增
- [ ] AC 16: Given 会话过期时间到达, when 清理过期会话, then 过期会话被正确移除且不影响活跃会话

**边界情况验收标准：**

- [ ] AC 17: Given 用户发送空问题, when �verfy验证, then Pydantic 返回验证错误提示字段不能为空
- [ ] AC 18: Given 用户使用不支持的类别, when 发送请求, then 返回 400 错误提示不支持的类别
- [ ] AC 19: Given RAG 服务响应超时, when 15秒内无响应, then 返回"当前网络异常，请稍后再试"错误消息
- [ ] AC 20: Given Dify 服务不可用, when 请求发送, then 捕获异常并返回错误响应对客户端不崩溃

**集成测试验收标准：**

- [ ] AC 21: Given 运行 test.py 脚本, when 执行测试, then 测试成功完成且接收流式响应
- [ ] AC 22: Given 运行 test_client.py 脚本, when 执行测试, then 所有测试用例通过
- [ ] AC 23: Given 切换到生产环境配置, when 运行测试, then 使用生产环境的 RAG_BASE_URL 和 CHAT_IDS

**依赖验收标准：**

- [ ] AC 24: Given requirements.txt 更新后, when 执行 pip install -r requirements.txt, then PyYAML 成功安装且无版本冲突
- [ ] AC 25: Given 添加 PyYAML 依赖, when 导入 yaml 模块, then 导入成功无错误

## Additional Context

### Dependencies

**外部依赖：**
- pydantic_settings==2.1.0：配置管理和环境变量加载
- pyyaml==6.0.1：YAML 配置文件解析（新增）
- FastAPI==0.104.1：Web 框架
- aiohttp==3.9.1：异步 HTTP 客户端

**外部服务依赖：**
- RAG 服务：http://172.16.11.60:8081（地址和密钥通过配置加载）
- Dify Chatflow：http://172.16.11.60/v1/chat-messages（API key 通过配置加载）

**模块依赖关系：**
- main.py → routes/chat_routes.py
- routes/chat_routes.py → models/schemas.py, services/rag_service.py, services/dify_service.py
- services/rag_service.py → config/settings.py, utils/session_manager.py
- services/dify_service.py → config/settings.py
- utils/session_manager.py → config/settings.py

### Testing Strategy

**单元测试（建议添加）：**
- config/settings.py 模块：测试配置加载、环境切换、默认值
- utils/session_manager.py 模块：测试会话创建、查询、过期清理
- services/rag_service.py 模块：模拟 RAG 服务响应测试流式处理
- services/dify_service.py 模块：模拟 Dify 服务响应测试流式处理

**集成测试：**
- 测试所有16个 API 端点的正常流程
- 测试环境切换功能
- 测试会话管理完整生命周期

**手动测试步骤：**
1. 配置测试：
   - 设置 active_env: development
   - 运行应用并验证加载 .env.development
   - 设置 active_env: production
   - 运行应用并验证加载 .env.production

2. 功能测试：
   - 运行 test.py 脚本，验证流式响应
   - 运行 test_client.py 脚本，验证所有端点
   - 测试会话创建、查询、删除功能
   - 测试健康检查接口

3. 压力测试（可选）：
   - 多用户并发会话创建
   - 长时间流式响应连接保持
   - 会话过期自动清理验证

### Notes

**高风险项（预-mortem分析）：**
1. 环境切换配置错误：如果 active_env 设置错误或对应 .env 文件缺失，应用将无法启动。需要明确的错误提示。
2. 模块导入循环：src 目录结构复杂，需要注意避免循环导入。建议在函数内导入而非文件顶部。
3. 配置合并逻辑：.env 和 YAML 配置合并时可能出现冲突，需要明确定义优先级（.env 优先）。
4. 会话管理迁移：SessionManager 依赖 settings，重构后需要确保从正确的模块导入配置。

**已知限制：**
- 会话管理仍基于内存，应用重启后会话丢失（不在本次重构范围内）
- 无单元测试框架，需要手动验证功能（不在本次重构范围内）
- CHAT_IDS 字典硬编码在 YAML 中，未来可考虑数据库化

**未来考虑（超出范围但值得注意）：**
- 添加单元测试框架（pytest）
- 实现会话持久化（Redis 或数据库）
- CHAT_IDS 动态加载（从数据库或配置中心）
- 添加日志配置到 YAML 文件
-当前环境自动检测（通过环境变量 DJANGO_SETTINGS_MODULE 或类似机制）

