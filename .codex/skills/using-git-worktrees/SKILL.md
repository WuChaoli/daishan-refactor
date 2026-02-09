---
name: using-git-worktrees
description: 用于开始需要与当前工作区隔离的功能开发时，或在执行实施计划之前——创建具有智能目录选择和安全验证的隔离git工作树
---

# 使用Git工作树

## 概述

Git工作树创建共享同一仓库的隔离工作区，允许同时在多个分支上工作而无需切换。

**核心原则：** 系统的目录选择 + 安全验证 = 可靠的隔离。

**开始时声明：** “我正在使用using-git-worktrees技能来设置隔离的工作区。”

## 目录选择流程

按照以下优先级顺序进行：

### 1. 检查现有目录

```bash
# 按优先级检查
ls -d .worktrees 2>/dev/null     # 首选（隐藏）
ls -d worktrees 2>/dev/null