# Phase 4: 补充真实环境测试 - Context

**Gathered:** 2025-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

使用真实 AI 服务验证端到端链路，补充 mock 测试的不足。测试范围包括典型企业名改写、复杂句子结构、无企业名 query 和边界情况。通过 Python 代码手动触发测试，快速验证（< 30 秒），测试失败阻塞发布。

本阶段不涉及：自动化 CI/CD 集成、性能压测、多环境并行测试。

</domain>

<decisions>
## Implementation Decisions

### 测试范围与目标
- **核心目标**：验证端到端链路（从入口到 AI 返回）
- **测试场景**：典型企业名改写、复杂句子结构、无企业名 query、边界情况
- **测试粒度**：Service API 层 + HTTP 端点层
- **测试产出**：日志记录 + 断言验证

### 执行与集成
- **执行时机**：手动触发（避免频繁调用真实 AI 服务）
- **失败处理**：阻塞发布（测试失败时阻止部署）
- **执行时长**：快速（< 30 秒，仅测试典型场景）
- **触发方式**：通过 Python 代码执行（便于集成现有代码库）

### Claude's Discretion
- 具体的企业名测试数据集设计
- 断言验证的具体实现方式（完全匹配、包含检查、相似度阈值）
- 日志输出的详细程度和格式
- 测试脚本的具体文件位置和组织方式

</decisions>

<specifics>
## Specific Ideas

- 测试应验证 AI 改写后企业名确实被删除，且语义基本保留
- 边界情况包括：超长 query（> 200 字符）、空字符串、纯标点符号
- 失败时应有清晰的错误信息，便于定位问题
- 建议提供便捷的命令行入口，如 `python -m scripts.test_real_env`

</specifics>

<deferred>
## Deferred Ideas

- CI/CD 自动集成 — 当前阶段手动触发即可
- 性能基准测试 — 非本阶段重点
- 多 AI 提供商对比测试 — 未来扩展
- 混沌测试（模拟网络故障、超时等）— 超出当前范围

</deferred>

---

*Phase: 04-补充真实环境测试*
*Context gathered: 2025-02-28*
