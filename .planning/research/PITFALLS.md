# Pitfalls Research

**Domain:** 企业名称清理型 query 改写
**Researched:** 2026-02-28
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Prompt 过于开放导致改写过度

**What goes wrong:** 模型重写整句而不只是删除企业名。  
**Why it happens:** 指令只说“优化表达”，没有边界。  
**How to avoid:** Prompt 明确“仅删除企业名称，其他词序尽量不变，仅返回改写后句子”。  
**Warning signs:** 输出出现新增信息、同义改写过多。  
**Phase to address:** Phase 2

---

### Pitfall 2: 外部服务抖动导致主流程失败

**What goes wrong:** LLM 超时/鉴权失败影响通用问答。  
**Why it happens:** 把增强能力当成强依赖。  
**How to avoid:** 失败时回退原句，记录 warning。  
**Warning signs:** `query_normalized` 失败比例上升。  
**Phase to address:** Phase 2

---

### Pitfall 3: 配置命名不一致导致环境不可用

**What goes wrong:** 配置键、env 覆盖键不匹配，运行时报空配置。  
**Why it happens:** 新配置域命名未统一。  
**How to avoid:** 在 `settings` 中集中定义并补测试。  
**Warning signs:** 启动后首次请求即抛鉴权/URL 错误。  
**Phase to address:** Phase 1/3

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| 直接复用旧 `openai` 配置域 | 快速接线 | 与“无 openai 前缀”要求冲突 | 不建议 |
| 不写测试直接改 service | 速度快 | 回归风险高 | 不可接受 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAI SDK | 直接在协程内同步阻塞调用 | 使用 `asyncio.to_thread` |
| config.yaml | 把密钥硬编码进仓库 | 用 env 覆盖敏感项 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| 每请求都长上下文调用 | 延迟上升 | 缩短 prompt，限制 max_tokens | 中高并发 |
| 无超时控制 | 请求挂起 | 显式 timeout | 网络抖动时 |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| 在日志打印原始密钥 | 凭据泄露 | 日志脱敏 + 不记录密钥 |
| 把 API key 写入 config.yaml | 仓库泄露风险 | 仅留占位符，走 env |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| 删除了非企业实体 | 用户问题被误改 | 明确只删企业名并保留句意 |
| 输出不是纯文本 | 下游意图识别受扰 | 强制只返回一句文本 |

## "Looks Done But Isn't" Checklist

- [ ] 清理逻辑成功路径可用，且失败路径已验证原句回退。
- [ ] 配置可从 YAML 读取且可被 env 覆盖。
- [ ] 单测覆盖“改写成功/改写异常”两条路径。
- [ ] 不再依赖旧正则逻辑进行统一替换。

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| 改写过度 | MEDIUM | 收紧 prompt + 增加样例测试 |
| 服务不可用 | LOW | 回退原句，保留链路可用 |
| 配置错误 | LOW | 修正配置键并补配置测试 |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 改写过度 | Phase 2 | 比对输入输出是否仅删企业名 |
| 外部抖动 | Phase 2 | 模拟异常时断言返回原句 |
| 配置不一致 | Phase 1/3 | 配置加载测试通过 |

## Sources

- `src/rag_stream/src/services/chat_general_service.py`
- `src/rag_stream/src/config/settings.py`
- `src/DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py`

---
*Pitfalls research for: query normalization*
*Researched: 2026-02-28*
