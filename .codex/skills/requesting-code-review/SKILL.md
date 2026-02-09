---
name: requesting-code-review
description: 用于完成任务、实现主要功能或合并前，以验证工作是否符合要求
---

# 请求代码审查

调度superpowers:code-reviewer子代理，在问题扩大前发现它们。

**核心原则：** 尽早审查，经常审查。

## 何时请求审查

**必须进行：**
- 在子代理驱动开发中的每个任务之后
- 完成主要功能之后
- 合并到主分支之前

**可选但有价值：**
- 遇到困难时（获取新视角）
- 重构之前（进行基准检查）
- 修复复杂漏洞之后

## 如何请求审查

**1. 获取git SHA：**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 或 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. 调度code-reviewer子代理：**

使用类型为superpowers:code-reviewer的任务工具，填写`code-reviewer.md`中的模板

**占位符：**
- `{WHAT_WAS_IMPLEMENTED}` - 你刚刚构建的内容
- `{PLAN_OR_REQUIREMENTS}` - 它应该实现的功能
- `{BASE_SHA}` - 起始提交
- `{HEAD_SHA}` - 结束提交
- `{DESCRIPTION}` - 简要概述

**3. 根据反馈采取行动：**
- 立即修复严重问题
- 在继续之前修复重要问题
- 记录次要问题供以后处理
- 如果审查者有误，可反驳（并给出理由）

## 示例

```
[刚完成任务2：添加验证函数]

你：在继续之前，我要请求代码审查。

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[调度superpowers:code-reviewer子代理]
  WHAT_WAS_IMPLEMENTED: 会话索引的验证和修复函数
  PLAN_OR_REQUIREMENTS: docs/plans/deployment-plan.md中的任务2
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: 添加了带有4种问题类型的verifyIndex()和repairIndex()

[子代理返回]：
  优点：架构清晰，有实际测试
  问题：
    重要：缺少进度指示器
    次要：报告间隔使用了魔数（100）
  评估：可以继续

你：[修复进度指示器]
[继续任务3]
```

## 与工作流的集成

**子代理驱动开发：**
- 每个任务后都进行审查
- 在问题恶化前发现它们
- 在进入下一个任务前修复问题

**执行计划：**
- 每完成一批（3个任务）后进行审查
- 获取反馈，应用反馈，继续推进

**临时开发：**
- 合并前审查
- 遇到困难时审查

## 注意事项

**绝对不要：**
- 因为“很简单”而跳过审查
- 忽略严重问题
- 带着未修复的重要问题继续推进
- 对合理的技术反馈进行争辩

**如果审查者有误：**
- 用技术理由反驳
- 展示能证明其可行的代码/测试
- 请求澄清

查看模板：requesting-code-review/code-reviewer.md