# Phase 2: AI 改写接入 - Research

**Researched:** 2025-02-28
**Status:** Ready for planning

## 现有实现分析

### QueryChat 工具现状

文件：`src/rag_stream/src/utils/query_chat.py`

已实现功能：
- `QueryChat` 类封装 OpenAI 客户端
- `rewrite_query_remove_company(query: str) -> str` 同步函数
- 配置验证（base_url、api_key、model）
- 错误处理和日志记录（marker）
- 响应内容提取（支持多种格式）

### Service 层集成现状

文件：`src/rag_stream/src/services/chat_general_service.py`

已实现功能：
- `replace_economic_zone` 已是异步函数
- 配置检查（enabled、api_key、base_url）
- 降级逻辑（配置无效时返回原 query）
- 通过 `asyncio.to_thread` 调用同步工具函数
- 异常捕获和日志记录

### 与 CONTEXT.md 的对比

| 要求 | 现状 | 差距 |
|------|------|------|
| 异步接口 `async def rewrite_query` | 只有同步 `rewrite_query_remove_company` | 需要添加异步包装 |
| 显式传递 config 参数 | 使用全局 settings | 需要支持注入 config |
| 返回字符串 | 已实现 | ✅ 符合 |
| 统计指标 | 有基本 marker，但缺少成功/失败计数 | 需要增强 |

## 技术方案

### 1. 异步接口设计

在 `query_chat.py` 中添加：
```python
async def rewrite_query(query: str, config: QueryChatConfig) -> str:
    """异步改写 query，删除企业名称。
    
    Args:
        query: 原始查询字符串
        config: QueryChat 配置对象
        
    Returns:
        改写后的字符串，失败时返回原 query
    """
    # 实现：使用 asyncio.to_thread 包装现有逻辑
    # 或者重构 QueryChat 支持异步 HTTP 客户端
```

### 2. 统计指标增强

需要记录的指标：
- `query_chat.total_calls` - 总调用次数
- `query_chat.success` - 成功次数
- `query_chat.api_error` - API 错误次数
- `query_chat.empty_response` - 空响应次数
- `query_chat.content_invalid` - 内容无效次数（新增）

### 3. 内容验证规则

根据 CONTEXT.md，需要检测"内容异常"：
- 空字符串
- JSON 格式（AI 错误返回 JSON）
- 包含指令性文字（"请"、"应该"、"建议"等）
- 多行文本（可能包含解释）

## 文件变更清单

1. **修改**: `src/rag_stream/src/utils/query_chat.py`
   - 添加 `rewrite_query` 异步函数
   - 添加内容验证逻辑
   - 增强统计指标
   - 保持向后兼容（保留原有同步函数）

2. **可选修改**: `src/rag_stream/src/services/chat_general_service.py`
   - 改用新的异步接口（可选，现有代码已可用）

## 依赖关系

- 依赖 Phase 1 的 `QueryChatConfig`（包含 enabled 字段）
- 依赖现有的 `marker` 日志系统
- 无新增外部依赖

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 异步/同步混用导致性能问题 | 使用 `asyncio.to_thread` 或在同步函数内部处理 |
| 内容验证规则过于严格 | 先实现基础规则，后续根据实际数据调优 |
| 向后兼容性问题 | 保留原有 `rewrite_query_remove_company` 函数 |

## 建议的计划结构

### Wave 1: 异步接口实现
- 任务 1: 添加 `rewrite_query` 异步函数
- 任务 2: 添加内容验证逻辑

### Wave 2: 统计指标增强
- 任务 3: 增强 marker 记录，添加统计指标
- 任务 4: 验证完整流程

---

*Phase: 02-ai-改写接入*  
*Research completed: 2025-02-28*
