---
phase: 06-分类驱动检索
plan: 01
subsystem: intent-service
tags: [classification, retrieval, tdd, intent-service]

requires:
  - 05-意图分类基础

provides:
  - classification-driven-retrieval
  - confidence-threshold-filtering
  - fallback-mechanism

affects:
  - src/rag_stream/src/services/intent_service/intent_service.py
  - src/rag_stream/src/services/intent_service/base_intent_service.py
  - src/rag_stream/config.yaml

tech-stack:
  added: []
  patterns:
    - dataclasses.replace for immutable updates
    - Strategy pattern for filtering logic

key-files:
  created:
    - src/rag_stream/tests/test_intent_service_classification.py
  modified:
    - src/rag_stream/src/services/intent_service/intent_service.py
    - src/rag_stream/src/services/intent_service/base_intent_service.py
    - src/rag_stream/config.yaml

decisions:
  - Use dataclasses.replace for immutable settings update
  - Keep backward compatibility with optional text_input parameter
  - Defensive programming: return full mapping when no matching database

metrics:
  duration: 15
  completed-date: 2026-02-28
  tests-added: 8
  tests-passing: 8
---

# Phase 06 Plan 01: Classification-Driven Retrieval Summary

## One-Liner
实现两阶段识别机制：粗分类后仅在对应类型的向量库中检索，解决语义混淆问题

## What Was Built

### 核心功能
1. **置信度阈值配置**: 将 `confidence_threshold` 从 0.5 更新为 0.7
2. **分类驱动检索**: 在 `_load_process_settings` 中集成分类器调用
3. **智能过滤逻辑**:
   - 置信度 >= 0.7: 仅检索对应类型的向量库
   - 置信度 < 0.7: 执行全量检索（向后兼容）
   - 降级时: 执行全量检索并记录 marker
4. **Marker 日志**: 记录降级和低置信度 fallback 场景

### 代码变更

#### src/rag_stream/config.yaml
```yaml
intent_classification:
  confidence_threshold: 0.7  # 从 0.5 更新
```

#### src/rag_stream/src/services/intent_service/intent_service.py
- 添加 `dataclasses` 导入
- 修改 `_load_process_settings(text_input: Optional[str] = None)`
- 实现分类调用和 database_mapping 过滤逻辑

#### src/rag_stream/src/services/intent_service/base_intent_service.py
- 更新抽象方法签名以支持 `text_input` 参数
- 修改 `process_query` 以传递 `text_input`

#### src/rag_stream/tests/test_intent_service_classification.py (新建)
- 8 个测试用例覆盖所有场景

## Test Coverage

| Test | Scenario | Status |
|------|----------|--------|
| test_high_confidence_filters_database_mapping | 置信度 0.85 >= 0.7，过滤为单库 | PASS |
| test_low_confidence_returns_full_mapping | 置信度 0.5 < 0.7，全量检索 | PASS |
| test_degraded_classification_returns_full_mapping | 降级时全量检索 + marker | PASS |
| test_disabled_classifier_returns_full_mapping | 分类器 None 时全量检索 | PASS |
| test_confidence_threshold_respected | 置信度 0.7 == 阈值，应用过滤 | PASS |
| test_type_id_mapping_correctness | type_id=3 映射正确性 | PASS |
| test_no_text_input_returns_full_mapping | 无输入时向后兼容 | PASS |
| test_no_matching_database_returns_full_mapping | 无匹配库时防御性处理 | PASS |

## Deviations from Plan

无偏差 - 计划按预期执行

## Verification Results

- [x] 配置验证: confidence_threshold 值为 0.7
- [x] 测试覆盖验证: pytest 运行通过，覆盖 8 个测试场景
- [x] 分类调用验证: grep 搜索 classify() 调用点，确认在 _load_process_settings 中
- [x] 过滤逻辑验证: 使用字典推导式和 dataclasses.replace
- [x] Marker 验证: 搜索 "classifier.degraded_fallback" 和 "classifier.low_confidence_fallback" 标记
- [x] 向后兼容验证: 未启用分类时，database_mapping 保持完整

## Commits

| Commit | Message | Files |
|--------|---------|-------|
| 715c14a | chore(06-01): update confidence_threshold to 0.7 | config.yaml |
| ab3da45 | test(06-01): add classification-driven retrieval tests (RED) | test_intent_service_classification.py |
| 684a3d8 | feat(06-01): implement classification-driven retrieval logic | intent_service.py, base_intent_service.py |

## Self-Check: PASSED

- [x] 所有测试通过 (8/8)
- [x] 配置文件已更新
- [x] 代码实现符合 TDD 流程
- [x] 向后兼容保持
- [x] Marker 日志已添加
