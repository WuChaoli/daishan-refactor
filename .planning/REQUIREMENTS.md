# Requirements: Rag Stream Query Normalization

**Defined:** 2026-02-28
**Core Value:** 用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。

## v1.2 Requirements

### Integration Testing Framework

- [x] **INT-01**: 集成测试框架支持 .venv 环境隔离运行
  - 测试脚本自动检测并激活 .venv 环境
  - 支持通过环境变量覆盖默认 Python 解释器路径
  - 测试失败时提供清晰的虚拟环境诊断信息

- [x] **INT-02**: 外部 AI API 服务连通性测试
  - 验证 QueryChat 工具能成功调用 AI API
  - 测试 API 认证是否有效
  - 超时和错误响应处理验证

- [x] **INT-03**: 向量库服务连通性测试
  - 验证向量库连接配置正确
  - 测试基础查询操作可正常执行
  - 验证所有配置的向量库均可访问

- [x] **INT-04**: 数据库服务连通性测试
  - 验证达梦数据库连接正常
  - 测试基础 SQL 查询可执行
  - 验证连接池配置有效

### API E2E Testing

- [ ] **INT-05**: /api/general 接口 E2E 测试（含意图分类链路）
  - 测试完整请求-响应流程
  - 验证意图分类结果符合预期
  - 验证降级机制在故障时正常工作
  - 测试响应时间是否在可接受范围内

- [ ] **INT-06**: 测试配置与环境变量分离（支持 CI/CD 注入）
  - 支持通过环境变量注入敏感配置（API 密钥、数据库密码）
  - 支持通过配置文件注入非敏感配置
  - CI/CD 环境特定的配置覆盖机制

### Test Reporting & CI/CD

- [ ] **INT-07**: 测试报告输出（JUnit/XML 格式支持）
  - pytest 生成 JUnit XML 格式报告
  - 测试摘要包含通过率、失败详情、执行时间
  - 支持 HTML 报告生成

- [ ] **INT-08**: CI/CD 流水线配置文件（GitHub Actions/GitLab CI）
  - 提供 GitHub Actions 工作流配置
  - 支持手动触发和定时触发
  - 测试失败时通知机制
  - 流水线步骤：安装依赖 → 连通性测试 → E2E 测试 → 报告生成

## Historical Requirements

### v1.1 Intent Classification Optimization (Completed)

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLS-01 | Phase 5 | Complete |
| CLS-02 | Phase 5 | Complete |
| CLS-03 | Phase 6 | Complete |
| CLS-04 | Phase 5 | Complete |
| CLS-05 | Phase 7 | Complete |
| CFG-03 | Phase 5 | Complete |
| CFG-04 | Phase 5 | Complete |
| TEST-03 | Phase 7 | Complete |
| TEST-04 | Phase 7 | Complete |
| TEST-05 | Phase 8 | Complete |

### v1.0 Query Normalization (Completed)

- QUERY-01 ~ QUERY-05: All Complete

## v2 Requirements

Deferred to future release.

### Performance Testing

- **PERF-01**: API 响应时间基准测试
- **PERF-02**: 并发请求处理能力测试
- **PERF-03**: 内存和 CPU 使用率监控

### Multi-Environment Testing

- **MULTI-01**: 支持多环境配置（开发/测试/生产）
- **MULTI-02**: 环境特定的测试数据集

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mock/Stub 服务 | 本里程碑聚焦真实环境连通性验证 |
| 安全渗透测试 | 属于安全审计范畴，非功能测试 |
| 混沌工程测试 | 复杂度高， deferred to v2+ |
| 可视化测试报告平台 | 当前文本/XML 报告足够满足 CI/CD 需求 |
| 训练专用意图分类模型 | 复用 LLM 足够，避免模型维护成本 |
| 重构所有现有向量检索逻辑 | 保持现有检索逻辑不变 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase 9 | Complete |
| INT-02 | Phase 9 | Complete |
| INT-03 | Phase 9 | Complete |
| INT-04 | Phase 9 | Complete |
| INT-05 | Phase 10 | Pending |
| INT-06 | Phase 10 | Pending |
| INT-07 | Phase 11 | Pending |
| INT-08 | Phase 11 | Pending |

**Coverage:**
- v1.2 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after v1.2 requirements defined*
