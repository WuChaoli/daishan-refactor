# log_decorator 入口/出口装饰器需求文档

## 背景

当前 `log_decorator` 项目只提供了一个 `@log()` 装饰器，通过 `is_entry=True` 参数来标记入口函数。这种设计存在以下问题：

1. **语义不够清晰**：需要记住 `is_entry` 参数，不如独立装饰器直观
2. **缺少出口标记**：无法明确标记调用链的结束点，导致调用栈状态可能残留
3. **使用场景受限**：在 API 请求处理、业务流程边界、测试用例隔离等场景中，需要更明确的入口/出口控制

## 目标

1. 新增 `@log_entry` 装饰器，替代 `@log(is_entry=True)`，提供更清晰的入口标记
2. 新增 `@log_end` 装饰器，标记调用链结束点并清理调用栈状态
3. 废弃 `is_entry` 参数，简化 API 设计
4. 支持可选配对使用，提供灵活的调用链管理能力

## 功能描述

### 1. @log_entry 装饰器

**功能**：标记函数为调用链的入口点

**行为**：
- 完全替代 `@log(is_entry=True)` 的功能
- 支持所有 `@log` 装饰器的参数（`print_args`、`print_result`、`print_duration`、`message`、`args_handler`、`result_handler`、`enable_mermaid`、`force_mermaid`、`log_level`）
- 创建独立的日志文件 `logs/{entry_func}.log`
- 初始化 Mermaid 记录器（如果 `enable_mermaid=True`）
- 设置当前入口函数标记

**示例**：
```python
from log_decorator import log_entry

@log_entry(enable_mermaid=True, message="API请求开始")
def handle_api_request(user_id: int, action: str):
    # 业务逻辑
    return {"status": "ok"}
```

### 2. @log_end 装饰器

**功能**：标记函数为调用链的结束点，并清理调用栈状态

**行为**：
- 支持所有 `@log` 装饰器的参数
- 执行完毕后清理调用栈状态：
  - 重置调用深度计数器
  - 清除当前入口函数标记
- 触发 Mermaid 文件输出（如果启用）
- 关闭入口函数的独立日志处理器

**示例**：
```python
from log_decorator import log_end

@log_end(message="API请求结束")
def finalize_response(response: dict):
    # 最终处理
    return response
```

### 3. 废弃 is_entry 参数

**变更**：
- 从 `@log()` 装饰器中删除 `is_entry` 参数
- 更新文档，说明使用 `@log_entry` 替代

### 4. 配对使用（可选）

**场景**：
- **API 请求处理**：在路由处理函数上使用 `@log_entry`，在返回响应前使用 `@log_end`
- **业务流程边界**：在复杂业务流程的开始和结束使用，明确边界
- **测试用例隔离**：在测试用例中使用，隔离每个测试的日志

**示例**：
```python
@log_entry(enable_mermaid=True)
def process_order(order_id: int):
    validate_order(order_id)
    result = execute_payment(order_id)
    return finalize_order(result)

@log_end()
def finalize_order(payment_result: dict):
    # 最终处理
    return {"order_id": payment_result["order_id"], "status": "completed"}
```

## 技术约束

1. **向后兼容性**：直接删除 `is_entry` 参数，不保留向后兼容
2. **线程安全**：使用 `threading.local` 管理调用栈状态
3. **错误处理**：装饰器内部错误不应影响业务函数执行
4. **性能影响**：装饰器开销应控制在可接受范围内

## 验收标准

1. `@log_entry` 装饰器功能完整，支持所有 `@log` 参数
2. `@log_end` 装饰器能正确清理调用栈状态
3. 废弃 `is_entry` 参数，代码中不再使用
4. 文档更新完整，包含使用示例和迁移指南
5. 测试覆盖率达到 80% 以上
6. 现有使用 `@log(is_entry=True)` 的代码需要迁移

## 影响范围

- **代码变更**：`decorator.py`、`__init__.py`
- **文档变更**：`README.md`、`UPDATELOG.md`
- **测试变更**：新增测试用例，覆盖新装饰器功能
- **迁移工作**：项目中现有使用 `is_entry=True` 的代码需要更新
