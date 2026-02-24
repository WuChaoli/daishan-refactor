# 设计说明

## 配置层

在 `intent_mapping.example.json` 新增参数：

- `priority_similarity_threshold`: 专用于岱山优先分流判断的阈值，默认值 `0.7`。

在 `IntentRecognizerSettings` 增加同名字段，确保判定函数可读取该配置。

## 判定流程

1. 从 `table_results` 中提取两个优先库的最佳候选：
   - `岱山-指令集`
   - `岱山-指令集-固定问题`
2. 若优先候选存在且其相似度 `>= priority_similarity_threshold`，直接返回该候选。
3. 否则，将所有库返回结果展开，取全局最高相似度候选作为降级结果。
4. 若无任何候选，返回 `None`。

## 生效开关

仅当映射中同时存在两张优先表时，返回自定义 `judge_function`；否则走基类默认逻辑，避免影响非岱山场景。
