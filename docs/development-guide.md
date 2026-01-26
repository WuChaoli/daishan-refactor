# 开发指南

## 文档信息

- **项目名称**: 岱山 (daishan-master)
- **生成日期**: 2026-01-26
- **适用范围**: 开发环境搭建和本地开发

## 前置要求

### 系统要求
- **操作系统**: Linux / macOS / Windows (WSL2)
- **Python 版本**: 3.12 或更高
- **内存**: 最低 4GB RAM
- **磁盘空间**: 最低 2GB 可用空间

### 必需软件
- Python 3.12+
- pip (Python 包管理器)
- Git (版本控制)

### 可选软件
- PyCharm 或 VS Code (推荐 IDE)
- Docker (用于容器化部署)
- Postman 或 curl (API 测试)

## 环境搭建

### 1. 克隆项目

```bash
git clone <repository-url>
cd daishan-master
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3.12 -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 3. 安装依赖

#### 安装根目录依赖
```bash
pip install -r requirements.txt
```

#### 安装 RAG Stream 服务依赖
```bash
pip install -r rag_stream/requirements.txt
```

### 4. 配置环境变量

#### RAG Stream 服务配置

创建 `rag_stream/.env` 文件（可选，使用默认配置可跳过）：

```bash
# RAGFlow 服务配置
RAG_BASE_URL=http://172.16.11.60:8081
RAG_API_KEY=ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm

# 超时配置
REQUEST_TIMEOUT=300
STREAM_TIMEOUT=300

# 会话管理配置
SESSION_EXPIRE_HOURS=1
MAX_SESSIONS_PER_USER=5
```

#### Digital Human 服务配置

Digital Human 服务的配置硬编码在 `main.py` 中，如需修改：

```python
# 在 Digital_human_command_interface/main.py 中修改
FIXED_API_KEY = "app-Dkzi2px4Gg8F7vaUdn22Z3VL"
FIXED_BASE_URL = "http://172.16.11.60/v1"
DIFY_TIMEOUT = 30.0
FIXED_PORT = 11029
```

## 本地开发

### 启动 Digital Human Command Interface

#### 方式 1: 直接运行
```bash
cd Digital_human_command_interface
python main.py
```

#### 方式 2: 使用 uvicorn
```bash
uvicorn Digital_human_command_interface.main:app --host 0.0.0.0 --port 11029 --reload
```

**服务地址**: http://localhost:11029

**API 文档**: http://localhost:11029/docs

### 启动 RAG Stream 服务

#### 方式 1: 直接运行
```bash
cd rag_stream
python main.py
```

#### 方式 2: 使用 uvicorn
```bash
uvicorn rag_stream.main:app --host 0.0.0.0 --port 11027 --reload
```

**服务地址**: http://localhost:11027

**API 文档**: http://localhost:11027/docs

### 同时启动两个服务

使用两个终端窗口分别启动：

**终端 1 - Digital Human:**
```bash
source .venv/bin/activate
cd Digital_human_command_interface
python main.py
```

**终端 2 - RAG Stream:**
```bash
source .venv/bin/activate
cd rag_stream
python main.py
```

## 开发工作流

### 1. 代码修改

- 修改代码后，使用 `--reload` 参数的 uvicorn 会自动重启服务
- 建议使用 IDE 的代码格式化工具保持代码风格一致

### 2. API 测试

#### 使用 FastAPI 自动文档
- Digital Human: http://localhost:11029/docs
- RAG Stream: http://localhost:11027/docs

#### 使用 curl 测试

**Digital Human 流式聊天:**
```bash
curl -X POST http://localhost:11029/api/stream-chat \
  -H "Content-Type: application/json" \
  -d '{
    "text_input": "请介绍贵公司",
    "user_id": "test_user"
  }' \
  --no-buffer
```

**RAG Stream 法律法规问答:**
```bash
curl -X POST http://localhost:11027/api/laws \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法？",
    "user_id": "test_user"
  }' \
  --no-buffer
```

#### 使用 Python 测试

```python
import requests
import json

# 测试 Digital Human
url = "http://localhost:11029/api/stream-chat"
data = {"text_input": "你好", "user_id": "test"}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))

# 测试 RAG Stream
url = "http://localhost:11027/api/laws"
data = {"question": "安全生产法的主要内容", "user_id": "test"}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### 3. 健康检查

```bash
# Digital Human
curl http://localhost:11029/health

# RAG Stream
curl http://localhost:11027/health
```

### 4. 日志查看

两个服务都使用 Python logging 模块，日志输出到控制台：

- **INFO**: 正常操作日志
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **EXCEPTION**: 异常堆栈

## 常见开发任务

### 添加新的 RAG 领域

1. 在 `rag_stream/config.py` 中添加新的 chat_id：
```python
CHAT_IDS: ClassVar[Dict[str, str]] = {
    # ... 现有配置
    "新领域": "new-chat-id-here"
}
```

2. 在 `rag_stream/main.py` 中添加新的路由：
```python
@app.post("/api/new-domain", response_model=ChatResponse)
async def chat_new_domain(request: ChatRequest):
    """新领域问答接口"""
    return await chat_with_category("新领域", request)
```

