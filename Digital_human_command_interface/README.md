# 岱山意图识别服务

基于 RAGFlow 的用户指令意图识别 REST API 服务

## 功能特性

- **智能意图识别**: 自动识别用户查询的三种意图类型
  - type=0: 语义类问题 (使用 RAG 知识库检索)
  - type=1: 明确指令 (一一对应的函数处理)
  - type=2: 统计类问题 (需要数据库查询)

- **多知识库支持**: 支持同时查询多个 RAGFlow 知识库
- **相似度排序**: 按相似度降序返回最匹配的结果
- **降级策略**: RAGFlow 服务异常时自动降级，保证服务可用性
- **分层日志系统**: 全局日志 + 功能日志，便于问题排查
- **高性能**: 基于 FastAPI 异步框架，支持高并发

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
conda create -n daishan-new python=3.10
conda activate daishan-new

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置示例文件
cp config.example.yaml config.yaml

# 编辑配置文件，修改 RAGFlow API Key 和服务地址
vim config.yaml
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://0.0.0.0:11029` 启动

### 4. 测试接口

```bash
# 健康检查
curl http://localhost:11029/health

# 意图识别
curl -X POST http://localhost:11029/intent \
  -H "Content-Type: application/json" \
  -d '{"query": "今天天气怎么样"}'

curl -X POST http://localhost:11029/intent \
  -H "Content-Type: application/json" \
  -d '{"query": "打开双重预防运行效果"}'

curl -X POST http://localhost:11029/intent \
  -H "Content-Type: application/json" \
  -d '{"query": "单位面积产值最近三个月有没有明显提升？具体数值是多少？"}'
```


## API 文档

启动服务后访问:
- **Swagger UI**: http://localhost:11029/docs
- **ReDoc**: http://localhost:11029/redoc

## 项目结构

```
daishan-new/
├── config.yaml              # 配置文件
├── config.example.yaml      # 配置示例
├── main.py                  # 应用入口
├── requirements.txt         # Python 依赖
├── README.md                # 项目说明
│
├── src/                     # 源代码
│   ├── config.py            # 配置管理器
│   ├── log_manager.py       # 日志管理器
│   ├── ragflow_client.py    # RAGFlow 客户端
│   ├── intent_judgment.py   # 意图判断逻辑
│   ├── models.py            # 数据模型
│   └── api/
│       └── routes.py        # FastAPI 路由
│
├── logs/                    # 日志目录
│   ├── global/              # 全局日志
│   ├── functions/           # 功能日志
│   └── archive/             # 归档日志
│
└── tests/                   # 测试
    ├── test_config.py       # 配置测试
    ├── test_log_manager.py  # 日志测试
    ├── test_models.py       # 模型测试
    └── test_api.py          # API 测试
```

## 配置说明

```yaml
# RAGFlow 配置
ragflow:
  api_key: "ragflow-xxxxxxxxxxxxxxxxxxxx"
  base_url: "http://192.168.1.160:8081"
  database_mapping:
    cmd_test1: 1  # 指令表 → 明确指令
    cmd_test2: 2  # 统计表 → 统计类

# 意图判断参数
intent:
  similarity_threshold: 0.4  # 相似度阈值
  top_k_per_database: 3      # Top-K 结果数
  default_type: 0            # 默认类型

# 服务器配置
server:
  host: "0.0.0.0"
  port: 11029

# 日志配置
logging:
  log_dir: "logs"
  max_bytes: 10485760        # 10MB
  backup_count: 5
  total_size_limit: 524288000  # 500MB
```

## API 接口

### POST /intent

意图识别接口

**请求**:
```json
{
  "query": "今天天气怎么样"
}
```

**响应**:
```json
{
  "type": 2,
  "question": "天气查询方法"
}
```

**错误响应** (400):
```json
{
  "error": "query_empty",
  "message": "查询内容不能为空",
  "suggestion": "请输入有效的查询内容"
}
```

## 开发

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 代码格式化

```bash
# 使用 black 格式化代码
pip install black
black src/ tests/

# 使用 isort 排序 import
pip install isort
isort src/ tests/
```

## 日志

日志文件位于 `logs/` 目录:
- `global/info.log`: 全局 INFO 日志
- `global/error.log`: 全局 ERROR 日志
- `functions/ragflow_client.log`: RAGFlow 客户端日志
- `functions/intent_judgment.log`: 意图判断日志
- `functions/api_interface.log`: API 接口日志

## 故障排查

### 服务启动失败

1. 检查配置文件是否存在: `config.yaml`
2. 检查配置格式是否正确: 运行 `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
3. 检查 RAGFlow 服务是否可访问

### RAGFlow 连接失败

1. 检查 `config.yaml` 中的 `base_url` 是否正确
2. 检查 `api_key` 是否有效
3. 查看 `logs/ragflow_client.log` 获取详细错误信息

### 日志容量超限

当日志总容量超过 500MB 时，系统会自动清理旧日志。如需手动清理:

```bash
# 查看日志容量
du -sh logs/

# 清理所有日志
rm -rf logs/*
```

## 技术栈

- Python 3.10
- FastAPI - Web 框架
- RAGFlow SDK - 语义检索
- Pydantic - 数据验证
- PyYAML - 配置文件
- Uvicorn - ASGI 服务器

## 许可证

内部项目，仅供岱山项目使用。

## 联系方式

如有问题，请联系开发团队。
