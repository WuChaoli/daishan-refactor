## Python 开发规范

### 环境与依赖
| 规则 | 命令 |
|------|------|
| 强制 uv（禁用 pip） | `uv add requests` / `uv add --dev pytest` |
| 虚拟环境 `.venv/` | `uv venv --python 3.11` |
| 锁文件提交 | `uv sync --frozen` |

### 数据建模
| 原则 | 要求 |
|------|------|
| 优先类包装 | 跨函数/模块传递必须用类，禁止裸字典/元组 |
| 类型即文档 | 所有字段必须类型注解 |
| 行为内聚 | 相关方法放在类内部 |
| 单文件单类 | 1个公开类 + N个私有函数，文件名=类名蛇形 |

### 错误处理（快速失败）
| 层级 | 策略 |
|------|------|
| 内部函数 | 直接抛出异常 `if not x: raise ValueError(msg)` |
| 端点函数 | 捕获并返回 `{"code":1, "message":"", "data":None}` |
| 异常类型 | 捕获具体异常（ValueError/KeyError），避免 Exception |
| 日志记录 | 业务错误 `logger.error(msg)`，系统异常 `exc_info=True` |