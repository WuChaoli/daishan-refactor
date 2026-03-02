---
type: quick
task: 3
mode: quick
description: 更新打包docker镜像
date: 2026-03-02
---

<objective>
在不引入研究阶段的前提下，完成 `rag_stream` Docker 镜像打包配置更新，并通过一次可复现的本地构建验证打包链路可用。
</objective>

<tasks>

<task type="auto">
  <name>更新镜像打包配置</name>
  <files>
    src/rag_stream/Dockerfile
    src/rag_stream/docker-compose.yml
    src/rag_stream/docker-compose.prod.yml
  </files>
  <action>
1. 调整 Dockerfile 中与打包相关的构建参数/依赖安装步骤，确保生产镜像构建逻辑一致且可复用。
2. 同步更新 compose 文件中的 build/image 相关配置，保证开发与生产覆盖文件的打包入口一致。
3. 保留现有服务端口、健康检查与优雅退出设置，不扩展到非打包范围改动。
  </action>
  <verify>
    <automated>docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml config >/tmp/rag_stream.compose.rendered.yml && test -s /tmp/rag_stream.compose.rendered.yml</automated>
  </verify>
  <done>compose 渲染成功，且打包配置在 Dockerfile 与 compose 文件中保持一致</done>
</task>

<task type="auto">
  <name>执行镜像构建与最小可用性验证</name>
  <files>
    src/rag_stream/Dockerfile
    src/rag_stream/docker-compose.yml
    src/rag_stream/docker-compose.prod.yml
  </files>
  <action>
1. 使用更新后的配置构建 `rag_stream` 镜像（生产组合配置）。
2. 启动容器并执行一次 `/health` 健康检查，确认镜像可启动。
3. 记录构建成功标识（镜像 tag/构建时间）与容器健康检查结果，作为交付证据。
  </action>
  <verify>
    <automated>docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml build rag_stream && docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml up -d rag_stream && docker compose -f src/rag_stream/docker-compose.yml -f src/rag_stream/docker-compose.prod.yml exec -T rag_stream python -c "import urllib.request; urllib.request.urlopen('http://localhost:11028/health', timeout=5); print('health-ok')"</automated>
  </verify>
  <done>镜像构建通过，容器健康检查返回成功</done>
</task>

</tasks>

<success_criteria>
- [ ] Dockerfile 与 compose 的打包配置已同步更新
- [ ] `rag_stream` 镜像可按更新配置完成构建
- [ ] 容器启动后 `/health` 检查通过
</success_criteria>
