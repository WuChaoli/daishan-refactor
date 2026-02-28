# Phase 9: 外部服务连通性测试 - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

验证 AI API、向量库、数据库的连通性，确保外部服务可正常访问。测试使用 .venv 环境隔离运行，支持 CI/CD 自动化测试。

本阶段不测试业务逻辑，仅验证服务连通性。

</domain>

<decisions>
## Implementation Decisions

### 测试范围

- **AI API 测试**: 实际调用测试 — 发送简单请求验证完整链路（与现有 test_real_env.py 模式一致）
- **向量库测试**: 实际检索 — 执行一次简单向量检索验证完整链路
- **数据库测试**: 实际查询 — 执行 SELECT 1 验证完整连接池

### 失败诊断

测试失败时输出以下诊断信息：
- 环境变量检查 — 验证必需的 API 密钥、连接字符串是否已设置
- 配置文件验证 — 验证 config.yaml 中的配置项是否正确
- 网络连通性 — 检查目标主机和端口是否可达
- 详细错误堆栈 — 输出完整的异常信息便于调试

### CI/CD 配置

- **敏感配置处理**: 环境变量 + 配置文件混合（与现有 settings 体系一致）
  - 敏感信息（API 密钥、数据库密码）通过环境变量注入
  - 非敏感信息（端点地址、超时设置）使用配置文件
- **跳过机制**: 独立跳过控制
  - `SKIP_AI_TEST=1` — 跳过 AI API 测试
  - `SKIP_VECTOR_TEST=1` — 跳过向量库测试
  - `SKIP_DB_TEST=1` — 跳过数据库测试

### 报告格式

- pytest 默认控制台输出（适合本地调试和 CI/CD 查看）

### 超时设置

- 10 秒快速失败（适合 CI/CD 环境，快速反馈）
- 每个服务独立超时控制

### Claude's Discretion

- 具体的诊断信息输出格式
- 测试用例的组织结构
- 错误消息的详细程度

</decisions>

<specifics>
## Specific Ideas

- 复用现有的 `test_real_env.py` 模式进行 AI API 连通性测试
- 参考 `test_services_integration.py` 的结构组织测试代码
- 诊断信息应该清晰指出问题所在（是配置问题、网络问题还是服务问题）

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `src/rag_stream/tests/test_real_env.py`: 真实环境 AI 测试模式，可直接复用
- `src/rag_stream/tests/test_api_general_e2e.py`: E2E 测试结构参考
- `tests/integration/test_services_integration.py`: 集成测试组织方式
- `src/rag_stream/src/config/settings.py`: 配置加载体系，支持环境变量覆盖

### Established Patterns

- 测试使用 pytest 框架，asyncio 支持
- 配置通过 `config.yaml` + `.env` 加载，环境变量优先级高
- 测试数据使用 JSON 文件存储在 `tests/data/` 目录
- 真实环境测试使用 dataclass 组织测试用例和结果

### Integration Points

- 测试脚本需要添加项目路径到 sys.path（参考现有测试）
- 使用 `load_settings()` 加载配置
- 使用 `QueryChat` 工具类测试 AI API 连通性
- 向量库和数据库连接复用现有客户端类

</code_context>

<deferred>
## Deferred Ideas

- JUnit XML 格式报告输出 — 可在 Phase 11 (CI/CD 流水线集成) 中添加
- 性能基准测试 — 属于性能里程碑，非本阶段范围
- 多环境配置支持（开发/测试/生产）— 属于 v2 需求

</deferred>

---

*Phase: 09-external-service-connectivity*
*Context gathered: 2026-02-28*
