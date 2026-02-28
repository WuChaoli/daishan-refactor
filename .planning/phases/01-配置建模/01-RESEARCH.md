# Phase 1: 配置建模 - Research

**Researched:** 2025-02-28
**Status:** Ready for planning

## 现有实现分析

### 配置系统状态

项目已有一个完善的配置系统：

1. **配置文件**: `src/rag_stream/config.yaml`（已存在 `query_chat` 配置块）
2. **配置类**: `src/rag_stream/src/config/settings.py` 中的 `QueryChatConfig`
3. **环境变量覆盖**: 已支持 `QUERY_CHAT_*` 前缀的环境变量

### 当前实现缺口

| 组件 | 状态 | 说明 |
|------|------|------|
| `query_chat` YAML 配置 | ✅ 已存在 | 包含 api_key, base_url, model, timeout, temperature |
| `QueryChatConfig` 类 | ⚠️ 需修改 | 缺少 `enabled` 字段 |
| 环境变量覆盖 | ✅ 已存在 | QUERY_CHAT_API_KEY, QUERY_CHAT_BASE_URL, QUERY_CHAT_MODEL 等 |
| 降级逻辑 | ❌ 需添加 | `replace_economic_zone` 未检查配置状态 |
| 启动警告 | ❌ 需添加 | 配置无效时应记录 WARN 日志 |

### 目标函数分析

`replace_economic_zone` 位于 `src/rag_stream/src/services/chat_general_service.py`:

```python
async def replace_economic_zone(query: str) -> str:
    """使用 AI 对 query 进行企业名称清理。失败时返回原 query。"""
    # ... 当前实现：总是尝试 AI 调用
```

**当前行为**: 总是执行 AI 调用，没有配置开关  
**目标行为**: 检查配置，未启用时降级到原有逻辑

## 技术方案

### 1. 配置模型扩展

在 `QueryChatConfig` 中添加：
```python
enabled: bool = Field(default=True, description="是否启用 query 清理功能")
```

### 2. 降级逻辑实现

在 `replace_economic_zone` 开头添加：
```python
from src.config.settings import settings

# 检查配置是否启用
if not settings.query_chat.enabled:
    marker("query_normalized_disabled", {"query_len": len(query)})
    return query  # 透传原值，后续正则替换逻辑继续执行
```

### 3. 启动警告

在 `load_settings()` 或配置验证中添加：
```python
# 检查 query_chat 配置有效性
if settings.query_chat.enabled:
    if not settings.query_chat.api_key or not settings.query_chat.base_url:
        logger.warning("QUERY_CHAT 配置不完整，功能将降级运行")
```

### 4. 敏感信息脱敏

日志中 API key 使用 `***` 替代，已在现有代码中通过 marker 机制隐式处理。

## 文件变更清单

1. **修改**: `src/rag_stream/src/config/settings.py`
   - `QueryChatConfig` 添加 `enabled` 字段
   - 添加配置验证逻辑（启动时警告）

2. **修改**: `src/rag_stream/src/services/chat_general_service.py`
   - `replace_economic_zone` 添加配置检查

3. **配置示例**: `src/rag_stream/config.yaml` 已有 `query_chat` 块，文档化 `enabled` 字段

## 依赖关系

无外部依赖，仅修改现有配置系统。

## 测试建议

1. **单元测试**: 测试 `enabled=False` 时返回原值
2. **集成测试**: 测试环境变量覆盖生效
3. **降级测试**: 测试配置无效时的警告日志

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 默认启用可能影响现有行为 | `enabled` 默认值为 `True`，保持向后兼容 |
| 环境变量命名冲突 | 使用 `QUERY_CHAT_ENABLED` 前缀，与现有命名一致 |
| 配置加载顺序问题 | 在 `load_settings()` 中统一验证所有配置 |

## 关键技术细节

### Pydantic 验证器模式

参考现有代码中的验证器模式：
```python
@field_validator("timeout")
@classmethod
def validate_timeout(cls, v: int) -> int:
    if v <= 0:
        raise ValueError(f"timeout 必须大于 0，当前值: {v}")
    return v
```

### Marker 日志系统

项目使用自定义 marker 系统进行结构化日志：
```python
marker("event_name", {"key": "value"}, level="WARNING")
```

### 环境变量加载顺序

1. `.env` 文件通过 `load_dotenv()` 加载
2. `load_from_yaml_with_env_override()` 应用环境变量覆盖
3. 配置优先级：环境变量 > 配置文件 > 默认值

## 建议的计划结构

### Wave 1: 配置模型增强
- 任务 1: 添加 `enabled` 字段和验证器
- 任务 2: 添加启动时配置验证和警告

### Wave 2: 服务层集成
- 任务 3: 在 `replace_economic_zone` 中集成配置检查
- 任务 4: 验证降级行为

---

*Phase: 01-配置建模*  
*Research completed: 2025-02-28*
