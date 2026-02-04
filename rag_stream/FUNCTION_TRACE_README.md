# 函数调用追踪系统使用说明

## 概述

已为 `source_dispath_srvice.py` 中的所有函数添加了调用追踪功能，可以记录：
- 函数名称和调用时间（精确到秒）
- 输入参数（包括参数名和值，**对象属性会被自动提取**）
- 返回值（对象属性会被自动提取）
- 执行耗时（毫秒）
- 错误信息（如果发生异常）
- **函数执行期间的日志输出**（新增）

## 追踪的函数列表

1. `handle_source_dispatch` - 主入口函数
2. `_get_solid_resource_instruction` - 获取固体资源指令
3. `_query_resource_by_type` - 通用资源查询
4. `handle_emergency_supplies` - 应急物资调度
5. `handle_rescue_team` - 救援队伍调度
6. `handle_emergency_expert` - 应急专家调度
7. `handle_fire_fighting_facilities` - 消防设施调度
8. `handle_shelter` - 避难场所调度
9. `handle_medical_institution` - 医疗机构调度
10. `handle_rescue_organization` - 救援机构调度
11. `handle_protection_target` - 防护目标调度

## 日志文件位置

```
rag_stream/logs/function_trace.log
```

## 日志格式示例

**新格式（YAML，更易读）：**

```yaml
2026-02-03 14:55:04 - handle_source_dispatch
module: src.services.source_dispath_srvice
execution_time_ms: 1234.56
args:
  request:
    _type: SourceDispatchRequest
    _attrs:
      source_type: 应急物资
      business_area: '2'
      number: 5
      accident_event:
        _type: AccidentEventData
        _attrs:
          event_id: evt_001
          event_type: 火灾
  log_manager:
    _type: LogManager
    _attrs:
      session_id: sess_123
return_value:
  - _type: EmergencySupply
    _attrs:
      name: 消防器材
      quantity: 100
logs:
- 'INFO - 开始处理资源调度请求'
- 'INFO - 查询应急物资，区域: 2'
- 'INFO - 找到 2 条匹配资源'
================================================================================
```

**旧格式（JSON，已废弃）：**

```json
{
  "timestamp": "2026-02-03T14:29:51.692623",
  "function_name": "handle_source_dispatch",
  "module_name": "src.services.source_dispath_srvice",
  "args": {
    "request": "<SourceDispatchRequest object>",
    "log_manager": "<LogManager object>"
  },
  "kwargs": {},
  "return_value": {
    "code": 0,
    "message": "success",
    "data": [...]
  },
  "execution_time_ms": 1234.56,
  "error": null
}
================================================================================
```

## 字段说明

- **第一行**: `时间戳 - 函数名`（时间精确到秒）
- **module**: 函数所在的模块路径
- **execution_time_ms**: 函数执行耗时（毫秒）
- **args**: 函数的位置参数
  - 对于对象类型，会显示 `_type`（类名）和 `_attrs`（对象属性）
  - 自动提取对象的公开属性（不包括以 `_` 开头的私有属性）
- **kwargs**: 函数的关键字参数（如果有）
- **return_value**: 函数的返回值
  - 对象会被自动展开显示其属性
- **error**: 如果发生异常，记录异常类型和消息
- **logs**: 函数执行期间捕获的日志输出（新增）

## 使用方式

追踪功能已自动启用，无需额外配置。每次调用被追踪的函数时，都会自动记录到日志文件中。

## 查看日志

```bash
# 查看完整日志（最新的在最上面）
cat rag_stream/logs/function_trace.log

# 查看最近的调用记录（前50行）
head -n 50 rag_stream/logs/function_trace.log

# 实时监控新增日志（注意：新日志会添加到文件开头）
watch -n 1 'head -n 30 rag_stream/logs/function_trace.log'
```

## 注意事项

1. **日志文件大小**: 长时间运行可能导致日志文件变大，建议定期清理或归档
2. **敏感信息**: 日志中会记录参数值和logger输出，注意保护敏感数据
3. **性能影响**: 追踪功能会有轻微的性能开销（通常 < 1ms）
4. **对象序列化**:
   - 对象会自动提取公开属性（不包括 `_` 开头的私有属性）
   - 递归深度限制为3层，防止无限递归
   - 基本类型（str, int, float, bool）不受深度限制
5. **日志顺序**: 最新的记录在文件最上面，方便查看最近的调用
6. **日志捕获**: 自动捕获函数执行期间的所有logger输出

## 扩展到其他文件

如需为其他文件添加追踪功能：

```python
# 1. 导入装饰器
from src.utils.function_tracer import trace_function

# 2. 在函数定义前添加装饰器
@trace_function
async def your_function(param1, param2):
    # 函数实现
    pass
```

## 实现文件

- 追踪器实现: `rag_stream/src/utils/function_tracer.py`
- 应用文件: `rag_stream/src/services/source_dispath_srvice.py`
