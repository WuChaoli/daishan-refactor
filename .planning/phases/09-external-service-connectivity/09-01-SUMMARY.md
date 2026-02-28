---
phase: 09-external-service-connectivity
plan: 01
subsystem: testing
tags: [pytest, integration-testing, connectivity, ci-cd, external-services]

# Dependency graph
requires:
  - phase: 08-intent-classification
    provides: [IntentClassifier, QueryChat, configuration system]
provides:
  - tests/integration/conftest.py - 共享测试 fixtures 和配置
  - tests/integration/test_external_service_connectivity.py - 外部服务连通性测试套件
  - 环境变量跳过控制机制 (SKIP_AI_TEST, SKIP_VECTOR_TEST, SKIP_DB_TEST)
  - 诊断信息格式化功能
  - 10秒超时配置
affects:
  - CI/CD pipeline configuration
  - Integration test suite
  - Deployment verification

tech-stack:
  added: [pytest-asyncio]
  patterns:
    - "Session-scoped fixtures for settings and config status"
    - "Environment variable based skip control"
    - "Diagnostic message formatting for clear failure reporting"
    - "Direct module loading to bypass __init__.py import issues"

key-files:
  created:
    - tests/integration/conftest.py - 共享 fixtures 和诊断辅助函数
    - tests/integration/test_external_service_connectivity.py - 连通性测试套件
  modified: []

key-decisions:
  - "使用 importlib.util 直接加载模块，绕过 utils/__init__.py 的导入问题"
  - "配置验证测试无需外部服务连接，确保在 CI/CD 中始终可运行"
  - "诊断信息隐藏敏感值（API密钥、密码），只显示是否设置"
  - "10秒超时适合 CI/CD 环境快速反馈"

patterns-established:
  - "Fixture-based configuration sharing across test classes"
  - "Environment variable skip control for optional external dependencies"
  - "Structured diagnostic messages with environment and config status"
  - "Separate markers for different test categories (ai_api, vector_store, database, config)"

requirements-completed:
  - INT-01
  - INT-02
  - INT-03
  - INT-04

# Metrics
duration: 8min
completed: 2026-02-28
---

# Phase 09 Plan 01: 外部服务连通性测试 Summary

**创建了外部服务连通性测试套件，支持 AI API、向量库、数据库的自动化连通性验证，适用于 CI/CD 环境。**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-28T08:13:14Z
- **Completed:** 2026-02-28T08:21:35Z
- **Tasks:** 3
- **Files created:** 2

## Accomplishments

1. **共享测试基础设施** - conftest.py 提供 settings、env_status、config_status fixtures
2. **AI API 连通性测试** - 测试 QueryChat 和 Intent Classification API 的连通性
3. **向量库连通性测试** - 测试 RAGFlow 连接和向量检索功能
4. **数据库连通性测试** - 测试 MySQLManager 数据库连接
5. **配置验证测试** - 无需外部服务即可验证配置结构完整性
6. **诊断信息功能** - 测试失败时输出环境变量和配置状态，帮助定位问题

## Task Commits

1. **Task 1: 创建共享测试配置和 fixtures** - `805e54d` (test)
2. **Task 2 & 3: 实现 AI API、向量库和数据库连通性测试** - `070a21a` (feat)

**Plan metadata:** `TBD` (docs)

## Files Created

- `tests/integration/conftest.py` (365 lines) - 共享 fixtures、诊断辅助函数、跳过控制
- `tests/integration/test_external_service_connectivity.py` (388 lines) - 连通性测试套件

## Decisions Made

1. **直接模块加载** - 由于 `utils/__init__.py` 使用 `rag_stream.utils` 包风格导入，与测试路径设置不兼容，使用 `importlib.util` 直接加载模块文件，绕过 `__init__.py`。

2. **配置验证测试分离** - 添加 `TestConfigurationValidation` 测试类，验证配置结构完整性，这些测试不依赖外部服务，确保在 CI/CD 中始终可运行。

3. **敏感信息保护** - 诊断信息只显示 API 密钥、密码等是否设置（True/False），不显示实际值。

4. **10秒超时** - 适合 CI/CD 环境快速反馈，避免长时间等待无响应的服务。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 解决模块导入问题**
- **Found during:** Task 2 (AI API tests implementation)
- **Issue:** `utils/__init__.py` 使用 `from rag_stream.utils.geo_utils import ...` 包风格导入，与测试路径设置不兼容
- **Fix:** 使用 `importlib.util.spec_from_file_location` 直接加载模块文件，绕过有问题的 `__init__.py`
- **Files modified:** tests/integration/test_external_service_connectivity.py
- **Verification:** 测试可以正常收集和执行
- **Committed in:** 070a21a

**2. [Rule 2 - Missing Critical] 添加配置验证测试**
- **Found during:** Task 3 (整体测试结构审查)
- **Issue:** 如果外部服务配置不完整，所有测试都会被跳过，无法验证测试基础设施本身
- **Fix:** 添加 `TestConfigurationValidation` 测试类，验证配置结构，这些测试无需外部服务
- **Files modified:** tests/integration/test_external_service_connectivity.py
- **Verification:** 5个配置验证测试始终通过
- **Committed in:** 070a21a

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** 所有修复都增强了测试套件的健壮性，无范围蔓延。

## Issues Encountered

1. **模块导入路径问题** - `utils/__init__.py` 使用包风格绝对导入，与测试路径设置冲突。通过直接模块加载解决。

2. **LSP 静态分析错误** - 由于动态路径设置，LSP 无法解析部分导入。这是预期行为，不影响运行时。

## User Setup Required

None - 测试套件使用现有配置体系（config.yaml + .env）。

如需运行测试，确保：
1. 安装依赖：`uv sync` 或 `pip install -e .`
2. 配置环境变量或 config.yaml
3. 运行测试：`pytest tests/integration/test_external_service_connectivity.py -v`

## Next Phase Readiness

- 测试基础设施完成，可用于 CI/CD 集成
- 配置验证测试确保配置结构正确性
- 外部服务测试可在配置完整时自动运行

---
*Phase: 09-external-service-connectivity*
*Completed: 2026-02-28*
