# rag_stream Docker 使用方法

## 1. 镜像下载结果

在项目根目录（`/home/wuchaoli/codespace/daishan-refactor`）执行：

```bash
docker pull daishan/rag_stream:local
```

返回结果：

```text
Error response from daemon: pull access denied for daishan/rag_stream, repository does not exist or may require 'docker login'
```

结论：当前环境无法直接从远端拉取 `daishan/rag_stream:local`。  
如果你们使用私有仓库，请先 `docker login <registry>` 再拉取。

## 2. 本地构建镜像（可用方案）

```bash
docker build -f src/rag_stream/Dockerfile -t daishan/rag_stream:local --target runtime .
```

本工作区构建成功，镜像 ID 为：

```text
sha256:5c3de868238ab4605245815da19d0442535737c1a1b7437330a985a255d76ad6
```

## 3. 使用 docker run 启动

容器内服务端口为 `11027`：

```bash
docker run -d \
  --name rag_stream \
  -p 11027:11027 \
  --env-file src/Digital_human_command_interface/.env \
  -e LOG_CONSOLE_OUTPUT=true \
  -v /home/wuchaoli/codespace/daishan-refactor/src/rag_stream/config.yaml:/app/src/rag_stream/config.yaml:ro \
  daishan/rag_stream:local
```

健康检查：

```bash
curl http://127.0.0.1:11027/health
```

停止并删除容器：

```bash
docker stop rag_stream && docker rm rag_stream
```

## 4. 使用 docker compose 启动（推荐）

在 `src/rag_stream` 目录执行：

```bash
cd src/rag_stream
docker compose up -d rag_stream
```

查看日志：

```bash
docker compose logs -f rag_stream
```

停止服务：

```bash
docker compose down
```

生产配置（如需）：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d rag_stream
```

## 5. 常见问题

1. `pull access denied`：检查镜像仓库地址、标签和 `docker login` 登录状态。
2. 健康检查失败：检查 `.env` 中是否包含 `RAG_BASE_URL`、`RAG_API_KEY` 等关键配置。
3. `11027` 端口冲突：改宿主机端口，例如 `-p 18027:11027`。
4. 配置未生效：确认挂载路径为绝对路径且文件存在。
