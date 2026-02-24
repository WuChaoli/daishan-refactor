# 需求说明

- 目标：调整 `IntentService._judge_daishan_intent_priority` 的分流策略。
- 规则：优先判断【岱山-指令集】和【岱山-指令集-固定问题】。
- 规则：当优先库中的最高相似度 `>= priority_similarity_threshold`（默认 `0.7`）时，直接返回该类别。
- 规则：若优先库均未达到该阈值，则在所有返回结果中按最高相似度进行降级判定。
- 补充：启用 `_get_process_judge_function`，使自定义判定逻辑实际生效。
