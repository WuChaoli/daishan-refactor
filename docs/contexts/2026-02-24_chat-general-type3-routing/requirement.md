# 需求说明

## 背景
- `intent_mapping.example.json` 已新增映射：`"岱山-指令集-固定问题": 3`。
- 当前 `chat_general_service` 仅区分 type=1 与其他(type2路径)，未实现 type=3。

## 目标
- 在不影响 type=1/2 现有行为的前提下，新增 type=3 分流处理。
- `intent_service.process_query` 返回体补充顶层 `answer` 字段。
- type=3 时调用 `DaiShanSQL.Server.judgeQuery(query, returnQuestion)`，将 `answer + judgeQuery结果 + 原问题` 拼接后走 `chat_with_category("通用", ...)`。

## 约束
- 失败兜底：`answer` 缺失、`judgeQuery` 异常或空结果时，直接降级 `chat_with_category("通用", request)`。
- `judgeQuery` 第二参数使用 `Question:` 与 `\tAnswer:` 之间的文本。
- 提示词中的 `answer` 使用 `\tAnswer:` 后半段。
