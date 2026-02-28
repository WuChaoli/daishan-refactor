# Rag Stream Query Normalization

## What This Is

本项目是在现有 `rag_stream` 服务上增加一条 AI 改写链路：在意图识别前先对用户 query 进行企业名称清理。目标是通过 LLM 仅删除企业名称、保留原句语义和结构，从而减少企业名对意图识别与后续检索的噪声。

## Core Value

用户输入中的企业名可以被稳定移除，同时保留原句其余内容不变。

## Current State: v1.1 Shipped (2026-02-28)

**Shipped:** 两阶段意图识别机制，先用 LLM 进行粗粒度分类，再在对应向量库中精检索，解决语义混淆导致分类不准确的问题。

**Next Milestone:** v1.2 Integration Testing for CI/CD

## Current Milestone: v1.2 Integration Testing for CI/CD (In Progress)

**Goal:** 设计集成测试套件，使用 .venv 环境连接外部真实环境，验证接口连通性，支持 CI/CD 自动化测试。

**Target features:**
- 集成测试框架设计（支持 .venv 环境隔离）
- 外部服务连通性测试（AI API、向量库、数据库）
- 核心接口 E2E 测试（/api/general 等）
- CI/CD 流水线集成配置
- 测试数据与环境配置分离

## Next Milestone: v1.3 Production Build and Deployment Scripts

**Goal:** 创建生产环境的构建和运行脚本，支持自动化部署和运维。

**Target features:**
- Docker 容器化配置（Dockerfile + docker-compose）
- 生产环境构建脚本（依赖安装、静态资源构建）
- 服务启动脚本（支持 graceful shutdown）
- 环境配置管理（生产环境变量模板）
- 健康检查和监控端点
- 日志轮转和清理机制
- 数据库迁移脚本集成

## Requirements

### Validated

- ✓ `rag_stream` 已提供通用问答入口与意图识别流程（`/api/general` + `handle_chat_general`）— existing
- ✓ 项目已具备 OpenAI 兼容调用依赖（`openai`）和 DaiShanSQL 参考实现 — existing
- ✓ `rag_stream` 已具备 `config.yaml + .env` 配置加载机制 — existing
- ✓ 新增 `rag_stream` 内部聊天工具（`src/rag_stream/src/utils/query_chat.py`），实现 OpenAI 兼容 chat 调用 — v1.0
- ✓ 在 `src/rag_stream/config.yaml` 配置该聊天工具参数，命名使用 `query_chat` 前缀（非 `openai`）— v1.0
- ✓ 在 `replace_economic_zone` 中调用 AI 删除企业名称并返回改写句 — v1.0
- ✓ AI 失败时返回原句，不再退回旧正则替换逻辑 — v1.0
- ✓ 补充单元测试和真实环境测试套件 — v1.0
- ✓ **CLS-01**: 系统在意图识别前先进行粗粒度分类（数据库/指令/固定问题）— v1.1
- ✓ **CLS-02**: 粗分类后，仅在对应类型的向量库中检索 — v1.1
- ✓ **CLS-03**: 复用现有 QueryChat 工具实现分类逻辑 — v1.1
- ✓ **CLS-04**: 分类失败时降级到现有检索流程 — v1.1
- ✓ **CLS-05**: 为新流程添加测试覆盖 — v1.1 (E2E测试)

### Active

- **INT-01**: 集成测试框架支持 .venv 环境隔离运行
- **INT-02**: 外部 AI API 服务连通性测试
- **INT-03**: 向量库服务连通性测试
- **INT-04**: 数据库服务连通性测试
- **INT-05**: /api/general 接口 E2E 测试（含意图分类链路）
- **INT-06**: 测试配置与环境变量分离（支持 CI/CD 注入）
- **INT-07**: 测试报告输出（JUnit/XML 格式支持）
- **INT-08**: CI/CD 流水线配置文件（GitHub Actions/GitLab CI）

### Out of Scope

- 性能测试与压力测试 — 属于性能里程碑，非连通性测试
- 多环境并行测试矩阵 — 当前仅支持单一真实环境
- Mock/Stub 服务 — 本里程碑聚焦真实环境连通性
- 安全渗透测试 — 属于安全审计范畴

