# 设计说明

## 设计概览
- 在 `IntentService._post_process_result` 新增 `answer` 解析逻辑。
- 在 `chat_general_service` 新增 `_post_process_and_route_type3`。
- 在 `handle_chat_general` 增加 `elif result_type == 3` 分支。

## 关键设计点
1. `answer` 解析
- 来源：`results[0].question`。
- 规则：按 `\tAnswer:` 切分，取后半段并去空白；不满足格式返回空字符串。

2. type=3 分流
- 前置校验：`result_dict.answer` 非空，且 `results[0].question` 可解析出 `returnQuestion`。
- 数据查询：`await asyncio.to_thread(server.judgeQuery, request.question, returnQuestion)`。
- 提示词拼接：`answer + "\n\n" + str(judge_result) + "\n\n" + request.question`。
- 路由目标：固定 `"通用"`。

3. 异常与降级
- `judgeQuery` 抛异常、返回空、answer 缺失、returnQuestion 无法解析：统一返回 `None`，由上层降级通用问答。

## 兼容性
- 保留原有 `type/query/results/similarity/database` 字段。
- type=1 和 type=2 路径不改语义。
