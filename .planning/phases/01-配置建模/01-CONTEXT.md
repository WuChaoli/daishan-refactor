# Phase 1: 配置建模 - Context

**Gathered:** 2025-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

在 `config.yaml + settings` 中建立 query 清理配置能力，命名不使用 openai 前缀。配置支持环境变量覆盖，未配置时服务行为可降级（不阻断主流程）。本阶段不涉及 AI 改写逻辑的实现。

</domain>

<decisions>
## Implementation Decisions

### 配置域结构
- **扁平单层结构**：不采用嵌套分组，保持简单（当前仅一个 AI 模型）
- **命名风格**：下划线风格（`api_key`, `model_name`, `base_url`）
- **必须显式声明的键**：`enabled`, `model`, `api_key`, `base_url`
- **配置位置**：顶层独立块 `query_cleaning:` 与其他配置项同级

### 未配置降级行为
- **默认行为**：原样返回 query，但当前函数中的替换工作仍需执行
- **一致性处理**：`enabled: false` 与配置缺失处理一致，都视为"功能关闭"
- **响应标记**：不需要在响应中标记，通过日志体现降级状态
- **多步骤策略**：透传模式——某一步降级则该步返回原值，后续步骤继续执行

### 校验与错误提示
- **非法值处理**：启动时警告（不阻断启动，记录 WARN 日志，功能降级运行）
- **详细程度**：调试模式——根据日志级别动态调整，DEBUG 时输出完整信息
- **敏感信息**：完全隐藏——`api_key` 在日志中显示为 `***` 或 `[REDACTED]`
- **热更新**：不支持——仅启动时加载配置，修改需重启服务

### Claude's Discretion
- 配置块的具体 YAML 缩进和格式细节
- 环境变量命名前缀的具体设计（需避免与现有配置冲突）
- WARN 日志的具体文案和格式
- 配置模型的内部数据结构（Pydantic 模型字段命名等）

</decisions>

<specifics>
## Specific Ideas

- 配置命名明确不使用 `openai_` 前缀，保持提供商无关性
- 降级时保留原有正则替换逻辑，确保向后兼容
- 环境变量覆盖需遵循项目现有约定（优先 `.env`，其次 `config.yaml`）

</specifics>

<deferred>
## Deferred Ideas

- 多 AI 提供商支持（如同时配置 OpenAI 和 Anthropic）——未来扩展
- 配置热重载能力——当前阶段明确不支持
- 动态模型切换——Phase 2 后评估

</deferred>

---

*Phase: 01-配置建模*
*Context gathered: 2025-02-28*