### 修改超时配置

**Digital Human:**
```python
# 在 main.py 中修改
DIFY_TIMEOUT = 30.0  # 总超时
# 在 dify_async_stream_generator 中修改首次响应超时
if not first_output_sent and (time.time() - start_time > 15):
```

**RAG Stream:**
```python
# 在 config.py 中修改
REQUEST_TIMEOUT: int = 300
STREAM_TIMEOUT: int = 300

# 在 main.py 中修改首次响应超时
if not first_output_sent and (time.time() - start_time > 15):
```

### 修改打字机效果

在 `Digital_human_command_interface/main.py` 中：
```python
chunk_size = 3  # 每次输出字符数
await asyncio.sleep(0.02)  # 延迟时间（秒）
```

### 添加新的数据模型

在 `rag_stream/models.py` 中添加：
```python
class NewModel(BaseModel):
    """新模型描述"""
    field1: str = Field(..., description="字段1描述")
    field2: Optional[int] = Field(None, description="字段2描述")
```

## 调试技巧

### 1. 启用详细日志

修改日志级别为 DEBUG：
```python
logging.basicConfig(level=logging.DEBUG)
```

### 2. 使用 Python 调试器

```python
import pdb; pdb.set_trace()  # 设置断点
```

### 3. 使用 IDE 调试

**PyCharm 配置:**
1. 创建 Python 运行配置
2. Script path: 指向 `main.py`
3. Working directory: 指向服务目录
4. 设置断点并启动调试

**VS Code 配置 (launch.json):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Digital Human",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/Digital_human_command_interface/main.py",
      "console": "integratedTerminal"
    },
    {
      "name": "RAG Stream",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/rag_stream/main.py",
      "console": "integratedTerminal"
    }
  ]
}
```

### 4. 监控网络请求

使用 mitmproxy 或 Charles 监控 HTTP 请求：
```bash
pip install mitmproxy
mitmproxy -p 8888
```

## 代码风格

### Python 代码规范

遵循 PEP 8 规范：
- 使用 4 个空格缩进
- 行长度不超过 120 字符
- 函数和类之间空两行
- 使用有意义的变量名

### 推荐工具

```bash
# 安装代码格式化工具
pip install black isort flake8

# 格式化代码
black .
isort .

# 检查代码风格
flake8 .
```

## 性能优化

### 1. 异步处理

两个服务都使用异步处理，确保：
- 使用 `async/await` 语法
- 使用异步 HTTP 客户端（httpx, aiohttp）
- 避免阻塞操作

### 2. 连接池

httpx 和 aiohttp 自动管理连接池，无需额外配置。

### 3. 超时设置

合理设置超时时间，避免长时间等待：
- 总超时: 30 秒
- 首次响应超时: 15 秒

## 故障排查

### 问题 1: 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :11029
lsof -i :11027

# 杀死进程
kill -9 <PID>
```

### 问题 2: 依赖安装失败

**错误**: `pip install` 失败

**解决**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: 虚拟环境激活失败

**错误**: 无法激活虚拟环境

**解决**:
```bash
# 删除旧的虚拟环境
rm -rf .venv

# 重新创建
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 问题 4: 外部服务连接失败

**错误**: 无法连接到 Dify 或 RAGFlow

**解决**:
1. 检查服务地址是否正确
2. 检查网络连接
3. 检查 API 密钥是否有效
4. 使用 curl 测试外部服务：
```bash
curl -H "Authorization: Bearer <API_KEY>" http://172.16.11.60/v1/health
```

### 问题 5: 流式响应超时

**错误**: 15 秒后返回超时错误

**解决**:
1. 检查外部服务响应速度
2. 增加超时时间配置
3. 检查网络延迟

## 开发最佳实践

### 1. 使用虚拟环境

始终在虚拟环境中开发，避免依赖冲突。

### 2. 版本控制

- 提交前检查代码
- 编写清晰的提交信息
- 不要提交敏感信息（API 密钥、密码）

### 3. 错误处理

- 使用 try-except 捕获异常
- 记录详细的错误日志
- 返回友好的错误信息

### 4. 测试

- 编写单元测试
- 测试边界情况
- 测试错误处理

### 5. 文档

- 为函数添加 docstring
- 更新 API 文档
- 记录配置变更

## 依赖管理

### 查看已安装的包

```bash
pip list
```

### 更新依赖

```bash
pip install --upgrade <package-name>
```

### 导出依赖

```bash
pip freeze > requirements.txt
```

### 检查依赖安全性

```bash
pip install safety
safety check
```

## 下一步

完成开发环境搭建后：

1. 阅读 [API 合约文档](./api-contracts-digital_human.md) 和 [RAG Stream API 文档](./api-contracts-rag_stream.md)
2. 查看 [源代码树分析](./source-tree-analysis.md) 了解项目结构
3. 参考 [部署指南](./deployment-guide.md) 进行生产部署
4. 查看 [架构文档](./architecture-digital_human.md) 了解系统设计

## 获取帮助

- 查看 FastAPI 文档: https://fastapi.tiangolo.com/
- 查看 Python 异步编程: https://docs.python.org/3/library/asyncio.html
- 项目问题: 联系项目维护者