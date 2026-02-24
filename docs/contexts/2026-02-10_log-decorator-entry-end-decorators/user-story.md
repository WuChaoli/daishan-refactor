# 用户故事

## 故事 1：API 开发者使用 @log_entry 标记入口

**作为** API 开发者
**我想要** 使用 `@log_entry` 装饰器标记 API 请求处理函数
**以便** 清晰地标识调用链的入口点，并生成独立的日志文件

**场景**：
```python
from log_decorator import log_entry

@log_entry(enable_mermaid=True, message="处理用户登录请求")
def handle_login(username: str, password: str):
    user = authenticate_user(username, password)
    token = generate_token(user)
    return {"token": token, "user_id": user.id}
```

**预期结果**：
- 在 `logs/handle_login.log` 中记录完整的调用链日志
- 如果启用 Mermaid，生成调用图文件
- 日志中清晰显示 "处理用户登录请求" 的开始信息

---

## 故事 2：使用 @log_end 清理调用栈

**作为** 后端开发者
**我想要** 使用 `@log_end` 装饰器标记业务流程的结束点
**以便** 确保调用栈状态被正确清理，避免状态残留影响下一次调用

**场景**：
```python
from log_decorator import log_entry, log_end

@log_entry(enable_mermaid=True)
def process_order(order_id: int):
    validate_order(order_id)
    payment_result = execute_payment(order_id)
    return finalize_order(payment_result)

@log_end(message="订单处理完成")
def finalize_order(payment_result: dict):
    update_order_status(payment_result["order_id"], "completed")
    send_confirmation_email(payment_result["order_id"])
    return {"status": "success", "order_id": payment_result["order_id"]}
```

**预期结果**：
- `finalize_order` 执行完毕后，调用深度被重置为 0
- 当前入口函数标记被清除
- Mermaid 文件被输出到 `logs/mermaid/process_order/`
- 独立日志处理器被关闭

---

## 故事 3：测试工程师隔离测试用例日志

**作为** 测试工程师
**我想要** 在每个测试用例中使用 `@log_entry` 和 `@log_end`
**以便** 隔离每个测试的日志，方便调试和问题定位

**场景**：
```python
import pytest
from log_decorator import log_entry, log_end

@log_entry(message="测试用户注册流程")
def test_user_registration():
    user_data = {"username": "test_user", "email": "test@example.com"}
    result = register_user(user_data)
    assert result["status"] == "success"
    cleanup_test_data(result["user_id"])

@log_end()
def cleanup_test_data(user_id: int):
    delete_user(user_id)
```

**预期结果**：
- 每个测试用例的日志被隔离到独立文件
- 测试结束后调用栈状态被清理，不影响下一个测试
- 日志中清晰显示测试的开始和结束

---

## 故事 4：从 @log(is_entry=True) 迁移

**作为** 现有项目维护者
**我想要** 将现有的 `@log(is_entry=True)` 代码迁移到 `@log_entry`
**以便** 使用新的装饰器 API，保持代码一致性

**迁移前**：
```python
from log_decorator import log

@log(is_entry=True, enable_mermaid=True)
def handle_request(data: dict):
    return process_data(data)
```

**迁移后**：
```python
from log_decorator import log_entry

@log_entry(enable_mermaid=True)
def handle_request(data: dict):
    return process_data(data)
```

**预期结果**：
- 功能完全一致，无行为变化
- 代码更简洁，语义更清晰
- `is_entry` 参数不再可用

---

## 故事 5：灵活使用单独的装饰器

**作为** 开发者
**我想要** 可以单独使用 `@log_entry` 或 `@log_end`，不强制配对
**以便** 根据实际场景灵活选择使用方式

**场景 1：只使用 @log_entry**
```python
@log_entry(enable_mermaid=True)
def simple_task():
    # 简单任务，不需要显式结束
    return "done"
```

**场景 2：只使用 @log_end**
```python
@log_end()
def cleanup_resources():
    # 清理资源，重置调用栈
    close_connections()
```

**预期结果**：
- 两个装饰器都可以独立使用
- 不会因为缺少配对而报错或警告
- 各自的功能正常工作
