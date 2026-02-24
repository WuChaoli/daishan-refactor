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
2026-02-09 18:40:00 - INFO    - 🔵 add
2026-02-09 18:40:00 - INFO    -   ├─ 🧩 [ args ]
2026-02-09 18:40:00 - INFO    -   │  ├─ x: 1
2026-02-09 18:40:00 - INFO    -   │  └─ y: 2
2026-02-09 18:40:00 - INFO    -   └─ 🧪 [ returns ]
2026-02-09 18:40:00 - INFO    -      └─ result: 3
```

## 装饰器说明

三种装饰器定位：

- `@log(...)`：普通函数日志记录。
- `@log_entry(...)`：入口函数（创建 `{entry_func}.log`，可启用 Mermaid）。
- `@log_end(...)`：截止当前嵌套分支，下游 `@log(...)` 作为新分支继续。

> `@log()` 不再支持 `is_entry` 参数。

函数头标识（同形状不同颜色）：

- `🔵`：`@log(...)`
- `🟢`：`@log_entry(...)`
- `🟣`：`@log_end(...)`

## 通用参数

`@log()` 当前签名：

```python
def log(
    print_args: bool = True,
    print_result: bool = True,
    print_duration: bool = False,
    message: Optional[str] = None,
    args_handler: Optional[Callable[[tuple, dict], Any]] = None,
    result_handler: Optional[Callable[[Any], str]] = None,
    enable_mermaid: bool = False,
    force_mermaid: bool = False,
    log_level: Optional[Any] = None,
) -> Callable
```

`@log_entry()` 与 `@log_end()` 与 `@log()` 使用同一组参数。

参数说明：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `print_args` | `True` | 是否记录入参 |
| `print_result` | `True` | 是否记录出参 |
| `print_duration` | `False` | 是否记录耗时（默认关闭，可手动开启） |
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

## 运行时插入日志

可从 `log_decorator` 导入 `logging`，在函数中间插入日志：

```python
from log_decorator import log, logging

@log()
def process_order(order_id: int):
    logging.DEBUF(f"准备处理订单 {order_id}")
    logging.INFO("执行库存校验")
    return True
```

- 支持 `logging.DEBUF/INFO/WARNING/ERROR`
- 在 `@log` 上下文内会继承树状结构（`├─/│/└─`）
- 在 `@log` 上下文外调用会输出警告，并按根节点记录

说明：运行日志内容保持原样；仅 warning/error 行增加形状标识（`⚠` / `✖`）。

## 入参/出参渲染规则

- 入参优先使用函数签名中的参数名（如 `count`、`payload`），不再默认显示 `args[0]`
- `int/str/list/dict` 等基础类型与容器会尽量打印完整值
- 类对象优先调用 `to_json()` 输出；若不存在或调用失败，则回退 `str(obj)`
- 对实例方法会自动忽略 `self/cls`，仅保留业务参数

## 关键行为说明

### 1) 树形缩进与调用栈

- 采用线程本地调用栈（`threading.local`）追踪深度
- 嵌套调用使用 `├─` / `│` 前缀展示层级

### 2) 入口函数与双日志

- 始终写入全局日志：`logs/global.log`
- `@log_entry(...)` 且当前没有活跃入口时，额外写入 `logs/entries/{module_file}.{entry_func}.log`
- 同时只允许一个活跃入口，内层 `@log_entry(...)` 不会抢占外层入口
- `@log_end(...)` 会截止当前嵌套分支；外层可继续；下游 `@log(...)` 默认从新分支开始

### 3) Mermaid 输出触发条件

必须满足 `@log_entry(enable_mermaid=True)`，并且满足以下任一条件才会落盘：

1. `force_mermaid=True`
2. 装饰器有效级别是 `DEBUG`
3. 入口调用链中发生异常

输出目录：`logs/mermaid/{entry_func}/`

输出文件为 Markdown（`.md`），包含：

- ASCII 调用树
- 性能统计表
- Mermaid `flowchart TD`

### 4) 错误增强日志

任意 `@log/@log_entry/@log_end` 函数发生异常时，都会追加写入 `logs/error.log`，包含：

- 错误摘要（`错误摘要: <异常类型>: <异常信息>`）
- 错误位置（`错误位置: <文件>:<行号> in <函数>`）
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

### 6) 图标约定

- 函数头：`🔵/🟢/🟣`（按 `@log/@log_entry/@log_end` 区分）
- 入参与出参分组：`🧩 [ args ]`、`🧪 [ returns ]`
- warning 与 error：`⚠`、`✖`
- 运行日志正文：保持原样（不额外加图标）

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
  entry_log_dir: entries
  global_log_file: global.log
  console_enabled: true
  mermaid_enabled: false
  mermaid_dir: mermaid
  mermaid_max_size_mb: 10

  # 图标主题（仅作用于函数头与分组）
  icon_theme: default

  icon_themes:
    default:
      function:
        log: "🔵"
        entry: "🟢"
        end: "🟣"
      section:
        args: "🧩"
        returns: "🧪"
    minimal:
      function:
        log: "◽"
        entry: "◻"
        end: "◼"
      section:
        args: "▫"
        returns: "▪"
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
├── entries/
│   └── {module_file}.{entry_func}.log
├── error.log
└── mermaid/
    └── {entry_func}/
        └── 2026-02-09_18-40-00.123.md
```

## 导出 API

```python
from log_decorator import log, log_entry, log_end, logger, logging, parse_obj, load_config
```

## 使用建议

- 入口层函数优先使用 `@log_entry(...)`，业务内部函数按需加 `@log()`
- 在流程边界函数使用 `@log_end(...)` 显式截止当前分支
- 高频函数可关闭 `print_args` / `print_result` 降低日志体积
- 涉及密钥、密码、token 的接口优先自定义 `args_handler`
- 若要稳定留存调用图，建议 `force_mermaid=True`

## 迁移指南（`is_entry` -> `@log_entry`）

```python
# 旧写法（不再支持）
@log(is_entry=True, enable_mermaid=True)
def handler():
    ...

# 新写法
@log_entry(enable_mermaid=True)
def handler():
    ...

# 在流程边界截止当前分支
@log_end()
def finalize_step():
    ...
```
