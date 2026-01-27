---
title: '将 daishan-new 的意图识别接口集成到 daishan-master'
slug: 'intent-recognition-integration'
created: '2026-01-26 14:10:52'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
tech_stack:
  - Python 3.12
  - FastAPI
  - pydantic
  - pydantic-settings
  - RAGFlow SDK
  - Dify SDK
  - DaiShanSQL
files_to_modify:
  - rag_stream/src/routes/chat_routes.py
  - rag_stream/config.yaml
  - rag_stream/src/config/settings.py
code_patterns:
  - 使用 pydantic BaseModel 定义请求/响应模型
  - 使用 pydantic-settings 配置管理
  - 服务层与路由层分离 (services/ + routes/)
  - 流式响应使用 StreamingResponse 返回 SSE 格式
  - 日志使用 Python logging 模块
test_patterns: []
---

# Tech-Spec: 将 daishan-new 的意图识别接口集成到 daishan-master

**Created:** 2026-01-26 14:10:52

## Overview

### Problem Statement

当前 `daishan-master` 项目的 `/api/general` 接口使用简单的 Dify/RAG 切换逻辑。需要将 `daishan-new` 项目中更强大的意图识别系统完整集成过来，包括意图判断、多处理器路由（语义类、明确指令类、数据库查询类）、知识库查询等功能，以提供更智能和灵活的问答服务。

### Solution

从 `daishan-new` 复制意图识别相关代码（包括 `dify_sdk`、`ragflow_sdk`、`ragflow_client`、DaiShanSQL 等），在 `daishan-master` 中创建新的 `intent_service.py` 服务模块，适配 `LogManager` 和配置系统，完全替换 `/api/general` 接口的逻辑，实现基于 RAGFlow 的意图识别和多路由处理。

### Scope

**In Scope:**
- 复制 `dify_sdk` 和 `ragflow_sdk` 到 `/daishan-master/` 根目录
- 复制 `ragflow_client.py` 并适配到新项目
- 复制 DaiShanSQL 模块
- 创建 `rag_stream/src/services/intent_service.py` 业务服务
- 创建 `rag_stream/src/services/log_manager.py` 日志管理器（或适配现有）
- 在 `rag_stream/src/routes/chat_routes.py` 中完全替换 `chat_general` 函数
- 适配配置文件，合并现有配置与新配置
- 实现三个意图处理器：Type 0 (语义类)、Type 1 (明确指令类)、Type 2 (数据库查询类)
- 集成 Dify Chat 客户端（SQL 结果格式化、知识库查询等）

**Out of Scope:**
- 不修改 `/api/general` 以外的其他接口（如 `/api/laws`、`/api/standards` 等）
- 不修改现有的 RAG 服务逻辑
- 不修改前端调用代码
- 不修改 DaiShanSQL 的内部逻辑

## Context for Development

### Codebase Patterns

- **配置系统**: 使用 `pydantic-settings` + YAML 配置文件
  - `rag_stream/config.yaml` 主配置文件
  - `rag_stream/src/config/settings.py` 定义 Settings 类
  - 支持多环境 (development/production) 通过 `.env.{active_env}` 文件

- **请求/响应模型**: 使用 `pydantic BaseModel`
  - `rag_stream/src/models/schemas.py` 定义 ChatRequest, ChatResponse 等
  - 使用 Field 进行验证和描述

- **服务层架构**: 服务层与路由层分离
  - `rag_stream/src/services/` 存放业务逻辑
  - `rag_stream/src/routes/` 存放路由定义
  - 现有服务: `rag_service.py`, `dify_service.py`

- **流式响应**: 使用 FastAPI StreamingResponse 返回 SSE 格式
  - 事件格式: `data: {json_data}\n\n`
  - 支持 session_id, answer, flag, word_id, end 字段

