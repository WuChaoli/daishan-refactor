---
phase: 02-ai-改写接入
plan: 01
subsystem: ai-processing
requirements-completed:
  - NORM-01
  - NORM-02
  - NORM-03
  - SAFE-01

# Dependency graph
requires:
  - phase: 01-配置建模
    provides: QueryChatConfig 配置对象
provides:
  - 异步 rewrite_query 函数
  - 内容验证 _validate_content 方法
  - 统计指标标记（attempt/success/api_error/content_invalid）
affects:
  - replace_economic_zone 函数（将通过 asyncio.to_thread 调用）

# Tech tracking
tech-stack:
  added: []
  patterns:
    - asyncio.to_thread 包装同步调用
    - 输入验证 + 异常降级
    - marker 统计指标

key-files:
  created: []
  modified:
    - src/rag_stream/src/utils/query_chat.py

key-decisions:
  - 使用 asyncio.to_thread 包装同步 QueryChat 调用，保持向后兼容
  - 内容验证检测空内容、JSON、指令性文字、多行文本
  - 任何异常都返回原 query（降级策略）
  - marker 命名遵循小写下划线规范（query_chat.xxx）

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 02 Plan 01: AI 改写接入 Summary

**异步 query 改写接口，支持内容验证和统计指标，完整向后兼容**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-28T03:18:32Z
- **Completed:** 2026-02-28T03:20:47Z
- **Tasks:** 4
- **Files modified:** 1

## Accomplishments

- 实现异步 `rewrite_query` 函数，支持 `asyncio.to_thread` 调用
- 添加 `_validate_content` 内容验证，检测异常 AI 响应
- 完善统计指标（attempt/success/api_error/content_invalid）
- 保持向后兼容，原有同步接口无需修改

## Task Commits

Each task was committed atomically:

1. **Task 1: Add async rewrite_query function** - `4eb6213` (feat)
2. **Task 2: Add content validation logic** - `2bcd023` (feat)
3. **Task 3: Enhance statistics markers** - `99a337f` (feat)
4. **Task 4: Verify complete flow and backward compatibility** - Verification only

## Files Created/Modified

- `src/rag_stream/src/utils/query_chat.py` - 主要实现文件
  - 添加 `asyncio` 导入
  - 添加 `rewrite_query` 异步函数
  - 添加 `_validate_content` 静态方法
  - 更新 marker 统计标签

## Interfaces

### 异步接口（新增）
```python
async def rewrite_query(query: str, config: QueryChatConfig) -> str:
    """异步改写 query，删除企业名称。"""
```

### 同步接口（向后兼容）
```python
def rewrite_query_remove_company(query: str) -> str:
    """同步改写（全局函数）"""

class QueryChat:
    def rewrite_query_remove_company(self, query: str) -> str:
        """同步改写（实例方法）"""
```

### 内容验证
```python
@staticmethod
def _validate_content(text: str, original: str) -> tuple[bool, str]:
    """验证 AI 返回的内容是否有效。"""
```

## Decisions Made

- **降级策略**：任何异常都返回原 query，不中断业务流程
- **内容验证规则**：
  - 空内容 → 回退
  - JSON 格式 → 回退
  - 指令性文字（请/应该/建议/需要/可以）→ 回退（除非原句也包含）
  - 多行文本（>2 行）→ 回退
- **统计指标命名**：统一使用 `query_chat.xxx` 前缀

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- AI 改写接入完成
- `replace_economic_zone` 可调用 `rewrite_query` 进行异步改写
- 配置系统已在 Phase 1 完成，可直接使用

---
*Phase: 02-ai-改写接入*
*Completed: 2026-02-28*
