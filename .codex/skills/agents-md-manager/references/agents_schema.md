# AGENTS Dynamic Block Schema

## Block IDs

1. `PROJECT_STRUCTURE_SNAPSHOT`
2. `RULE_VERSION_HISTORY`
3. `MAINTENANCE_OWNERSHIP`
4. `VALIDATION_COMMANDS`
5. `UPDATE_FREQUENCY_POLICY`
6. `EXCEPTION_APPROVAL_PROCESS`
7. `CONFLICT_PRIORITY`
8. `GLOSSARY`
9. `CHANGE_IMPACT_SCOPE`

## Required Fields

### `PROJECT_STRUCTURE_SNAPSHOT`

- 阈值：文件数、最大深度
- 当前统计：`当前文件数`、`当前最大深度`
- 模式：`full-recursive` 或 `directory-plus-key-files`
- 结构快照：`text` 代码块

### `RULE_VERSION_HISTORY`

- `version`
- `last_updated`
- `change_note`
- `previous_baseline`

### `MAINTENANCE_OWNERSHIP`

- `owner`
- `reviewer`
- `修改权限边界`

### `VALIDATION_COMMANDS`

- `init-blocks`
- `sync`
- `check`
- `diff`
- 返回码约定

### `UPDATE_FREQUENCY_POLICY`

- 结构快照更新频率
- 治理区块更新频率
- 提交前检查要求

### `EXCEPTION_APPROVAL_PROCESS`

- 例外条件
- 审批记录模板
- 失效时间

### `CONFLICT_PRIORITY`

- 固定优先级链路（1-4）

### `GLOSSARY`

- `context-id`
- `active/archived`
- `dynamic block`
- `baseline`

### `CHANGE_IMPACT_SCOPE`

- 影响范围
- 不自动修复范围
- 审计要求

