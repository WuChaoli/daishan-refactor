# log_decorator

`log_decorator` 是一个轻量级函数日志装饰器，核心目标是：

- 统一记录函数开始、入参、出参、耗时
- 在嵌套调用时提供树形缩进，便于追踪调用链
- 支持入口函数独立日志文件与错误上下文日志
- 在特定条件下生成 Mermaid 执行路径 Markdown

该文档已按当前实现（`decorator.py` / `parser.py` / `mermaid.py`）同步更新。

## 安装与依赖

项目运行本功能至少需要 `pyyaml`：

```bash
uv add pyyaml
```

## 快速开始

```python
from log_decorator import log

@log()
def add(x: int, y: int) -> int:
    return x + y

add(1, 2)
```

典型日志（示意）：

```text
2026-02-09 18:40:00 - INFO  - add - 【开始执行】
2026-02-09 18:40:00 - INFO  - add - 【入参】
  - args[0]: 1
  - args[1]: 2
2026-02-09 18:40:00 - INFO  - add - 【出参】3
2026-02-09 18:40:00 - INFO  - add - 【执行完成】耗时：0.08ms
```

## `@log()` 参数

当前签名：

```python
def log(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = True,
    is_entry: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None,
) -> Callable
```

参数说明：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `print_args` | `True` | 是否记录入参 |
| `print_result` | `True` | 是否记录出参 |
| `print_duration` | `True` | 是否记录耗时 |
| `is_entry` | `False` | 是否作为“入口函数”，会增加 `{entry}.log` |
| `message` | `None` | 自定义开始日志文案，如 `【用户登录】开始执行` |
| `args_handler` | `None` | 自定义入参展示，接收 `(args, kwargs)` |
| `result_handler` | `None` | 自定义出参展示，接收函数返回值 |
| `enable_mermaid` | `False` | 是否为入口调用链启用 Mermaid 记录器 |
| `force_mermaid` | `False` | 是否强制输出 Mermaid 文件 |
| `log_level` | `None` | 装饰器级别，支持字符串或 `lambda` |

### `args_handler` 与 `result_handler`

```python
from log_decorator import log

@log(
    args_handler=lambda args, kwargs: {"uid": args[0], "op": kwargs.get("action")},
    result_handler=lambda result: {"status": result.get("status")},
)
def do_action(user_id: int, action: str):
    return {"status": "ok", "detail": "..."}
```

- `handler` 抛异常不会影响业务函数返回
- 处理失败时会降级并写入 warning

## 关键行为说明

### 1) 树形缩进与调用栈

- 采用线程本地调用栈（`threading.local`）追踪深度
- 嵌套调用使用 `├─` / `│` 前缀展示层级

### 2) 入口函数与双日志

- 始终写入全局日志：`logs/global.log`
- 当 `is_entry=True` 且当前没有活跃入口时，额外写入 `logs/{entry_func}.log`
- 同时只允许一个活跃入口，内层 `is_entry=True` 不会抢占外层入口

### 3) Mermaid 输出触发条件

必须满足 `is_entry=True` 且 `enable_mermaid=True`，并且满足以下任一条件才会落盘：

1. `force_mermaid=True`
2. 装饰器有效级别是 `DEBUG`
3. 入口调用链中发生异常

输出目录：`logs/mermaid/{entry_func}/`

输出文件为 Markdown（`.md`），包含：

- ASCII 调用树
- 性能统计表
- Mermaid `flowchart TD`

### 4) 错误增强日志

入口调用链发生异常时，会追加写入 `logs/error.log`，包含：

- 入口函数名
- 调用链路（例如 `level1 -> level2`）
- 错误类型与信息
- `__cause__` / `__context__` 异常链（如存在）
- 脱敏后的入参快照
- Mermaid 文件路径（如本次生成）

### 5) 敏感信息脱敏规则

`sanitize_sensitive_data` 会对字典键名做包含匹配（不区分大小写），默认规则：

- `api_key` / `key`：保留前缀并打码
- `token`：保留前后片段
- `password` / `secret`：直接替换为 `***`

## 对象解析规则（`parse_obj`）

默认 `compact=True`：

- `dict` -> `<dict: N keys>`
- `list` -> `<list: N items>`
- `tuple` -> `<tuple: N items>`
- 类实例 -> `<ClassName: N attrs>`

如需完整展开可显式使用：

```python
from log_decorator.parser import parse_obj

detail = parse_obj(obj, compact=False, max_depth=3)
```

## 日志级别控制（`log_level`）

```python
import os
from log_decorator import log

@log(log_level="DEBUG")
def debug_func():
    return 1

@log(log_level=lambda: os.getenv("LOG_LEVEL", "INFO"))
def dynamic_level_func():
    return 2
```

- 支持字符串级别：`DEBUG/INFO/WARNING/ERROR/CRITICAL`
- 支持 `lambda` 动态计算
- 无效值或计算异常会回退到全局配置级别

## 配置文件

配置加载优先级（高 -> 低）：

1. 项目根目录 `log_config.yaml`
2. `log_decorator/log_config.yaml`
3. 代码内 `DEFAULT_CONFIG`

示例：

```yaml
logging:
  format: "%(asctime)s - %(levelname)-5s - %(message)s"
  time_format: "%Y-%m-%d %H:%M:%S"
  level: INFO
  encoding: utf-8
  log_dir: logs
  global_log_file: global.log
  console_enabled: true
  mermaid_enabled: false
  mermaid_dir: mermaid
  mermaid_max_size_mb: 10
```

> 注意：当前实现中 Mermaid 是否启用以装饰器参数 `enable_mermaid` 为准；`mermaid_enabled` 目前仅作为配置项保留。

## 文件结构

```text
log_decorator/
├── __init__.py
├── decorator.py
├── parser.py
├── config.py
├── mermaid.py
├── log_config.yaml
└── README.md
```

典型日志目录：

```text
logs/
├── global.log
├── {entry_func}.log
├── error.log
└── mermaid/
    └── {entry_func}/
        └── 2026-02-09_18-40-00.123.md
```

## 导出 API

```python
from log_decorator import log, logger, parse_obj, load_config
```

## 使用建议

- 入口层函数加 `is_entry=True`，业务内部函数按需加 `@log()`
- 高频函数可关闭 `print_args` / `print_result` 降低日志体积
- 涉及密钥、密码、token 的接口优先自定义 `args_handler`
- 若要稳定留存调用图，建议 `force_mermaid=True`
