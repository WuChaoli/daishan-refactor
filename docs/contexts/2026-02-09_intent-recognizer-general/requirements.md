# 需求说明

## 背景
从 `src/rag_stream/src/services/intent_judgment.py` 提炼出可复用的通用意图识别逻辑，减少业务耦合。

## 目标
1. 获取用户问题 query。
2. 使用 `config.yaml` 的查询表（database）与意图映射。
3. 对所有返回结果按相似度排序，选择最高相似度对应查询表。
4. 返回该查询表对应意图映射，以及该表的查询结果列表。

## 非目标
- 不改动 `IntentService` 路由策略（当前仍按 type==1 走 type1，其余走 type2）。
- 不改动 RAGFlow SDK 调用细节。
