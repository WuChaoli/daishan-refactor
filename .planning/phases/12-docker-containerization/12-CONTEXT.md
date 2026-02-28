# Phase 12: Docker Containerization - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

创建安全优化的 Docker 容器配置，支持多阶段构建、非 root 运行、优雅关闭，无 secrets 泄漏。仅包括 Dockerfile 和 docker-compose.yml 配置，不包含 CI/CD 流水线（Phase 11）或健康检查端点实现（Phase 14）。

</domain>

<decisions>
## Implementation Decisions

### 基础镜像策略
- Python 版本：**3.11**（项目当前版本，稳定性优先）
- 发行版：**bookworm-slim**（Debian 12，稳定性好）
- 使用官方 Python 镜像作为基础，在 Dockerfile 中安装 uv
- 不使用 alpine（musl 兼容性问题）

### 构建阶段设计
- **两阶段构建：** builder 阶段编译依赖 → runtime 阶段只保留运行所需
- **缓存优化：** 先复制 pyproject.toml 和 uv.lock → 安装依赖 → 再复制代码
- **层优化：** 利用 Docker 层缓存，避免每次代码变更都重新安装依赖

### Docker Compose 编排
- **配置方式：** 使用项目已有 config.yaml + .env 配置（bind mount 挂载）
- **网络：** 默认 bridge 网络（单主机部署，简单够用）
- **健康检查：** Dockerfile 中加入 HEALTHCHECK 指令
- **服务依赖：** 定义外部服务（Milvus、DaiShanSQL）的连接等待

### 端口与目录
- **暴露端口：** 11027 和 11029
- **工作目录：** /app
- **代码挂载：** 可选开发模式 bind mount

### 安全加固
- **运行用户：** 自动创建非 root 用户（如 65534:nobody 或自定义 UID）
- **权限最小化：** 仅授予必要的文件读写权限
- **Secrets 处理：** 绝不将 secrets 写入镜像层，通过环境变量或挂载注入

### 优雅关闭
- **信号处理：** 使用 exec form CMD 确保 SIGTERM 正确传递
- **超时：** 配置 Uvicorn graceful shutdown 超时（30秒）
- **关闭顺序：** 先停止接受新请求 → 处理完活跃请求 → 关闭连接

</decisions>

<specifics>
## Specific Ideas

- 参考 uv 官方 Docker 使用示例优化构建
- builder 阶段使用完整 Debian 镜像确保编译工具可用
- runtime 阶段使用 slim 镜像减小体积
- 使用 .dockerignore 排除敏感文件（.env、secrets、缓存）

</specifics>

<deferred>
## Deferred Ideas

- 使用 uv 官方预构建镜像（ghcr.io/astral-sh/uv）—— 可后续优化
- 多架构构建（ARM64/AMD64）—— 当前非必需
- Kubernetes deployment manifests —— 超出当前阶段范围
- 镜像签名和 SBOM —— 安全增强，可后续添加

</deferred>

<claude_discretion>
## Claude's Discretion

以下实现细节由下游代理自行决定：
- 具体的 Dockerfile 指令顺序优化
- .dockerignore 文件的详细条目
- HEALTHCHECK 的具体命令和间隔时间
- 非 root 用户的具体创建方式（useradd vs adduser）
- 构建缓存的具体路径设置

</claude_discretion>

---

*Phase: 12-docker-containerization*
*Context gathered: 2026-02-28*
