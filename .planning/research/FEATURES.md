# Feature Research

**Domain:** Query 预处理（企业名称清理）
**Researched:** 2026-02-28
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 输入句保真（除企业名外基本不变） | 用户希望问句语义不漂移 | MEDIUM | Prompt 与返回校验必须保守 |
| 删除企业名称 | 这是本需求核心目标 | MEDIUM | 需明确“只删企业名，不扩写” |
| 失败可回退 | 外部 LLM 可能不可用 | LOW | 失败返回原句即可 |
| 可配置模型与地址 | 不同环境模型路由不同 | LOW | 走 config + env override |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 可观测日志（改写前后差异） | 快速定位误改写 | LOW | marker 打点即可 |
| 轻量输出约束（返回纯文本） | 降低下游解析成本 | LOW | Prompt 强约束 |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| 一次性做“企业名+地名+行业术语”全清洗 | 想一步到位 | 高误伤，难验证 | 先聚焦企业名清理 |
| 清理后再自动重写问法 | 期望更智能 | 可能改变用户意图 | 只删实体，不改句式 |

## Feature Dependencies

```text
配置加载
  └──requires──> AI 客户端
                     └──requires──> chat_general_service 调用接入
                                          └──requires──> 测试验证与回归
```

### Dependency Notes

- **AI 客户端 requires 配置加载：** 模型/地址/API key 必须先可读。
- **service 接入 requires AI 客户端：** 改写逻辑以客户端为中心。
- **测试 requires service 接入：** 先有调用点，才能验证 success/fallback 行为。

## MVP Definition

### Launch With (v1)

- [ ] 新增 `rag_stream` AI 聊天工具（utils）。
- [ ] `replace_economic_zone` 改为 AI 清理企业名。
- [ ] AI 失败返回原句。
- [ ] 最小单测覆盖成功与失败路径。

### Add After Validation (v1.x)

- [ ] 企业名称词典与提示词联动（减少漏删/误删）。
- [ ] 改写效果采样评估（离线回放）。

### Future Consideration (v2+)

- [ ] 多模型路由（不同场景切换模型）。
- [ ] 批量改写与缓存策略。

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| 企业名删除 | HIGH | MEDIUM | P1 |
| 失败回退原句 | HIGH | LOW | P1 |
| config.yaml 配置化 | HIGH | LOW | P1 |
| 改写前后可观测日志 | MEDIUM | LOW | P2 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Query 清洗 | 规则引擎 | 轻量 LLM | 轻量 LLM + 原句回退 |
| 失败策略 | 静默失败 | 默认模板替换 | 原句透传，最小副作用 |

## Sources

- 代码现状：`src/rag_stream/src/services/chat_general_service.py`
- 参考实现：`src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`

---
*Feature research for: query normalization*
*Researched: 2026-02-28*
