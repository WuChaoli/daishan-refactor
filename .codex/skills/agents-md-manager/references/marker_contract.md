# Marker Contract

## Syntax

- Begin marker:
  - `<!-- BEGIN AGENTS-DYNAMIC:<BLOCK_ID> -->`
- End marker:
  - `<!-- END AGENTS-DYNAMIC:<BLOCK_ID> -->`

`<BLOCK_ID>` 必须为大写字母、数字或下划线组合。

## Editable Boundary

- 仅允许脚本改写 Begin/End marker 之间的内容。
- marker 之外的内容视为静态内容，不允许脚本改写。
- 每个 `BLOCK_ID` 必须且只能出现一对 marker。

## Error Codes

- `0`: 成功
- `1`: 校验失败（marker 不配对、缺失区块、结构统计过期）
- `2`: 参数或路径错误

## Typical Failure Cases

1. Begin/End 不对称：
   - `Marker mismatch for <BLOCK_ID>`
2. 区块缺失：
   - `Missing dynamic blocks`
3. 结构统计过期：
   - `Project structure stats are stale`

