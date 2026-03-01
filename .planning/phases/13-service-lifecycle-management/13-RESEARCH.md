# Phase 13: Service Lifecycle Management - Research

**Research Date:** 2026-03-01
**Phase:** 13 - Service Lifecycle Management
**Goal:** 启动关闭与资源清理

---

## 1. FastAPI Lifespan Protocol

### Current Best Practice (Modern FastAPI)

FastAPI 推荐使用 `lifespan` 参数替代 `startup`/`shutdown` 事件处理器：

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    await wait_for_external_services()
    yield
    # Shutdown
    await close_database()
    await close_http_clients()

app = FastAPI(lifespan=lifespan)
```

### Key Advantages

- **确定性清理**: `yield` 之后的代码保证执行（即使在启动阶段异常）
- **上下文管理器语义**: 自然支持资源获取即初始化（RAII）模式
- **可测试性**: Lifespan 上下文可独立测试

---

## 2. Uvicorn Signal Handling

### Default SIGTERM Behavior

Uvicorn 默认信号处理：

```python
# uvicorn/server.py 中的信号处理逻辑
async def shutdown(self, sig=None):
    """Graceful shutdown process."""
    logger.info("Shutting down")
    
    # 1. Stop accepting new connections
    await self.lifespan.shutdown()
    
    # 2. Wait for active requests to complete
    await self._wait_for_connections()
    
    # 3. Close all connections
    for connection in list(self.server_state.connections):
        connection.close()
```

### Custom Signal Handler

如需自定义关闭日志：

```python
import signal
import sys

def create_signal_handler(server):
    def handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        server.handle_exit(sig, frame)
    return handler

# 注册自定义处理器
signal.signal(signal.SIGTERM, create_signal_handler(server))
```

### Graceful Shutdown Timeout

Uvicorn 配置选项：

```bash
uvicorn main:app \
  --workers 4 \
  --timeout-keep-alive 30 \
  --timeout-graceful-shutdown 30  # Python 3.11+ / Uvicorn 0.24+
```

---

## 3. Database Connection Management

### Async Database Pattern

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 连接池配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # 自动检测失效连接
    pool_recycle=3600,   # 1小时后回收连接
    echo=False
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Lifespan 集成
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 测试连接
    await test_db_connection()
    app.state.db_engine = engine
    app.state.db_session = SessionLocal
    yield
    # 关闭连接池
    await engine.dispose()
```

### Connection Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    reraise=True
)
async def test_db_connection():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
```

---

## 4. External Service Readiness

### Best Effort Startup Pattern

```python
import asyncio
import httpx

async def wait_for_service(url: str, timeout: float = 30.0) -> bool:
    """
    非阻塞式服务就绪检测。
    返回 True 表示服务就绪，False 表示超时但继续启动。
    """
    start = asyncio.get_event_loop().time()
    async with httpx.AsyncClient() as client:
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                resp = await client.get(f"{url}/health", timeout=2.0)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
    return False

# Lifespan 中的使用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 数据库必须就绪
    await wait_for_db()
    
    # 外部服务最佳 effort
    app.state.dify_ready = await wait_for_service(DIFY_URL)
    app.state.ragflow_ready = await wait_for_service(RAGFLOW_URL)
    
    if not app.state.dify_ready:
        logger.warning("Dify not ready at startup, will retry on requests")
    
    yield
    # 关闭...
```

---

## 5. HTTP Client Connection Pool

### Shared Client Pattern

```python
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 创建共享 HTTP 客户端（连接池）
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        )
    )
    yield
    # 关闭连接池
    await app.state.http_client.aclose()
```

### Dependency Injection

```python
async def get_http_client() -> httpx.AsyncClient:
    from fastapi import Request
    # 通过 request.app.state 访问
    pass

# 或作为依赖
async def dify_client(app_state) -> httpx.AsyncClient:
    return app_state.http_client
```

---

## 6. Docker Signal Delivery

### Critical Configuration

Dockerfile 必须使用 exec form 的 CMD：

```dockerfile
# ✅ 正确 - PID 1 是 uvicorn，能接收信号
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11028"]

# ❌ 错误 - PID 1 是 /bin/sh，信号不会转发
CMD uvicorn main:app --host 0.0.0.0 --port 11028
```

### Docker Compose 配置

```yaml
services:
  app:
    stop_signal: SIGTERM
    stop_grace_period: 30s
    # 健康检查确保启动完成后才标记为健康
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11028/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 40s
```

---

## 7. Startup Script Pattern

### Database Wait Script

```python
#!/usr/bin/env python3
"""
启动前等待数据库就绪。
在 Dockerfile 中作为 ENTRYPOINT 或 CMD 前缀使用。
"""
import asyncio
import sys
import os