## Context

### Current State (v1.1 Shipped 2026-02-28)

**Intent Classification Service:**
- `IntentClassifier`: 基于 LLM 的粗粒度意图分类
- `ClassificationResult`: 分类结果数据类（type_id, confidence, degraded）
- 配置驱动：`intent_classification.enabled` 开关控制
- 降级机制：超时/错误/无效结果时降级到全量检索

**Two-Stage Recognition:**
- Stage 1: LLM 粗分类（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）
- Stage 2: 根据分类结果过滤向量库，仅在对应库中检索
- 降级策略：分类失败时回退到全库检索

**Key Issue Resolved:**
- 案例：「XX企业的危化品类目」现在通过 LLM 分类为 Type2，只在数据库问题库检索
- 结果：避免跨库语义混淆，提高分类准确率

**Testing:**
- 14 个单元测试覆盖分类服务（成功/降级路径）
- E2E 测试：9 个测试用例覆盖 3 种意图类型
- Excel 测试数据集支持非技术人员维护

### Original Context

**Tech Stack:**
- Python 3.11+ with uv package manager
- OpenAI SDK for AI chat integration
- pytest + asyncio for testing
- 11,845 lines of Python code

**Architecture:**
- 新增 `QueryChat` 工具类 (`src/rag_stream/src/utils/query_chat.py`)
- 配置模型 `QueryChatConfig` 集成到现有 `settings` 体系
- 异步接口 `rewrite_query` 支持非阻塞调用
- 内容验证和统计指标集成

**Testing:**
- 4 个单元测试覆盖成功/失败路径
- 11 个真实环境测试用例（typical/complex/boundary）
- CLI 工具支持 (`scripts/test_real_env.py`)

**Known Issues:**
- 真实环境测试需要 AI API 密钥才能完整运行
- 测试数据集可进一步扩展边界情况

### Original Context

- 仓库是 brownfield Python monorepo，`rag_stream` 已有完整服务和测试基础。
- 现有 `replace_economic_zone` 使用正则统一替换"经开区/开发区"等词，不满足"仅删除企业名"的新需求。
- 参考实现位于 `src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`，但该实现与 `rag_stream` 配置体系不完全一致，需要按 `rag_stream` 的 `settings` 体系落地。

## Constraints

- **Tech stack**: 必须使用 Python + 现有 `openai` 依赖 — 保持与仓库一致。
- **Configuration**: 必须在 `src/rag_stream/config.yaml` 配置，且命名不要用 `openai` 前缀 — 用户明确要求。
- **Behavior**: AI 改写失败时必须返回原 query — 用户明确要求。
- **Scope**: 仅修改 `rag_stream` 相关代码与测试 — 避免影响其他子系统。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 在 `rag_stream` 内新增独立聊天工具而非直接复用 DaiShanSQL 模块 | 降低跨模块耦合，保持 `rag_stream` 自治 | ✓ Good — 模块独立，易于维护 |
| 企业名清理由正则改为 AI 改写主路径 | 需求要求"删除企业名且返回原句"，正则难覆盖 | ✓ Good — 满足需求，测试通过 |
| 失败兜底改为"原句返回" | 用户明确指定 B 策略 | ✓ Good — 主流程稳定，无中断风险 |
| 使用模式匹配验证 AI 输出而非精确匹配 | AI 输出有细微差异，模式验证更灵活 | ✓ Good — 适应 AI 不确定性 |
| dry-run 模式支持无 AI 环境测试 | 便于开发和 CI 环境验证 | ✓ Good — 开发体验良好 |
| 意图分类使用专用配置块 `intent_classification` | 与 `query_chat` 分离，独立控制 | ✓ Good — 可独立开关分类功能 |
| 分类驱动检索时创建新的 Settings 实例 | 保持不可变性，避免副作用 | ✓ Good — 代码清晰，易于测试 |
| 降级时返回 type_id=0 并标记 degraded | 明确区分正常/降级结果 | ✓ Good — 调用方可感知降级 |

---
*Last updated: 2026-02-28 after v1.3 milestone started*
