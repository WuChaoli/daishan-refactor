# 需求文档

## 背景

`rag_stream` 在调用 `ragflow_sdk` 检索时未显式配置 `vector_similarity_weight`，无法通过项目配置统一管理向量权重策略。

## 需求说明

1. 在配置文件中显式配置 `vector_similarity_weight`，目标值为 `0.7`。
2. 配置关系采用继承：
   - `ragflow` 为基础配置
   - `intent` 为用例配置，可覆盖 `ragflow` 基础值
3. 调用 `RetrievalRequest` 时传入生效权重。
4. 不新增 `.env` 覆盖项。
5. 使用真实环境验证调用成功。

## 验收标准

1. `src/rag_stream/config.yaml` 出现 `vector_similarity_weight: 0.7`。
2. 代码中实际检索请求携带 `vector_similarity_weight`。
3. 存在单元测试覆盖继承与覆盖逻辑。
4. 真实环境调用成功（接口返回 `code == 0`）。