async def wait_for_db(max_retries: int = 30, interval: float = 2.0) -> bool:
    """Wait for database to be ready."""
    from src.rag_stream.database import test_connection
    
    for i in range(max_retries):
        try:
            if await test_connection():
                print(f"✓ Database ready after {i+1} attempts")
                return True
        except Exception as e:
            print(f"  Attempt {i+1}/{max_retries}: {e}")
        
        await asyncio.sleep(interval)
    
    return False

async def main():
    # 等待数据库
    if not await wait_for_db():
        print("✗ Database not ready, exiting")
        sys.exit(1)
    
    # 启动主应用
    os.execvp("uvicorn", ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11028"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Alternative: Lifespan-Only Approach

现代 FastAPI 应用推荐纯 lifespan 方式，无需单独的启动脚本：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 所有初始化在这里完成
    await init_with_retry()
    yield
    # 所有清理在这里完成
    await cleanup()
```

---

## 8. Uvicorn Configuration for Production

### Command Line Options

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 11028 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --lifespan on \
  --timeout-keep-alive 30 \
  --timeout-graceful-shutdown 30 \
  --access-log \
  --log-level info
```

### Programmatic Configuration

```python
import uvicorn
from uvicorn.config import Config
from uvicorn.server import Server

config = Config(
    "main:app",
    host="0.0.0.0",
    port=11028,
    workers=4,
    lifespan="on",
    timeout_keep_alive=30,
    log_level="info"
)

server = Server(config)
```

---

## 9. Common Pitfalls

### ❌ 异步生成器中的异常处理

```python
# 错误：yield 后的异常不会执行清理
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init()
    yield
    await cleanup()  # 如果 init() 失败，这行不会执行
```

### ✅ 正确的异常处理

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    resources = []
    try:
        resource = await init()
        resources.append(resource)
        yield
    finally:
        for r in resources:
            await r.close()
```

### ❌ 阻塞操作在异步上下文

```python
# 错误：time.sleep 会阻塞事件循环
await asyncio.sleep(5)  # ✓ 正确
import time
time.sleep(5)  # ✗ 错误
```

---

## 10. Implementation Recommendations

### Recommended Architecture

```
main.py
├── lifespan() context manager
│   ├── init_database() - 连接池 + 重试
│   ├── init_http_client() - 共享客户端
│   ├── wait_for_external_services() - 最佳 effort
│   └── yield
│   ├── close_http_client()
│   └── close_database()
├── FastAPI(app=lifespan)
└── Uvicorn with 4 workers + 30s timeout
```

### File Structure

```
src/rag_stream/
├── main.py                 # Lifespan + app factory
├── lifespan.py             # 独立的 lifespan 模块
├── startup.py              # 启动相关工具函数
├── shutdown.py             # 关闭相关工具函数
└── docker-compose.yml      # 已存在，需确认 stop_grace_period
```

### Key Configuration Values

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Workers | 4 | CPU cores in container |
| Keep-alive timeout | 30s | Match Docker stop timeout |
| Graceful shutdown | 30s | Docker stop_grace_period |
| DB retry attempts | 5 | 10s total wait |
| DB retry interval | 2s | Linear backoff |
| External service timeout | 30s | Best effort, non-blocking |

---

## Validation Architecture

### Test Strategy

1. **Unit Tests**: Lifespan 上下文管理器独立测试
2. **Integration Tests**: Docker 环境中测试 SIGTERM 处理
3. **E2E Tests**: 完整启动 → 请求 → 关闭流程

### Test Scenarios

```python
# 测试场景 1: 正常启动关闭
async def test_lifespan_normal():
    async with lifespan(app):
        # 应用运行中
        assert app.state.db_engine is not None
    # 清理完成
    assert app.state.db_engine.closed

# 测试场景 2: SIGTERM 信号处理
async def test_sigterm_handling():
    # 启动容器
    # 发送 SIGTERM
    # 验证优雅关闭日志
    # 验证资源已释放
```

### Docker Test

```bash
# 构建并启动
docker-compose up -d

# 等待启动完成
sleep 10

# 发送 SIGTERM
docker-compose kill -s SIGTERM rag_stream

# 观察日志
docker-compose logs rag_stream | grep -E "(shutdown|cleanup|graceful)"

# 验证退出码
docker-compose ps | grep "Exit 0"
```

---

## References

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [Uvicorn Configuration](https://www.uvicorn.org/settings/)
- [Docker Stop Signal](https://docs.docker.com/engine/reference/commandline/stop/)
- [Python asyncio - Graceful Shutdown](https://docs.python.org/3/library/asyncio-runner.html#graceful-shutdown)

---

*Research complete. Ready for planning.*