- **日志系统**: Python logging 模块
  - 使用标准 logging 模块
  - 支持文件和控制台输出

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `~/codespace/daishan-new/src/api/routes.py` | 源意图识别接口实现 |
| `~/codespace/daishan-new/src/config.py` | 源配置管理器 |
| `~/codespace/daishan-new/src/log_manager.py` | 源日志管理器 |
| `~/codespace/daishan-new/src/models.py` | 源数据模型 |
| `~/codespace/daishan-new/src/intent_judgment.py` | 意图判断逻辑 |
| `~/codespace/daishan-new/src/ragflow_client.py` | RAGFlow 客户端适配器 |
| `~/codespace/daishan-new/src/dify_sdk/` | Dify SDK 完整实现 |
| `~/codespace/daishan-new/src/ragflow_sdk/` | RAGFlow SDK 实现 |
| `~/codespace/daishan-new/src/DaiShanSQL/` | DaiShanSQL 数据库查询模块 |
| `rag_stream/src/routes/chat_routes.py` | 目标路由文件（需修改） |
| `rag_stream/src/services/rag_service.py` | 现有 RAG 服务 |
| `rag_stream/src/services/dify_service.py` | 现有 Dify 服务 |
| `rag_stream/src/models/schemas.py` | 现有数据模型 |
| `rag_stream/src/config/settings.py` | 现有配置类 |

### Technical Decisions

1. **SDK 放置位置**: 将 `dify_sdk` 和 `ragflow_sdk` 复制到 `/daishan-master/` 根目录，作为通用 SDK 供其他服务使用

2. **服务层结构**:
   - 创建 `rag_stream/src/services/ragflow_client.py` - RAGFlow 客户端适配器
   - 创建 `rag_stream/src/services/config_manager.py` - 配置管理器（适配原 config.py）
   - 创建 `rag_stream/src/services/log_manager.py` - 日志管理器（适配原 log_manager.py）
   - 创建 `rag_stream/src/services/intent_service.py` - 意图识别服务（核心业务逻辑）

3. **配置合并策略**:
   - 在 `rag_stream/config.yaml` 中添加新的配置节:
     - `ragflow`: RAGFlow 配置（API Key、Base URL、database_mapping）
     - `intent`: 意图判断配置（similarity_threshold、top_k_per_database、default_type）
     - `logging`: 日志配置（log_dir、max_bytes、backup_count、total_size_limit）
   - 保持现有的 `environments` 配置结构

4. **模型适配**:
   - 在 `rag_stream/src/models/schemas.py` 中添加意图识别相关的模型:
     - `IntentRequest` (text_input, user_id)
     - `IntentResponse` (type, query, results)
     - `QueryResult` (question, similarity)

5. **接口替换策略**:
   - 完全替换 `chat_general` 函数逻辑
   - 新接口接收 `ChatRequest` 格式
   - 内部调用意图判断逻辑，根据 type 路由到不同处理器
   - 保持流式响应格式与现有接口兼容

## Implementation Plan

### Tasks

- [x] Task 1: 复制 SDK 到根目录
  - File: `/daishan-master/dify_sdk/`
  - Action: 从 `~/codespace/daishan-new/src/src/dify_sdk/` 复制整个目录到 `/daishan-master/`
  - Notes: 包括 `__init__.py`, `client.py`, `core/`, `http/`, `models/`, `parsers/` 等所有子目录

- [x] Task 2: 复制 RAGFlow SDK
  - File: `/daishan-master/ragflow_sdk/`
  - Action: 从 `~/codespace/daishan-new/src/src/ragflow_sdk/` 复制整个目录到 `/daishan-master/`
  - Notes: 包括 `__init__.py`, `config/`, `core/`, `http/`, `models/`, `parsers/`, `utils/` 等所有子目录

- [x] Task 3: 复制 DaiShanSQL 模块
  - File: `/daishan-master/D/aiShanSQL/`
  - Action: 从 `~/codespace/daishan-new/src/DaiShanSQL/` 复制整个目录到 `/daishan-master/`
  - Notes: 保持内部结构不变，仅修改导入路径

- [x] Task 4: 创建配置管理器
  - File: `rag_stream/src/services/config_manager.py`
  - Action: 创建配置管理器类，适配原 `config.py` 的逻辑
  - Notes: 使用 `pydantic-settings` 读取配置，提供 `Config` dataclass，包含 ragflow、intent、server、logging 配置

- [x] Task 5: 创建日志管理器
  - File: `rag_stream/src/services/log_manager.py`
  - Action: 创建日志管理器类，适配原 `log_manager.py` 的逻辑
  - Notes: 使用标准 logging 模块，实现分层日志（global/、functions/），支持文件轮转

