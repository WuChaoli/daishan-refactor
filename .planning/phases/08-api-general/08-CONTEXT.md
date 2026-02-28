# Phase 8: 增加真实环境测试，测试真实调用/api/general接口，测试接口是否通畅、记录过程中的意图分类过程 - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

创建端到端真实环境测试，验证 `/api/general` 接口的完整可用性。测试将本地启动服务，真实调用接口，记录意图分类过程，并验证流式响应。

</domain>

<decisions>
## Implementation Decisions

### 测试执行方式
- 本地启动服务后执行测试（非远程连接）
- 使用真实外部依赖（Dify、RAGFlow、DaiShanSQL），不 mock
- 服务启动作为测试前置步骤

### 意图分类记录验证
- 验证 log-marker 输出中的分类结果
- 检查 marker 日志中 "意图分类" 相关标记
- 记录分类类型（Type1/Type2/Type3）和置信度

### 测试数据集
- 创建 Excel 文件作为验证集（`.xlsx` 格式）
- 初始包含覆盖 3 种意图类型的测试问题
- 文件位置：`src/rag_stream/tests/data/intent_test_cases.xlsx`
- 后续支持手动添加新测试用例
- Excel 列结构：问题文本、期望意图类型、备注

### 测试通过标准
- HTTP 状态码 200
- 流式传输有实际内容返回（非空）
- 完整接收 SSE 流式响应并记录

### 测试输出
- 记录每次测试的请求/响应
- 保存意图分类过程日志
- 生成测试报告（通过/失败状态、响应时间、分类结果）

</decisions>

<specifics>
## Specific Ideas

- Excel 验证集便于非技术人员维护测试用例
- 流式响应需要完整接收并验证内容非空
- 意图分类过程通过现有的 marker 日志系统追踪

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `test_chat_general_service.py`: 已有 20+ 个单元测试，包含意图服务测试模式
- `log_manager_import`: marker/entry_trace 系统已集成，用于记录分类过程
- `chat_routes.py:/api/general`: 接口已实现，调用 `handle_chat_general`

### Established Patterns
- 测试使用 pytest 框架
- 日志通过 marker() 函数记录，可用于追踪
- SSE 流式响应使用 `dict_to_stream_generator` 生成

### Integration Points
- 测试需启动 FastAPI 应用（`src/rag_stream/main.py`）
- 接口依赖 `intent_service`（从 `app.state` 获取）
- 外部调用：Dify API、RAGFlow API、DaiShanSQL Server

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-api-general*
*Context gathered: 2026-02-28*
