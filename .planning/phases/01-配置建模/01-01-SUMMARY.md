---
phase: 01-配置建模
plan: 01
subsystem: config
tags: [query_chat, settings, env_override, fallback]
requires: []
provides:
  - query_chat.enabled 配置开关
  - 启动阶段 query_chat 配置校验与降级告警
  - replace_economic_zone 配置驱动降级路径
affects: [02-聊天工具接入, 03-测试回归]
tech-stack:
  added: []
  patterns: [配置驱动开关, 启动时校验告警, 服务层前置降级]
key-files:
  created:
    - src/rag_stream/tests/test_query_chat_config.py
    - src/rag_stream/tests/test_query_chat_validation.py
  modified:
    - src/rag_stream/src/config/settings.py
    - src/rag_stream/src/services/chat_general_service.py
    - src/rag_stream/config.yaml
    - src/rag_stream/tests/test_chat_general_service.py
key-decisions:
  - "query_chat.enabled 默认 true，兼容现有行为"
  - "配置不完整仅告警并降级，不阻断启动"
  - "DEBUG 日志展示脱敏 api_key（***）"
patterns-established:
  - "配置域字段统一通过 settings + QUERY_CHAT_* 覆盖"
  - "服务层在调用外部 AI 前先做 enabled/完整性检查"
requirements-completed: [CFG-01, CFG-02]
duration: 6 min
completed: 2026-02-28
---

# Phase 1 Plan 01: 配置模型与加载逻辑落地 Summary

**为 query 清理能力补齐可控开关、启动校验告警和运行时降级路径，确保配置缺失不阻断主流程。**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-28T02:42:15Z
- **Completed:** 2026-02-28T02:48:00Z
- **Tasks:** 4
- **Files modified:** 6

## Accomplishments
- `QueryChatConfig` 新增 `enabled` 字段并支持 `QUERY_CHAT_ENABLED` 环境变量覆盖。
- `load_settings()` 增加启动阶段配置校验，缺少 `api_key/base_url` 时写 WARN，DEBUG 输出脱敏配置。
- `replace_economic_zone` 增加禁用与配置不完整两条降级分支，直接透传原 query。

## Task Commits

Each task was committed atomically:

1. **Task 1+2: 配置字段与启动校验** - `6c72ed2` (feat)
2. **Task 3: 服务层配置降级检查** - `ea250e3` (feat)
3. **Task 4: 配置示例更新** - `9f0074f` (docs)

**Plan metadata:** pending

## Files Created/Modified
- `src/rag_stream/src/config/settings.py` - 增加 enabled、布尔环境变量覆盖、启动校验与脱敏日志
- `src/rag_stream/src/services/chat_general_service.py` - 增加 disabled/misconfigured 降级检查
- `src/rag_stream/config.yaml` - 增加 `query_chat.enabled` 示例与说明
- `src/rag_stream/tests/test_query_chat_config.py` - 覆盖 YAML 加载与 env 覆盖场景
- `src/rag_stream/tests/test_query_chat_validation.py` - 覆盖校验告警与脱敏日志
- `src/rag_stream/tests/test_chat_general_service.py` - 覆盖 replace_economic_zone 降级路径

## Decisions Made
- 默认启用，确保旧行为不回退。
- 配置缺失采用 warn+降级，不在配置层抛错阻断业务。
- 日志可观测优先，敏感项严格脱敏。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 拆分测试文件避免任务提交互相耦合**
- **Found during:** Task 1/2 提交流程
- **Issue:** 配置加载测试和校验日志测试写在同一文件，难以按任务提交
- **Fix:** 新增 `test_query_chat_validation.py` 并拆分测试职责
- **Files modified:** src/rag_stream/tests/test_query_chat_config.py, src/rag_stream/tests/test_query_chat_validation.py
- **Verification:** `pytest tests/test_query_chat_config.py tests/test_query_chat_validation.py -q`
- **Committed in:** 6c72ed2

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** 仅改善交付粒度，不影响功能范围。

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 配置基线与降级策略已具备，Phase 2 可直接实现 query_chat 工具调用细节。
- 无阻塞项。

## Self-Check: PASSED

---
*Phase: 01-配置建模*
*Completed: 2026-02-28*
