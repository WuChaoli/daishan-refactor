# Requirements: Rag Stream Intent Classification Optimization

**Defined:** 2026-02-28
**Core Value:** 用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。

## v1 Requirements

### Classification Service

- [x] **CLS-01**: 系统在意图识别前先进行粗粒度分类（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）。
- [x] **CLS-02**: 复用现有 `QueryChat` 工具实现分类逻辑，配置专门的分类 prompt。
- [ ] **CLS-03**: 分类后，仅在对应类型的向量库中检索具体问题。
- [ ] **CLS-04**: 分类失败或返回无效结果时，降级到现有向量检索流程。

### Configuration

- [x] **CFG-03**: 支持 `intent_classification` 配置块，包含启用开关、模型参数、阈值设置。
- [x] **CFG-04**: 环境变量可以覆盖分类配置。

### Testing

- [ ] **TEST-03**: 单测覆盖分类成功路径（0/1/2/3 不同类型）。
- [ ] **TEST-04**: 单测覆盖分类失败降级路径。
- [x] **TEST-05**: 集成测试验证两阶段识别流程完整可用。

## v2 Requirements

(未来待定义)

## Out of Scope

| Feature | Reason |
|---------|--------|
| 训练专用意图分类模型 | 复用 LLM 足够，避免模型维护成本 |
| 重构所有现有向量检索逻辑 | 本次仅新增分类层，保持现有检索逻辑不变 |
| 改造 Ragflow 接口 | 在 rag_stream 内部实现分类，不依赖远端改造 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLS-01 | Phase 5 | Complete |
| CLS-02 | Phase 5 | Complete |
| CLS-03 | Phase 6 | Pending |
| CLS-04 | Phase 5 | Pending |
| CFG-03 | Phase 5 | Complete |
| CFG-04 | Phase 5 | Complete |
| TEST-03 | Phase 7 | Pending |
| TEST-04 | Phase 7 | Pending |
| TEST-05 | Phase 7 | Complete |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9/9 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after roadmap creation*
