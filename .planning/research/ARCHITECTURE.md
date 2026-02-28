# Architecture Research

**Domain:** rag_stream 查询预处理改造
**Researched:** 2026-02-28
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌───────────────────────────────────────────────────────────┐
│ FastAPI Route Layer (`chat_routes`)                      │
├───────────────────────────────────────────────────────────┤
│ Service Layer (`chat_general_service`)                   │
│   - query normalization (new AI cleaning step)           │
│   - intent routing                                        │
├───────────────────────────────────────────────────────────┤
│ Integration Layer (`utils`)                               │
│   - query chat tool (new)                                 │
│   - ragflow client / dify clients / DaiShanSQL adapter    │
├───────────────────────────────────────────────────────────┤
│ Config Layer (`settings`)                                 │
│   - YAML + env override                                   │
└───────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `settings` | 提供 query 清洗配置 | Pydantic config model |
| `utils` 新聊天工具 | 发送 chat completion 并返回纯文本 | OpenAI SDK wrapper |
| `replace_economic_zone` | 在 intent 前做企业名清理 | 异步调用 + 回退策略 |

## Recommended Project Structure

```text
src/rag_stream/
├── config.yaml
├── src/
│   ├── config/settings.py
│   ├── services/chat_general_service.py
│   └── utils/
│       └── query_chat.py   # new
└── tests/
```

### Structure Rationale

- **`utils/query_chat.py`:** 将外部 LLM 调用从 service 中抽离，单一职责。
- **`settings.py`:** 统一配置入口，避免散落环境变量读取。

## Architectural Patterns

### Pattern 1: Adapter Wrapper

**What:** 在业务层与第三方 SDK 之间增加轻量适配层。  
**When to use:** 需要隐藏 SDK 参数细节并提供稳定接口。  
**Trade-offs:** 多一层抽象，但可测试性更高。

### Pattern 2: Fail-Open Fallback

**What:** 外部能力失败时返回原输入继续主流程。  
**When to use:** 预处理是增强而不是强依赖。  
**Trade-offs:** 可用性提高，但功能效果在异常时会下降。

## Data Flow

### Request Flow

```text
User Query
  -> handle_chat_general
    -> normalize query via query_chat tool
      -> cleaned query (or original query on failure)
        -> intent_service.process_query
          -> downstream routing
```

### Key Data Flows

1. **Normalization Flow:** 用户 query -> AI 清理企业名 -> 标准化 query。
2. **Fallback Flow:** AI 异常 -> 原 query 透传 -> 保证接口可用。

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 低并发 | 线程池调用足够 |
| 中并发 | 增加超时、重试与限流 |
| 高并发 | 引入缓存与异步客户端 |

## Anti-Patterns

### Anti-Pattern 1: 在 service 中直接组装 OpenAI 请求

**Why it's wrong:** 难测、难维护、配置分散。  
**Do this instead:** 使用独立 `utils` 适配器。

### Anti-Pattern 2: 失败后继续正则强改

**Why it's wrong:** 与需求冲突且可能误改语义。  
**Do this instead:** 失败直接返回原句。

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI-compatible endpoint | SDK chat completion | 参数来自 `config.yaml`/env |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `chat_general_service` ↔ `query_chat` | function call | 可 mock 测试 |
| `query_chat` ↔ `settings` | config object | 避免硬编码 |

## Sources

- `src/rag_stream/src/services/chat_general_service.py`
- `src/rag_stream/src/config/settings.py`
- `src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`

---
*Architecture research for: query normalization*
*Researched: 2026-02-28*
