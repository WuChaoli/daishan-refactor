# 测试用例：handle_personnel_dispatch 函数

## 测试信息
- **测试对象**: `rag_stream/src/services/personnel_dispatch_service.py::handle_personnel_dispatch`
- **测试日期**: 2026-02-04
- **测试工程师**: 王麻子

## 函数签名
```python
async def handle_personnel_dispatch(
    voice_text: str,
    log_manager: LogManager,
    user_id: Optional[str] = None
) -> List[Dict[str, str]]
```

## 业务流程
1. 获取 Dify clients（general_client 用于实体提取，personnel_client 用于人员调度）
2. 使用 general_client 从语音文本中提取实体名称列表
3. 对每个实体并行调用 personnel_client 获取对应的人员ID
4. 返回格式为 `[{"id":"1111"},{"id":"2222"}]` 的人员ID列表

## 测试用例

### TC01: 正常流程 - 单个实体
**描述**: 输入包含单个实体的语音文本，成功提取实体并返回人员ID

**输入**:
- `voice_text`: "请调度张三"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: "test_user_001"

**预期输出**:
```python
[{"id": "1001"}]
```

**验证点**:
- 返回列表长度为 1
- 返回格式为 `[{"id": "..."}]`
- ID 为非空字符串

---

### TC02: 正常流程 - 多个实体
**描述**: 输入包含多个实体的语音文本，成功提取所有实体并返回多个人员ID

**输入**:
- `voice_text`: "请调度张三、李四和王五"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: "test_user_002"

**预期输出**:
```python
[{"id": "1001"}, {"id": "1002"}, {"id": "1003"}]
```

**验证点**:
- 返回列表长度为 3
- 每个元素格式为 `{"id": "..."}`
- 所有 ID 为非空字符串
- 并行调用成功

---

### TC03: 边界情况 - 空语音文本
**描述**: 输入空字符串，应返回空列表

**输入**:
- `voice_text`: ""
- `log_manager`: 有效的 LogManager 实例
- `user_id`: None

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 不抛出异常

---

### TC04: 边界情况 - 未提取到实体
**描述**: 输入不包含实体的语音文本，实体提取返回空列表

**输入**:
- `voice_text`: "今天天气真好"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: "test_user_003"

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 日志记录 "未提取到任何实体"

---

### TC05: 边界情况 - 实体返回空ID
**描述**: 实体提取成功，但人员调度返回空ID

**输入**:
- `voice_text`: "请调度不存在的人"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: "test_user_004"

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 日志记录 "返回空 ID"

---

### TC06: 异常情况 - General Client 未配置
**描述**: DIFY_CHAT_APIKEY_GENRAL_CHAT 环境变量未设置

**输入**:
- `voice_text`: "请调度张三"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: None

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 日志记录 "Dify general_chat client 未配置"
- 不抛出异常到调用方

---

### TC07: 异常情况 - Personnel Client 未配置
**描述**: DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING 环境变量未设置

**输入**:
- `voice_text`: "请调度张三"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: None

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 日志记录 "人员调度 client 未配置"
- 不抛出异常到调用方

---

### TC08: 异常情况 - 实体提取JSON解析失败
**描述**: Dify 返回的实体提取响应不是有效的JSON格式

**输入**:
- `voice_text`: "请调度张三"（模拟 Dify 返回非JSON响应）
- `log_manager`: 有效的 LogManager 实例
- `user_id`: None

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表
- 日志记录 "JSON解析失败"
- 不抛出异常到调用方

---

### TC09: 异常情况 - 人员调度调用失败
**描述**: 调用人员调度 client 时发生异常

**输入**:
- `voice_text`: "请调度张三"（模拟 personnel_client 调用失败）
- `log_manager`: 有效的 LogManager 实例
- `user_id`: None

**预期输出**:
```python
[]
```

**验证点**:
- 返回空列表（或部分成功的ID）
- 日志记录 "调用人员调度 client 失败"
- 继续处理其他实体

---

### TC10: 性能测试 - 大量实体并发
**描述**: 输入包含大量实体的语音文本，测试并发处理能力

**输入**:
- `voice_text`: "请调度张三、李四、王五、赵六、钱七、孙八、周九、吴十、郑十一、王十二"
- `log_manager`: 有效的 LogManager 实例
- `user_id`: "test_user_005"

**预期输出**:
```python
[
    {"id": "1001"}, {"id": "1002"}, {"id": "1003"}, {"id": "1004"}, {"id": "1005"},
    {"id": "1006"}, {"id": "1007"}, {"id": "1008"}, {"id": "1009"}, {"id": "1010"}
]
```

**验证点**:
- 返回列表长度为 10
- 所有实体并行处理
- 响应时间合理（< 5秒）

---

## 测试依赖

### 环境变量
- `DIFY_BASE_RUL`: Dify 服务基础URL
- `DIFY_CHAT_APIKEY_GENRAL_CHAT`: 通用聊天 API Key（用于实体提取）
- `DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING`: 人员调度 API Key

### 外部服务
- Dify 服务（http://172.16.11.60/v1）

### Mock 策略
由于依赖外部 Dify 服务，建议：
1. **集成测试**: 使用真实 Dify 服务（需要网络连接）
2. **单元测试**: Mock `get_client` 和 `run_chat` 方法

---

## 测试数据准备

### 有效实体名称
- 张三、李四、王五、赵六、钱七

### 无效实体名称
- 不存在的人、未知人员

### 特殊字符
- 空字符串、纯空格、特殊符号

---

## 风险与注意事项

1. **外部依赖**: 测试依赖 Dify 服务可用性
2. **异步执行**: 需要使用 `pytest-asyncio` 或类似工具
3. **日志验证**: 需要捕获日志输出进行验证
4. **并发测试**: 需要验证并行调用的正确性
5. **超时处理**: Dify 调用可能超时，需要合理设置超时时间

---

## 审查确认

**开发者审查**:
- [ ] 测试用例覆盖所有关键场景
- [ ] 预期输出符合业务逻辑
- [ ] 测试数据准备充分
- [ ] Mock 策略合理

**审查意见**:
_（待开发者填写）_

**审查日期**: _（待填写）_
