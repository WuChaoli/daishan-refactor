# LogTracer 实施计划（任务级）

## 基础信息

- `context_id`: `2026-02-11_logtracer-init`
- `项目路径`: `src/LogTracer/`
- `本次目标`: 生成可执行重构计划（不改原项目）

## Phase 0：需求与上下文建档

1. 创建上下文目录与文档骨架
2. 完成 `requirement.md`
3. 完成 `design.md`
4. 完成 `plan.md`
5. 更新 `.contexts-index.json`
6. 验收：索引可检索、元数据完整

## Phase 1：项目骨架与配置体系

7. 创建目录：`src/LogTracer/src/`、`src/LogTracer/test/`、`src/LogTracer/scripts/`
8. 设计配置优先级加载器（`.env > yaml > json`）
9. 定义配置模型与校验规则
10. 提供配置模板与示例环境变量
11. 规划 CLI 入口（run/check/generate-demo-trace）
12. 验收：配置覆盖关系可测、异常输入可报错

## Phase 2：Trace 核心能力

13. 初始化 TracerProvider 与 Resource
14. 实现 `@trace_span`（sync）
15. 实现 `@trace_span`（async）
16. 统一 span 命名与属性规范
17. 实现异常追踪（record_exception + status）
18. 实现采样策略与开关
19. 增加 trace context 工具函数
20. 验收：调用链父子关系与耗时正确

## Phase 3：I/O 观测能力

21. 实现 `@trace_io` 事件模型（enter/exit/error）
22. 实现入参摘要器
23. 实现出参摘要器
24. 实现脱敏规则引擎（键名+正则）
25. 实现长度截断与循环引用保护
26. 增加字段白名单/黑名单配置
27. 验收：敏感信息不明文泄露

## Phase 4：OTel 可视化接入

28. 对接 OTLP exporter
29. 制定 Jaeger 查询规范（service/operation/error）
30. 编写示例链路生成脚本
31. 形成本地运行手册（基于 `./.venv`）
32. 验收：Jaeger 中可视化链路可复现

## Phase 5：多 worker 隔离

33. 设计并实现 `global.{pid}.log` 输出策略
34. 设计并实现 `error.{pid}.log` 输出策略
35. 每条日志注入 `pid/worker_id/trace_id/span_id`
36. 增加跨 worker trace 聚合查询示例
37. 验收：并发下无串线，按 trace 可回放

## Phase 6：异常链路与诊断

38. 定义异常分类与错误码映射
39. 记录异常链（type/message/cause/stack）
40. 定义慢调用与超时观测指标
41. 验收：错误可从 trace 反查日志、从日志反查 trace

## Phase 7：测试与质量门

42. 单元测试：配置、装饰器、摘要、脱敏
43. 集成测试：sync/async/异常/采样
44. 并发测试：多协程/多 worker
45. 回归测试：配置优先级与兼容
46. 覆盖率门禁：关键模块 80%+
47. 验收：测试报告可复现、失败路径清晰

## Phase 8：交接与归档

48. 输出 `implementation.md`
49. 输出 `verification.md`
50. 完成归档：`docs/archive/`（任务完成后）

## 里程碑

- M1：Phase 0-1 完成（文档与骨架冻结）
- M2：Phase 2-4 完成（链路与可视化跑通）
- M3：Phase 5-7 完成（并发稳定 + 质量门达标）
- M4：Phase 8 完成（可归档交付）

