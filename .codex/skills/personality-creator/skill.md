---
name: personality-creator
description: 创建通用人格模板，可与任何职位组合。当用户提到"创建人格模板"、"生成性格模板"、"定义人格"、"personality template"时使用。
---

# 人格模板创建器

## 概述

创建通用人格模板，定义员工的工作风格、沟通方式、决策偏好等，存储在 `.codex/company/personality/` 目录。

**核心理念**：
- 人格与职位**分离**，可自由组合
- 例如：分析型架构师、创意型产品经理、务实型开发者

## 何时使用

- 定义员工性格特征和工作风格
- 创建可复用的人格类型
- 组合职位和人格创建个性化员工

## 工作流程

### 第1步：收集信息

向用户询问：
- 人格名称（如：分析型、创意型、务实型）
- 核心特征（3-5个关键词）
- 沟通、决策、协作风格
- 适合的职位类型

### 第2步：读取参考资料

读取以下文件：
- `${CLAUDE_SKILL_ROOT}/assets/personality-template.md` - 通用模板
- `${CLAUDE_SKILL_ROOT}/references/examples.md` - 示例人格

### 第3步：创建人格文件

1. 确保目录存在：`mkdir -p .codex/company/personality/`
2. 创建文件：`.codex/company/personality/[人格名称].md`
3. 填充模板内容

### 第4步：验证确认

检查：
- [ ] YAML frontmatter正确
- [ ] 核心特征清晰
- [ ] 工作风格具体
- [ ] 适配建议实用

## 人格分类

### 按思维方式
- **分析型**: 逻辑思维、数据驱动
- **创意型**: 发散思维、创新导向
- **务实型**: 结果导向、效率优先
- **理想型**: 愿景驱动、价值导向

### 按行动方式
- **主动型**: 积极进取、快速行动
- **响应型**: 稳健谨慎、深思熟虑
- **平衡型**: 灵活切换、情境适应

### 按社交方式
- **外向型**: 善于沟通、团队协作
- **内向型**: 独立思考、深度专注
- **适应型**: 情境切换、灵活调整

## 使用示例

### 创建员工
```
职位模板 + 人格模板 = 员工
.codex/company/position/architect.md + .codex/company/personality/analytical-type.md
→ .codex/company/employee/analytical-architect.md
```

### 团队配置
- 分析型架构师 + 创意型产品经理 + 务实型开发者
- 创意型架构师 + 协调型产品经理 + 分析型开发者

## 快速开始

1. 调用：`/personality-creator` 或提到"创建人格模板"
2. 回答人格相关问题
3. 查看生成的模板：`.codex/company/personality/[人格名称].md`
4. 与职位模板组合创建员工

---

**版本**: 1.0.0
**日期**: 2026-02-02