- [x] Task 6: 创建 RAGFlow 客户端适配器
  - File: `rag_stream/src/services/ragflow_client.py`
  - Action: 创建 RAGFlow 客户端类，适配原 `ragflow_client.py` 的逻辑
  - Notes: 使用根目录的 `ragflow_sdk`，实现多知识库查询、相似度排序等功能

- [x] Task 7: 创建意图判断模块
  - File: `rag_stream/src/services/intent_judgment.py`
  - Action: 创建意图判断核心逻辑，复制 `intent_judgment.py` 的实现
  - Notes: 定义 `QueryResult` 和 `IntentResult` dataclass，实现意图判断函数

- [x] Task 8: 创建意图识别服务
  - File: `rag_stream/src/services/intent_service.py`
  - Action: 创建意图识别服务，包含三个意图处理器（Type 0/1/2）
  - Notes:
    - Type 0: 返回固定错误消息 "无效指令#@#@#"
    - Type 1: 处理明确指令，支持知识库查询（园区/企业/安全信息知识库）
    - Type 2: 集成 DaiShanSQL，执行 SQL 查询并格式化结果
    - 实现流式响应，使用 DaishanStreamingParser

- [x] Task 9: 扩展数据模型
  - File: `rag_stream/src/models/schemas.py`
  - Action: 添加意图识别相关的数据模型
  - Notes: 添加 `IntentRequest`, `IntentResponse`, `QueryResult`, `ErrorResponse` 模型

- [x] Task 10: 扩展配置文件
  - File: `rag_stream/config.yaml`
  - Action: 添加意图识别相关配置节
  - Notes:
    - `ragflow`: API Key、Base URL、database_mapping
    - `intent`: similarity_threshold、top_k_per_database、default_type
    - `logging`: log_dir、max_bytes、backup_count、total_size_limit

- [x] Task 11: 替换 chat_general 接口
  - File: `rag_stream/src/routes/chat_routes.py`
  - Action: 完全替换 `chat_general` 函数逻辑
  - Notes:
    - 接收 `ChatRequest`（将 question 映射为 text_input）
    - 调用意图判断服务，获取 intent type
    - 根据 type 路由到对应的处理器
    - 返回流式响应

- [x] Task 12: 更新设置类
  - File: `rag_stream/src/config/settings.py`
  - Action: 扩展 Settings 类，添加意图识别相关配置字段
  - Notes: 添加 RAGFLOW_API_KEY, RAGFLOW_BASE_URL, DATABASE_MAPPING 等字段

### Acceptance Criteria

- [ ] AC 1: Given 意图识别服务已部署，when 用户发送问题，then 系统正确识别意图类型并路由到对应处理器
  - 验证点: 测试语义类、明确指令类、数据库查询类三种场景

- [ ] AC 2: Given Type 0 意图，when 识别到语义类查询，then 返回固定错误消息 "无效指令#@#@#"
  - 验证点: 验证流式响应格式正确

- [ ] AC 3: Given Type 1 意图，when 识别到明确指令并包含 [knowledgebase:xxx] 标记，then 调用对应 Dify Chat 客户端查询知识库
  - 验证点: 测试园区知识库、企业知识库、安全信息知识库三种场景

- [ ] AC 4: Given Type 2 意图，when 识别到数据库查询，then 调用 DaiShanSQL 执行 SQL 并返回格式化结果
  - 验证点: 验证 SQL 查询成功，结果被正确格式化为自然语言

- [ ] AC 5: Given RAGFlow 服务不可用，when 意图识别失败，then 降级到默认类型并返回错误提示
  - 验证点: 模拟 RAGFlow 服务超时或失败场景

- [ ] AC 6: Given 配置文件包含 database_mapping，when 启动服务，then 正确加载所有知识库映射
  - 验证点: 验证 config_manager 正确解析 YAML 配置

- [ ] AC 7: Given 用户请求包含 user_id，when 处理请求，then 日志正确记录用户 ID 和请求详情
  - 验证点: 检查日志文件（functions/intent_service.log、global/error.log）

- [ ] AC 8: Given 流式响应已启用，when 返回结果，then 客户端正确接收 SSE 格式的事件流
  - 验证点: 验证 event: start、message、complete、end 事件正确发送

## Additional Context

### Dependencies

