---
status: testing
phase: 01-配置建模
source: [01-01-SUMMARY.md]
started: 2026-02-28T02:53:58Z
updated: 2026-02-28T03:22:25Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 5
name: 配置不完整时透传 query
expected: |
  enabled=true 但 api_key/base_url 缺失时，replace_economic_zone 返回原 query 并记录 misconfigured 标记。
awaiting: user response

## Tests

### 1. 默认配置启用状态
expected: 在未设置 QUERY_CHAT_ENABLED 时，query_chat.enabled 应为 true。
result: pass

### 2. 环境变量覆盖开关
expected: 设置 QUERY_CHAT_ENABLED=false 后，配置应覆盖为 disabled，且无需改 YAML。
result: skipped
reason: 未设置环境开关

### 3. 配置缺失时非阻断启动
expected: 当 api_key/base_url 缺失时，启动阶段会记录 WARN，但服务仍可继续运行。
result: pass

### 4. 功能禁用时透传 query
expected: enabled=false 时，replace_economic_zone 返回原 query，不调用 AI 改写。
result: pass

### 5. 配置不完整时透传 query
expected: enabled=true 但 api_key/base_url 缺失时，replace_economic_zone 返回原 query 并记录 misconfigured 标记。
result: [pending]

## Summary

total: 5
passed: 3
issues: 0
pending: 2
skipped: 1

## Gaps

none
