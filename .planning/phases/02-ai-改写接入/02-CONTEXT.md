# Phase 2: AI 改写接入 - Context

**Gathered:** 2025-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

实现聊天工具并在 `replace_economic_zone` 中调用，达到"删除企业名、保留原句"。AI 异常时返回原 query，不再使用旧正则统一替换。改写输出为纯文本句子。

本阶段不涉及：多 AI 提供商支持、配置热更新、流式响应。

</domain>

<decisions>
## Implementation Decisions

### 聊天工具接口
- **调用方式**：异步函数 `async def rewrite_query(query: str, config: QueryChatConfig) -> str`
- **返回类型**：纯字符串，直接返回改写后的句子
- **参数设计**：显式传递 `query` 和 `config` 对象，便于测试和灵活控制
- **文件位置**：`src/rag_stream/src/utils/query_chat.py`（遵循 Roadmap 建议）

### 错误回退粒度
- **API 失败**：立即回退原句，不区分错误类型（网络超时、API 错误等统一处理）
- **内容异常**：AI 返回格式不符合预期（JSON、空字符串、包含指令等）时回退原句
- **日志级别**：WARNING — 便于运维人员监控回退情况
- **统计指标**：通过 marker 记录成功/失败/回退次数，便于监控成功率

### Claude's Discretion
- 具体的 HTTP 客户端选择（httpx / aiohttp / requests）
- AI 请求的超时时间和重试策略（虽然决策是"立即回退"，但实现时可考虑单次重试）
- 内容验证的具体规则（如何定义"格式不符合预期"）
- marker 的具体命名和标签设计

</decisions>

<specifics>
## Specific Ideas

- 工具函数应遵循项目现有的异步模式（与 `replace_economic_zone` 保持一致）
- 配置通过 `QueryChatConfig` 对象传递，便于单元测试时注入 mock 配置
- 需要记录指标：成功次数、API 失败次数、内容异常次数、总调用次数

</specifics>

<deferred>
## Deferred Ideas

- 多 AI 提供商支持（OpenAI、Anthropic 等）—— 未来扩展
- 流式响应支持 —— 当前阶段不需要
- 智能重试策略（指数退避、熔断等）—— 当前阶段明确"立即回退"
- 内容缓存机制 —— Phase 3 后评估

</deferred>

---

*Phase: 02-ai-改写接入*
*Context gathered: 2025-02-28*
