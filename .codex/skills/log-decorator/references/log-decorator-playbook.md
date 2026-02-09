# log_decorator Playbook

## 1. 目标与范围

用于本项目 `src/log_decorator/` 的函数日志装饰器接入、排障与参数调优。

## 2. 装饰器参数速查

`@log()` 当前关键参数：

- `print_args`: 是否记录入参
- `print_result`: 是否记录出参
- `print_duration`: 是否记录耗时
- `is_entry`: 是否作为入口函数（生成入口独立日志）
- `message`: 自定义开始文案
- `args_handler`: 自定义入参展示
- `result_handler`: 自定义出参展示
- `enable_mermaid`: 启用 Mermaid 记录器
- `force_mermaid`: 强制落盘 Mermaid 文件
- `log_level`: 装饰器日志级别（字符串或 lambda）

## 3. 默认落盘行为

- 始终写入：`logs/global.log`
- 入口函数额外写入：`logs/{entry_func}.log`
- 入口异常链路追加写入：`logs/error.log`

## 4. Mermaid 生成条件

前置条件：`is_entry=True` 且 `enable_mermaid=True`

满足以下任一条件即生成 `.md`：

1. `force_mermaid=True`
2. 装饰器有效级别为 `DEBUG`
3. 入口调用链发生异常

目录：`logs/mermaid/{entry_func}/`

## 5. 敏感数据脱敏

默认按键名包含匹配（不区分大小写）：

- `api_key` / `key`
- `token`
- `password` / `secret`

建议：对高敏接口优先自定义 `args_handler`，显式输出最小必要字段。

## 6. 常见排障清单

### Mermaid 未输出

1. 确认是否入口函数（`is_entry=True`）
2. 确认是否启用 Mermaid（`enable_mermaid=True`）
3. 确认是否满足触发条件（`force_mermaid` / `DEBUG` / 异常）

### 日志级别不生效

1. 检查 `log_level` 值是否为 `DEBUG/INFO/WARNING/ERROR/CRITICAL`
2. 若使用 lambda，检查返回值与异常处理
3. 检查配置加载优先级（根目录配置 > 包内配置 > 默认配置）

### 参数输出不可读或泄露

1. 实现专用 `args_handler` 和 `result_handler`
2. 验证 handler 异常是否降级且不影响业务
3. 对 token/password/key 字段做显式脱敏

## 7. 推荐落地模式

入口函数：

```python
@log(is_entry=True, enable_mermaid=True)
def api_entry(...):
    ...
```

内部函数：

```python
@log(print_args=False, print_result=False)
def internal_hot_path(...):
    ...
```

敏感接口：

```python
@log(args_handler=lambda args, kwargs: {"uid": args[0], "action": kwargs.get("action")})
def sensitive_api(...):
    ...
```

