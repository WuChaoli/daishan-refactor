# Personality Creator Skill

## 概述

personality-creator 是一个用于创建通用人格模板的技能。人格模板与职位模板分离，可以自由组合，创建具有不同工作风格的员工。

## 核心理念

**职位 + 人格 = 员工**

- **职位模板** (`.codex/company/position/`): 定义"做什么" - 职责、工具、技能
- **人格模板** (`.codex/company/personality/`): 定义"怎么做" - 风格、方式、偏好
- **员工** (`.codex/company/employee/`): 职位 + 人格的组合

## 示例

### 人格类型
- 分析型：逻辑严谨、数据驱动
- 创意型：发散思维、创新导向
- 务实型：结果导向、效率优先
- 协调型：平衡各方、沟通协调

### 组合示例
- 分析型架构师：严谨的技术架构设计
- 创意型架构师：创新的架构方案探索
- 务实型产品经理：快速的需求落地
- 协调型产品经理：平衡的需求管理

## 文件结构

```
.codex/skills/personality-creator/
├── skill.md                              # 主技能文件
├── assets/
│   └── personality-template.md           # 通用人格模板
└── references/
    ├── personality-components.md         # 组件说明
    └── examples.md                       # 示例人格
```

## 使用方法

1. 调用技能：`/personality-creator` 或提到"创建人格模板"
2. 回答关于人格的问题（名称、特征、风格等）
3. 生成的模板保存在 `.codex/company/personality/[人格名称].md`
4. 与职位模板组合创建员工

## 与 role-template-creator 的关系

- **role-template-creator**: 创建职位模板（架构师、产品经理、开发者）
- **personality-creator**: 创建人格模板（分析型、创意型、务实型）
- **组合使用**: 职位 × 人格 = 多样化的员工配置

## 版本

- **版本**: 1.0.0
- **创建日期**: 2026-02-02
