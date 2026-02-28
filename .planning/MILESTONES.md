# Milestones

## v1.2 Integration Testing for CI/CD (In Progress: 2026-02-28)

**Phases planned:** 3 phases (9-11), 3 plans

**Goal:** 设计集成测试套件，使用 .venv 环境连接外部真实环境，验证接口连通性，支持 CI/CD 自动化测试。

**Key features:**
- 外部服务连通性测试（AI API、向量库、数据库）
- API E2E 测试（/api/general 含意图分类链路）
- 测试配置与环境变量分离
- CI/CD 流水线集成（GitHub Actions）

---

## v1.1 Intent Classification Optimization (Shipped: 2026-02-28)

**Phases completed:** 3 phases, 5 plans, 0 tasks

**Key accomplishments:**
1. 实现基于 LLM 的粗粒度意图分类服务（Type1/Type2/Type3）
2. 完成分类驱动检索：根据分类结果过滤向量库，减少语义混淆
3. 实现完善的降级机制：超时/错误/无效结果时自动降级到全量检索
4. 补充 E2E 测试：9 个测试用例覆盖 3 种意图类型，Excel 数据集支持维护
5. 配置集成：支持 `intent_classification` 配置块，环境变量可覆盖

---

## v1.0 Query Normalization (Shipped: 2026-02-28)

**Phases completed:** 4 phases, 5 plans, 3 tasks

**Key accomplishments:**
- (none recorded)

---
