---
phase: 04-补充真实环境测试
plan: 01
subsystem: testing
 tags: [real-env-test, ai-testing, integration-test, python]

# Dependency graph
requires:
  - phase: 03-测试回归
    provides: query_chat 模块和单元测试基础
provides:
  - 真实环境测试脚本
  - 测试数据集（11个测试用例）
  - 命令行测试入口
  - 测试报告生成功能
affects:
  - 03-测试回归
  - 05-部署发布

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 异步测试执行模式
    - 基于模式的验证（should_contain/should_not_contain）
    - 分层测试架构（单元测试+真实环境测试）

key-files:
  created:
    - src/rag_stream/tests/data/real_env_test_cases.json
    - src/rag_stream/tests/test_real_env.py
    - scripts/test_real_env.py
  modified: []

key-decisions:
  - 使用 dry-run 模式支持无 AI 环境下的测试验证
  - 采用基于模式的验证而非精确匹配，适应 AI 输出的不确定性
  - 测试数据集使用 JSON 格式便于维护和扩展
  - 命令行入口和测试逻辑分离，便于集成到 CI/CD

patterns-established:
  - "真实环境测试架构: 数据集(JSON) + 测试引擎(Python) + CLI入口"
  - "模式验证: 使用 should_contain/should_not_contain 进行灵活断言"
  - "跳过机制: 通过 SKIP_REAL_ENV_TEST 环境变量控制执行"

requirements-completed: []

# Metrics
duration: 16min
completed: 2026-02-28
---

# Phase 04-01: 补充真实环境测试 Summary

**创建了真实环境测试套件，使用真实 AI 服务验证端到端企业名改写链路，包含 11 个测试用例覆盖典型场景和边界情况。**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-28T04:06:25Z
- **Completed:** 2026-02-28T04:13:03Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments

1. **测试数据集** (`real_env_test_cases.json`): 11 个测试用例覆盖 4 个类别
   - typical_company (4): 岱山石化、舟山港务集团、浙江石化、大鱼山电厂
   - complex_structure (2): 多企业名、句子中间位置
   - no_company (2): 无企业名 query
   - boundary (3): 空字符串、超长 query、纯标点

2. **测试脚本** (`test_real_env.py`): 完整的测试执行引擎
   - 异步执行支持（asyncio + 30 秒超时）
   - 基于模式的验证（should_contain/should_not_contain）
   - 详细的测试报告（通过/失败统计、耗时分析）
   - dry-run 模式用于无 AI 环境验证
   - 环境变量控制（SKIP_REAL_ENV_TEST、QUERY_CHAT_API_KEY）

3. **命令行入口** (`scripts/test_real_env.py`): 便捷的 CLI 工具
   - `--list`: 列出所有测试用例
   - `--category`: 按类别过滤
   - `--verbose`: 详细输出
   - `--dry-run`: 模拟运行
   - 非零退出码表示测试失败（适合 CI/CD 集成）

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建测试数据集** - `92b0148` (feat)
2. **Task 2: 创建真实环境测试脚本** - `a4956ed` (feat)
3. **Task 3: 创建命令行入口** - `3cea54f` (feat)

## Files Created

- `src/rag_stream/tests/data/real_env_test_cases.json` - 测试数据集（114 行）
- `src/rag_stream/tests/test_real_env.py` - 测试引擎（325 行）
- `scripts/test_real_env.py` - CLI 入口（146 行）

## Decisions Made

1. **使用模式匹配而非精确匹配**: AI 改写输出可能有细微差异，使用 should_contain/should_not_contain 模式验证更灵活可靠。

2. **dry-run 模式**: 支持无 AI 密钥环境下的功能验证，便于开发和 CI 环境测试脚本本身。

3. **类别过滤**: 支持按类别运行测试，便于针对性验证特定场景。

4. **环境变量控制**: 使用 SKIP_REAL_ENV_TEST 跳过测试，QUERY_CHAT_API_KEY 覆盖配置，符合 12-factor 原则。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

1. **路径导入问题**: 项目使用特殊的目录结构（src/rag_stream/src/），需要在测试脚本中正确设置 sys.path。
   - 解决: 在测试脚本中添加路径配置，确保从 rag_stream/src 导入模块正常工作。

2. **JSON 转义问题**: 测试用例中的纯标点符号包含引号，需要正确转义。
   - 解决: 使用 `"\""` 转义双引号。

## User Setup Required

None - no external service configuration required for the test framework itself.

To run tests with real AI:
```bash
# 设置 API 密钥（或配置 config.yaml）
export QUERY_CHAT_API_KEY="your-api-key"

# 运行所有测试
python scripts/test_real_env.py

# 或模拟运行（不调用 AI）
python scripts/test_real_env.py --dry-run
```

## Next Phase Readiness

- 真实环境测试套件已就绪，可用于验证 AI 改写功能
- 测试覆盖典型企业名场景，建议后续补充更多边界情况
- CLI 工具可直接用于 CI/CD 集成

---
*Phase: 04-补充真实环境测试*
*Completed: 2026-02-28*
