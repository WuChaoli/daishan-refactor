# 设计文档

## 设计目标

补齐 `RetrievalRequest` 与 RAGFlow 检索接口的主要参数对齐能力，同时避免破坏旧调用。

## 设计要点

1. 保留已有字段默认值：
   - `page=1`
   - `page_size=10`
   - `similarity_threshold=0.2`
   - `top_k=1024`
2. 新增字段并提供默认值或可选值：
   - `document_ids`
   - `vector_similarity_weight`
   - `rerank_id`
   - `keyword`
   - `highlight`
   - `cross_languages`
   - `metadata_condition`
   - `use_kg`
   - `toc_enhance`
3. 约束校验：
   - 增加模型级校验：`dataset_ids` 与 `document_ids` 至少提供一个。
4. 类型兼容：
   - `rerank_id` 采用 `Optional[Union[str, int]]`，兼容文档描述差异。

## 测试策略

1. 校验新增字段能被 `model_dump()` 输出。
2. 校验仅传 `document_ids` 时可创建请求对象。
3. 校验两者都缺失时抛出错误。
