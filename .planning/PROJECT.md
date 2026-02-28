# Rag Stream Query Normalization

## What This Is

本项目是在现有 `rag_stream` 服务上增加一条 AI 改写链路：在意图识别前先对用户 query 进行企业名称清理。目标是通过 LLM 仅删除企业名称、保留原句语义和结构，从而减少企业名对意图识别与后续检索的噪声。

## Core Value

用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。

## Requirements

### Validated

- ✓ `rag_stream` 已提供通用问答入口与意图识别流程（`/api/general` + `handle_chat_general`）— existing
- ✓ 项目已具备 OpenAI 兼容调用依赖（`openai`）和 DaiShanSQL 参考实现 — existing
- ✓ `rag_stream` 已具备 `config.yaml + .env` 配置加载机制 — existing

### Active

- [ ] 新增 `rag_stream` 内部聊天工具（放在 `src/rag_stream/src/utils`），实现 OpenAI 兼容 chat 调用。
- [ ] 在 `src/rag_stream/config.yaml` 配置该聊天工具参数，且配置命名不使用 `openai` 前缀。
- [ ] 在 `replace_economic_zone` 中改为调用 AI 删除企业名称并返回改写句。
- [ ] AI 失败时返回原句，不再退回旧正则替换逻辑。
- [ ] 为该改造补充可运行的最小测试验证。

### Out of Scope

- 全链路 Prompt 工程平台化（模板中心、策略路由）— 当前只解决企业名清理。
- 多模型供应商抽象（非 OpenAI 兼容客户端）— 当前只做单客户端实现。
- 对 `chat_general` 其他 type 路由逻辑的行为改造 — 本次仅改 query 预处理步骤。

## Context

- 仓库是 brownfield Python monorepo，`rag_stream` 已有完整服务和测试基础。
- 现有 `replace_economic_zone` 使用正则统一替换“经开区/开发区”等词，不满足“仅删除企业名”的新需求。
- 参考实现位于 `src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`，但该实现与 `rag_stream` 配置体系不完全一致，需要按 `rag_stream` 的 `settings` 体系落地。

## Constraints

- **Tech stack**: 必须使用 Python + 现有 `openai` 依赖 — 保持与仓库一致。
- **Configuration**: 必须在 `src/rag_stream/config.yaml` 配置，且命名不要用 `openai` 前缀 — 用户明确要求。
- **Behavior**: AI 改写失败时必须返回原 query — 用户明确要求。
- **Scope**: 仅修改 `rag_stream` 相关代码与测试 — 避免影响其他子系统。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 在 `rag_stream` 内新增独立聊天工具而非直接复用 DaiShanSQL 模块 | 降低跨模块耦合，保持 `rag_stream` 自治 | — Pending |
| 企业名清理由正则改为 AI 改写主路径 | 需求要求“删除企业名且返回原句”，正则难覆盖 | — Pending |
| 失败兜底改为“原句返回” | 用户明确指定 B 策略 | — Pending |

---
*Last updated: 2026-02-28 after initialization*
