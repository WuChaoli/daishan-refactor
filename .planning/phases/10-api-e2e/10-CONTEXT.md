# Phase 10: API E2E 测试 - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

创建完整的 `/api/general` 接口端到端测试套件，支持在 CI/CD 环境中运行。测试需在 Docker Compose 环境中自动启动服务，通过环境变量注入配置，验证完整 API 流程。区别于 Phase 08 的本地真实环境测试，本阶段侧重配置分离和 CI/CD 集成能力。

</domain>

<decisions>
## Implementation Decisions

### 测试运行模式
- Docker Compose 内运行测试（开发环境和 CI 一致）
- 使用真实外部服务连接（Dify、RAGFlow、数据库）
- 不采用 mock 方案，确保测试真实性
- 测试脚本自动管理服务的启动和关闭

### 配置注入策略
- 所有配置通过环境变量注入（敏感信息不外泄）
- 遵循 12-factor app 配置原则
- 支持 `.env` 文件加载（开发便利）
- 环境变量优先级高于配置文件

### 测试报告
- 生成 JSON 格式测试报告
- 包含：测试通过率、响应时间、分类结果、错误详情
- 报告可在 CI 中作为 artifact 保存

### 服务生命周期
- 测试脚本自动启动 uvicorn 服务
- 测试完成后自动优雅关闭服务
- 支持健康检查确认服务就绪
- 超时机制防止测试挂起

### 测试数据
- 复用 Phase 08 的 Excel 测试数据集
- 支持环境变量过滤测试用例（如只测试特定类型）
- 测试数据随代码版本管理

### Claude's Discretion
- 具体的 Docker Compose 服务编排细节
- 测试并行化策略（串行 vs 并发）
- 日志输出详细程度控制
- 测试超时具体时间值

</decisions>

<specifics>
## Specific Ideas

- Phase 08 的 `test_api_general_e2e.py` 可作为基础，但需要解耦本地开发假设
- 测试应可在 GitHub Actions 等标准 CI 环境中直接运行
- 失败时提供清晰的诊断信息（类似 Phase 09 的连通性测试模式）
- 考虑添加测试标记（pytest markers）支持选择性运行

</specifics>

<deferred>
## Deferred Ideas

- JUnit XML 格式报告支持 — 如 CI 系统需要可后续添加
- 完全 Mock 模式支持 — 未来可考虑添加以支持无外部服务环境
- 性能基准测试 — 属于 Phase 14 监控范畴

</deferred>

---

*Phase: 10-api-e2e*
*Context gathered: 2026-02-28*
