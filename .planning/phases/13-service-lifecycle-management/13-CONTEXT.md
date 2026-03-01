# Phase 13: Service Lifecycle Management - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

实现服务的启动关闭与资源清理机制。包括：SIGTERM 信号正确处理、外部连接优雅关闭、数据库等待初始化脚本、Uvicorn 工作进程配置。不包含健康检查端点（Phase 14）或日志管理（Phase 15）。

</domain>

<decisions>
## Implementation Decisions

### 启动流程
- 使用 startup event handler 执行初始化逻辑
- 数据库连接采用"尝试-重试"模式，最大重试 5 次，间隔 2 秒
- 外部服务（Dify、RAGFlow）不强制等待，启动后继续轮询就绪状态
- 启动超时：30 秒（与 Uvicorn 超时一致）

### 关闭行为
- 响应 SIGTERM 信号触发优雅关闭
- 关闭顺序：停止接受新请求 → 处理完活跃请求 → 关闭外部连接 → 清理资源
- 优雅关闭超时：30 秒（Docker stop 默认超时）
- 超时后强制终止剩余连接

### 资源清理
- 显式关闭的资源：数据库连接池、HTTP 客户端连接池、Redis 连接（如有）
- 清理顺序与依赖关系相反（先关闭上层资源）
- 所有清理操作在 lifespan shutdown 中完成

### Uvicorn 配置
- 工作进程数：4（基于容器 CPU 限制）
- 优雅关闭超时：30 秒
- 使用 lifespan 协议管理启动/关闭事件
- 信号处理：自定义 SIGTERM handler 在关闭前记录日志

### 故障恢复
- 启动失败时容器立即退出（不无限重试）
- Docker Compose 配置 restart: unless-stopped
- 关键错误日志输出到 stderr 便于监控告警

### Claude's Discretion
- 具体的重试间隔算法（线性 vs 指数退避）
- 连接池清理的具体实现细节
- 启动日志的详细程度

</decisions>

<specifics>
## Specific Ideas

- 参考 Phase 12 Dockerfile 中的 exec form CMD 确保信号正确传递
- 启动脚本可复用 Phase 09 的连通性测试逻辑验证依赖就绪
- 清理顺序应与初始化顺序相反

</specifics>

<deferred>
## Deferred Ideas

- 动态工作进程调整 — 超出当前阶段范围
- 预热机制（pre-warming）—— 可后续优化
- 启动探针（startup probe）—— 属于 Phase 14 健康检查

</deferred>

---

*Phase: 13-service-lifecycle-management*
*Context gathered: 2026-02-28*
