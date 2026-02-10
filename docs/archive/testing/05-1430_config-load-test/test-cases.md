# Config.py 加载测试用例

## 测试目标
验证 `Digital_human_command_interface/src/config.py` 的配置加载功能

## 测试环境

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.12.3 |
| 项目路径 | `Digital_human_command_interface/` |
| 配置文件 | `config.yaml` |
| 环境变量 | `.env` |
| 依赖 | `pyyaml`, `python-dotenv` |

## 测试用例

### TC01: 正常加载

**前置条件**:
- `.env` 文件包含 `RAGFLOW_API_KEY` 和 `DIFY_STREAM_CHAT_KEY`
- `config.yaml` 格式正确

**操作步骤**:
```python
from src.config import ConfigManager

manager = ConfigManager("config.yaml")
config = manager.get_config()
```

**预期输出**:
- `config` 非 `None`
- `config.ragflow_api_key` 与环境变量一致
- `config.database_mapping` 包含两个知识库
- `config.similarity_threshold == 0.5`
- `config.server_port == 11029`

---

### TC02: 配置文件不存在

**前置条件**:
- 传入不存在的配置文件路径

**操作步骤**:
```python
manager = ConfigManager("nonexistent.yaml")
```

**预期输出**:
- 抛出 `FileNotFoundError: 配置文件不存在: nonexistent.yaml`

---

### TC03: RAGFLOW_API_KEY 为空

**前置条件**:
- `.env` 中 `RAGFLOW_API_KEY` 为空或未设置

**操作步骤**:
```python
# 临时移除环境变量
import os
os.environ["RAGFLOW_API_KEY"] = ""

manager = ConfigManager("config.yaml")
```

**预期输出**:
- 抛出 `ValueError: 配置验证失败: RAGFlow API Key 不能为空`

---

### TC04: database_mapping 字符串转整数

**前置条件**:
- `config.yaml` 中 `database_mapping` 的值为字符串 `"1"` 而非整数 `1`

**操作步骤**:
```python
# 当前 config.yaml 已使用整数，需手动修改测试
manager = ConfigManager("config.yaml")
config = manager.get_config()
```

**预期输出**:
- `config.database_mapping` 值为整数类型
- 字符串 `"1"` 自动转为 `int` 1

---

### TC05: similarity_threshold 越界

**前置条件**:
- 修改 `config.yaml` 中 `intent.similarity_threshold` 为 `1.5`

**操作步骤**:
```python
manager = ConfigManager("config_test_invalid.yaml")
```

**预期输出**:
- 抛出 `ValueError: 配置验证失败: similarity_threshold 必须在 [0, 1] 范围内`

---

### TC06: server_port 越界

**前置条件**:
- 修改 `config.yaml` 中 `server.port` 为 `100`（小于 1024）

**操作步骤**:
```python
manager = ConfigManager("config_test_invalid.yaml")
```

**预期输出**:
- 抛出 `ValueError: 配置验证失败: server_port 必须在 [1024, 65535] 范围内`

---

### TC07: BASE_URL 格式错误

**前置条件**:
- 修改 `config.yaml` 中 `ragflow.base_url` 不以 `http://` 或 `https://` 开头

**操作步骤**:
```python
manager = ConfigManager("config_test_invalid.yaml")
```

**预期输出**:
- 抛出 `ValueError: 配置验证失败: RAGFlow BASE_URL 格式错误，必须以 http:// 或 https:// 开头`

---

### TC08: 日志目录自动创建

**前置条件**:
- 日志目录不存在

**操作步骤**:
```python
import shutil
import os

# 删除日志目录
log_dir = Path("logs")
if log_dir.exists():
    shutil.rmtree(log_dir)

manager = ConfigManager("config.yaml")
```

**预期输出**:
- 日志目录自动创建
- 验证通过，不抛出异常

---

### TC09: get_databases() 方法

**前置条件**:
- 配置正常加载

**操作步骤**:
```python
manager = ConfigManager("config.yaml")
databases = manager.get_databases()
```

**预期输出**:
- 返回列表 `["岱山-指令集-260129", "岱山-数据库问题-5张表"]`

---

### TC10: get_type_mapping() 正常情况

**前置条件**:
- 配置正常加载

**操作步骤**:
```python
manager = ConfigManager("config.yaml")
type_id = manager.get_type_mapping("岱山-指令集-260129")
```

**预期输出**:
- 返回 `1`

---

### TC11: get_type_mapping() 知识库不存在

**前置条件**:
- 配置正常加载

**操作步骤**:
```python
manager = ConfigManager("config.yaml")
type_id = manager.get_type_mapping("不存在的知识库")
```

**预期输出**:
- 抛出 `KeyError: 知识库 '不存在的知识库' 不在配置的 database_mapping 中`

---

## 测试数据文件

### config_test_invalid.yaml（用于 TC05, TC06, TC07）

```yaml
ragflow:
  base_url: "invalid_url"  # 不以 http/https 开头
  database_mapping:
    test_kb: 1

intent:
  similarity_threshold: 1.5  # 超出范围
  default_type: 0

server:
  port: 100  # 小于 1024
```
