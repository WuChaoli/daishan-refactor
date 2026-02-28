# Stack Research

**Domain:** 企业名称清理型 Query 预处理（brownfield rag_stream）
**Researched:** 2026-02-28
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | 服务与业务实现 | 与当前 monorepo 主运行时一致，改造成本最低 |
| FastAPI | 0.104.x | API 入口与请求链路 | 现有接口已稳定运行，改造只需下沉到 service 层 |
| OpenAI Python SDK | 2.x | 兼容 chat completions 调用 | 仓库已有依赖，且 DaiShanSQL 已有参考调用路径 |
| Pydantic v2 | 2.5.x | 配置模型与校验 | `settings.py` 既有配置体系，适合新增配置域 |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.x | 本地敏感配置加载 | 开发/测试环境需与 `.env` 对齐时 |
| pytest | 8.x | 行为回归测试 | 改造 `replace_economic_zone` 逻辑时必须验证 |
| unittest.mock | stdlib | 隔离外部 API 调用 | 单测中避免真实 LLM 网络请求 |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | 依赖与执行统一入口 | 项目治理要求强制使用 |
| gsd-tools | 规划文档提交与状态推进 | 与本次 `$gsd-new-project` 流程一致 |

## Installation

```bash
# 依赖已在仓库中声明，按锁文件同步
uv sync --frozen
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| LLM 删除企业名 | 正则规则硬编码 | 只在规则极少且格式完全稳定时 |
| settings 新配置域 | 直接复用 `settings.openai` | 仅当允许使用 openai 前缀命名时 |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| 在 `chat_general_service` 内写死 API Key/模型 | 安全与可维护性差 | 通过 `config.yaml + env override` 注入 |
| AI 失败后继续正则强改 | 与用户要求冲突，且可能误改语义 | 失败直接回退原句 |

## Stack Patterns by Variant

**If 网络可用且配置完整：**
- 使用 LLM 改写。
- 因为可按自然语言语义删除企业名。

**If 网络/配置异常：**
- 返回原 query。
- 因为需求指定失败不做正则替换。

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| openai>=2.15.0 | Python>=3.12 | 与根 `pyproject.toml` 一致 |
| fastapi==0.104.1 | pydantic==2.5.0 | 当前仓库锁定组合 |

## Sources

- 本仓库：`pyproject.toml`, `src/rag_stream/config.yaml`, `src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`
- 本仓库：`.planning/codebase/STACK.md`, `.planning/codebase/ARCHITECTURE.md`

---
*Stack research for: query normalization*
*Researched: 2026-02-28*