**外部依赖库**:
- pydantic: 请求/响应模型验证
- pydantic-settings: 配置管理
- PyYAML: 配置文件解析
- aiohttp: HTTP 客户端（用于 RAGFlow 和 Dify API 调用）
- FastAPI: Web 框架

**内部依赖**:
- `dify_sdk/`: Dify 工作流 API SDK（根目录）
- `ragflow_sdk/`: RAGFlow SDK（根目录）
- `DaiShanSQL/`: DaiShanSQL 数据库查询模块（根目录）

**服务依赖**:
- RAGFlow 服务: 意图识别需要 RAGFlow API 可用
- Dify Chat 服务: Type 1 处理器和 SQL 结果格式化需要 Dify Chat API 可用
- 数据库: Type 2 处理器需要 DaiShanSQL 配置的数据库连接

**配置依赖**:
- `rag_stream/config.yaml`: 主配置文件，需包含 RAGFlow、intent、logging 配置节
- 环境变量: 支持 `${VAR_NAME}` 和 `${VAR_NAME:-default}` 格式的环境变量引用

### Testing Strategy

**单元测试**:
- `tests/services/test_config_manager.py`: 配置管理器测试
  - 测试配置加载和验证
  - 测试 environment variable 展开功能
  - 测试 database_mapping 解析

- `tests/services/test_log_manager.py`: 日志管理器测试
  - 测试日志文件创建和轮转
  - 测试功能级日志器获取
  - 测试日志容量检查和清理

- `tests/services/test_intent_judgment.py`: 意图判断测试
  - 测试相似度阈值判断
  - 测试知识库映射
  - 测试降级策略（空结果、相似度不足、映射错误）

- `tests/services/test_intent_service.py`: 意图服务测试
  - 测试 Type 0 处理器
  - 测试 Type 1 处理器（知识库查询）
  - 测试 Type 2 处理器（SQL 查询）
  - 测试流式响应生成

**集成测试**:
- `tests/routes/test_chat_routes.py`: 路由集成测试
  - 测试 `/api/general` 接口
  - 测试意图识别路由
  - 测试流式响应
  - 测试错误处理

**手动测试步骤**:
1. **配置验证**: 检查查 `rag_stream/config.yaml` 包含所有必需的配置节
2. **SDK 导入**: 验证 `dify_sdk` 和 `ragflow_sdk` 可以从根目录正确导入
3. **意图识别测试**:
   - 发送语义类问题，验证返回 Type 0 和固定错误消息
   - 发送明确指令问题（包含知识库标记），验证返回 Type 1 和知识库查询结果
   - 发送数据库查询问题，验证返回 Type 2 和 SQL 查询结果
4. **降级测试**:
   - 停止 RAGFlow 服务，验证降级到默认类型
   - 停止 Dify Chat 服务，验证降级方案
5. **日志验证**: 检查日志文件正确创建（logs/global/、logs/functions/）
6. **流式响应验证**: 验证 SSE 事件流格式正确（event: start、message、complete、end）

### Notes

**高风险项**:
- **配置迁移**: 从 `daishan-new` 的 `config.yaml` 迁移到 `rag_stream/config.yaml`，确保所有配置项正确映射
- **SDK 路径适配**: 原代码使用 `from src.xxx` 导入，需改为使用根目录的 SDK（`from dify_sdk import ...`）
- **DaiShanSQL 集成**: 需要确保数据库连接配置正确，sys.path 动态添加可能影响其他模块
- **日志路径冲突**: 新的日志系统可能与现有日志系统冲突，需要确认日志目录隔离

**已知限制**:
- **流式响应兼容性**: 新意图识别使用 DaishanStreamingParser，需确保与现有前端流式处理兼容
- **会话管理**: 意图识别不使用现有的 session_manager，而是直接使用 user_id，可能导致会话状态不一致
- **配置热更新**: 配置文件修改后需要重启服务才能生效

**未来考虑**:
- **统一配置系统**: 考虑将所有配置统一到 `rag_stream/config.yaml`，使用单一的 `pydantic-settings` 体系
- **会话集成**: 未来可以考虑将意图识别与会话管理集成，实现多轮对话的意图跟踪
- **性能优化**: 考虑缓存意图识别结果，减少 RAGFlow 调用次数
