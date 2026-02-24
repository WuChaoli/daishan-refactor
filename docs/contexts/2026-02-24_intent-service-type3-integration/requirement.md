# 需求文档

## 背景

需要为 `src/rag_stream/src/services/intent_service/intent_service.py` 构建一组集成测试，覆盖一批园区相关问句的意图分类结果校验。

## 需求说明

1. 测试对象为 `IntentService.process_query`。
2. 测试链路要求为完整链路，不使用 mock。
3. 指定问句全部期望返回意图类别 `3`。
4. 断言策略为严格全等（实际类别必须等于 `3`）。
5. `某企业/某月` 类问句保持原句，不替换为具体参数。
6. 测试文件需归档在 `test/YYYY-MM-DD_<task>/` 目录。

## 验收标准

1. 存在可执行的 pytest 测试文件，包含全部指定问句。
2. 每条问句均有 `type == 3` 的断言。
3. 测试使用真实 `RagflowClient` 与 `IntentService` 组成的完整流程。
4. 文档上下文已登记到 `docs/contexts/.contexts-index.json`。
