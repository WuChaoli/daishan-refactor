# 任务拆解：补充缺失的测试用例

## 任务信息
- **任务ID**: 04-1630_fix-missing-tests
- **开发者**: 鲁班（TDD开发工程师）
- **创建时间**: 2026-02-04 16:30
- **任务类型**: 测试补充

## 背景

测试文档定义了10个测试用例（TC01-TC10），但测试代码只实现了6个。缺失的TC06-TC09都是异常情况测试，需要使用Mock来模拟异常场景。

## 问题分析

### 缺失的测试用例

| 用例 | 场景 | 需要Mock的对象 |
|------|------|---------------|
| TC06 | General Client未配置 | `get_client("GENRAL_CHAT")` 返回 None |
| TC07 | Personnel Client未配置 | `get_client("PERSONNEL_DISPATCHING")` 抛出 ValueError |
| TC08 | JSON解析失败 | `general_client.run_chat` 返回非JSON响应 |
| TC09 | 人员调度调用失败 | `personnel_client.run_chat` 抛出异常 |

### 技术挑战

1. **Mock策略**: 需要Mock `src.services.dify_client_factory.get_client`
2. **异步Mock**: 需要Mock异步方法 `run_chat`
3. **异常注入**: 需要在特定位置注入异常
4. **日志验证**: 需要验证错误日志是否正确记录

## 任务拆解

### Task 1: 补充TC06 - General Client未配置
**目标**: 测试当 `DIFY_CHAT_APIKEY_GENRAL_CHAT` 未配置时的异常处理

**实现步骤**:
1. 使用 `pytest.MonkeyPatch` 或 `unittest.mock.patch` Mock `get_client`
2. 让 `get_client("GENRAL_CHAT")` 返回 None
3. 调用 `handle_personnel_dispatch`
4. 验证返回空列表 `[]`
5. 验证日志记录包含 "Dify general_chat client 未配置"

**验证点**:
- 返回值为 `[]`
- 不抛出异常到调用方
- 日志记录正确

---

### Task 2: 补充TC07 - Personnel Client未配置
**目标**: 测试当 `DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING` 未配置时的异常处理

**实现步骤**:
1. Mock `get_client` 使其对 "GENRAL_CHAT" 返回正常client
2. 让 `get_client("PERSONNEL_DISPATCHING")` 抛出 ValueError
3. 调用 `handle_personnel_dispatch`
4. 验证返回空列表 `[]`
5. 验证日志记录包含 "人员调度 client 未配置"

**验证点**:
- 返回值为 `[]`
- 不抛出异常到调用方
- 日志记录正确

---

### Task 3: 补充TC08 - JSON解析失败
**目标**: 测试当Dify返回非JSON格式响应时的异常处理

**实现步骤**:
1. Mock `get_client` 返回正常的clients
2. Mock `general_client.run_chat` 返回非JSON响应（如 "这是一段文本"）
3. 调用 `handle_personnel_dispatch`
4. 验证返回空列表 `[]`
5. 验证日志记录包含 "JSON解析失败"

**验证点**:
- 返回值为 `[]`
- 不抛出异常到调用方
- 日志记录包含解析错误信息

---

### Task 4: 补充TC09 - 人员调度调用失败
**目标**: 测试当调用personnel_client失败时的异常处理和容错机制

**实现步骤**:
1. Mock `get_client` 返回正常的clients
2. Mock `general_client.run_chat` 返回正常的实体列表（如 ["张三", "李四"]）
3. Mock `personnel_client.run_chat` 对第一个实体抛出异常，第二个正常返回
4. 调用 `handle_personnel_dispatch`
5. 验证返回部分成功的结果（只包含第二个实体的ID）
6. 验证日志记录包含 "调用人员调度 client 失败"

**验证点**:
- 返回值包含成功的ID
- 失败的实体被跳过，不影响其他实体
- 日志记录包含失败信息
- 不抛出异常到调用方

---

## 技术实现方案

### Mock工具选择
使用 `unittest.mock.patch` 和 `pytest-mock`（如果已安装）

### Mock示例代码

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_tc06_general_client_not_configured(log_manager):
    with patch('src.services.personnel_dispatch_service.get_client') as mock_get_client:
        # Mock get_client 返回 None
        mock_get_client.return_value = None

        result = await handle_personnel_dispatch("请调度张三", log_manager, None)

        assert result == []
```

### 异步Mock注意事项
- 对于异步方法，使用 `AsyncMock` 或 `Mock(return_value=asyncio.coroutine(...))`
- 使用 `asyncio.to_thread` 的地方需要特殊处理

---

## 依赖项检查

### 需要的Python包
- [x] pytest
- [x] pytest-asyncio
- [ ] pytest-mock（可选，可用unittest.mock替代）

### 需要Mock的模块
- `src.services.dify_client_factory.get_client`
- Dify client 的 `run_chat` 方法

---

## 验收标准

- [ ] TC06-TC09 测试用例全部实现
- [ ] 所有测试用例通过
- [ ] 测试覆盖率达到 100%（10/10）
- [ ] 日志验证正确
- [ ] 异常处理路径全部覆盖

---

## 风险与注意事项

1. **Mock复杂度**: 需要正确Mock异步调用和嵌套依赖
2. **测试隔离**: 确保Mock不影响其他测试用例
3. **日志验证**: 需要捕获日志输出进行验证（使用 `caplog` fixture）
4. **异步执行**: 确保异步Mock正确工作

---

## 预计工作量

| 任务 | 复杂度 | 说明 |
|------|--------|------|
| Task 1 (TC06) | 低 | 简单的None返回Mock |
| Task 2 (TC07) | 低 | 简单的异常抛出Mock |
| Task 3 (TC08) | 中 | 需要Mock异步方法返回值 |
| Task 4 (TC09) | 高 | 需要Mock部分失败场景 |

---

**创建时间**: 2026-02-04 16:30
**更新时间**: 2026-02-04 16:30
