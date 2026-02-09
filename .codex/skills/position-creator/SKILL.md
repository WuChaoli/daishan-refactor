---
name: position-creator
description: 为公司职位创建职位模板。当用户提到"创建职位模板"、"生成职位模板"、"定义职位"、"position template"或需要为架构师、产品经理、开发者等职位创建标准化职位定义时使用。创建的模板文件字数控制在600-800字之间,确保AI能够充分理解职位职责。
---

# 职位模板创建器

为公司职位创建标准化模板。职位模板定义职责、工具、技能、文档产出、工作规则和执行后检查清单。

## 工作流程

### 1. 收集职位信息

**必需信息**:
- 职位名称、部门、核心职责(3-5条)

**可选信息**:
- 次要职责、工具、技能、文档类型、特殊规则

### 2. 读取参考资料

- `${CLAUDE_SKILL_ROOT}/assets/position-template.md` - 模板结构
- `${CLAUDE_SKILL_ROOT}/examples/` - 完整示例

### 3. 定制职位模板

**模板结构**(600-800字):

使用 `${CLAUDE_SKILL_ROOT}/assets/position-template.md` 作为模板基础,该模板已增强为600-800字结构,包含:
- 详细的概述说明(2-3句话,包含场景和区别)
- 职责说明(5条核心职责+4条次要职责,每条都有详细说明)
- 工具说明(包含使用场景)
- agents配置(包含使用场景)
- 详细的文档产出(包含格式示例和目录结构)
- 8条工作规则(每条都有原因说明)
- 10步工作流程(每步都有详细操作说明)
- 5个特殊场景处理
- 7项质量检查
- 3个协作接口(包含详细流程和交接内容)

### 4. 创建职位文件

**位置**: `.codex/company/position/[role-name].md`

**验证**:
```bash
wc -w .codex/company/position/[role-name].md
```

## 模板编写指南

### YAML Frontmatter (~50字)

定义职位的元数据:

```yaml
---
role: senior-architect      # 英文小写+连字符
position: 资深架构师        # 中文职位名
department: 技术部          # 部门名称
version: 1.0.0             # 语义化版本
created: 2026-02-02        # 创建日期
updated: 2026-02-02        # 更新日期
skills:
  fixed:
    - doc-location-manager
  role_specific:
    - c4-architecture
    - mermaid-diagrams
agents:
  recommended:
    - name: code-explorer
      purpose: 探索代码库结构
    - name: lite-dev
      purpose: 快速功能实现
---
```

**编写指南**:
- **role**: 英文小写,连字符分隔(如:`product-manager`)
- **position**: 中文职位名称
- **department**: 部门或团队名称
- **version**: 遵循语义化版本规范
- **created/updated**: YYYY-MM-DD格式

### 概述 (~30字)

1-2句话概括角色定位和核心价值:

```
负责系统架构部计和技术决策,确保系统可扩展性、可维护性和技术前瞻性。
```

### 职责 (~100字)

**核心职责**(3-5条): 最重要的职责,使用动词开头,每条一句话。

**次要职责**(2-3条): 辅助性职责,每条一句话。

**示例**:
```
### 核心职责
- 设计系统架构和技术方案
- 制定技术标准和最佳实践
- 评估技术选型和风险
- 指导团队技术实施

### 次要职责
- 参与技术评审和讨论
- 培养团队技术能力
```

### 工具 (~50字)

**必需工具**: 该职位必须使用的工具

**可选工具**: 根据情况使用的工具

**示例**:
```
**必需工具**: Read, Write, Bash
**可选工具**: Grep, Glob, Task
```

### 文档产出 (~120字)

使用表格列出核心文档(3-5个):

| 文档名称 | 位置 | 用途 | 更新频率 |
|---------|------|------|---------|
| 架构设计 | `docs/arch/design.md` | 架构方案 | 每个版本 |
| API文档 | `docs/api/` | 接口说明 | 每次变更 |
| 技术决策 | `docs/arch/adr/` | 决策记录 | 每次决策 |

**文档路径设计最佳实践**:

- 避免文档覆盖:使用时间戳+描述命名(如:`DD-HHMM_description`)
- 同一次执行的所有文档放在同一目录
- 查看活跃上下文:读取 `docs/contexts/.contexts-index.json`(如果存在)
- 功能相关文档:放在 `docs/contexts/YYYY-MM-DD_feature/` 下
- 独立任务:新建 `docs/contexts/YYYY-MM-DD_task/` 目录

### 工作规则 (~80字)

4条核心工作规则,每条一句话,具体可执行:

```
1. 架构设计必须考虑可扩展性和可维护性
2. 技术选型必须进行充分调研和评估
3. 关键决策必须记录架构决策记录(ADR)
4. 代码质量必须符合团队标准和最佳实践
```

### 工作流程 (~150字)

**标准流程**(4-6步): 主要工作流程,每步一句话说明。

**特殊场景**(2-3个): 特殊情况的简要处理方式。

**示例**:
```
### 标准流程
1. **需求分析**: 理解业务需求和技术约束
2. **架构设计**: 设计系统架构和技术方案
3. **技术评审**: 组织评审并收集反馈
4. **方案实施**: 指导团队实施架构方案
5. **文档更新**: 更新架构文档和ADR

### 特殊场景
- **紧急需求**: 快速评估风险,提供最小可行方案
- **技术债务**: 识别和记录技术债务,制定重构计划
```

### 质量检查 (~60字)

4-6项检查项,简短具体:

```
- [ ] 架构设计符合业务需求
- [ ] 技术方案经过充分评估
- [ ] 架构文档完整准确
- [ ] 代码质量符合标准
```

### 协作接口 (~80字)

列出主要协作角色,简短说明协作场景和交接文档:

```
### 与产品经理协作
- **场景**: 需求评审、技术可行性分析
- **交接**: 技术方案文档

### 与开发者协作
- **场景**: 架构实施、技术指导
- **交接**: 架构设计文档、API文档
```

## 字数分配

总字数控制在600-800字之间:

- **YAML frontmatter**: ~50字 (基本信息、技能、agents)
- **概述**: 60-80字 (2-3句话,包含场景和区别)
- **职责**: 150-180字 (5条核心+4条次要,每条有说明)
- **工具**: 60-80字 (必需+可选,包含使用场景)
- **文档产出**: 180-220字 (输入+输出+格式示例+目录结构)
- **工作规则**: 100-120字 (8条规则,每条有原因)
- **工作流程**: 200-250字 (10步标准流程+5个特殊场景)
- **质量检查**: 80-100字 (7项检查)
- **协作接口**: 120-150字 (3个协作角色,包含详细流程)
- **总计**: 600-800字

## 常用技能参考

**必需**:
- `doc-location-manager` - 文档位置管理

**工作流管理**:
- `context-engineering` - 上下文工程(文档归档、上下文管理)
- `brainstorming` - 创意思考和需求探索
- `checkpoint` - 开发检查点管理
- `session-compact` - 会话压缩和清理

**开发流程**:
- `tdd-workflow` - 测试驱动开发(TDD)
- `requesting-code-review` - 请求代码审查
- `commit-commands:commit` - Git提交
- `commit-commands:commit-push-pr` - 提交、推送并创建PR

**架构与设计**:
- `c4-architecture` - C4架构图生成
- `mermaid-diagrams` - Mermaid图表绘制
- `architecture-generator` - 自动生成项目架构文档
- `using-git-worktrees` - Git工作树管理

**Agent相关**:
- `agent-creator` - 创建自定义Agent
- `agent-usage-guide` - Agent使用规范指南
- `personality-creator` - 创建人格模板

**插件开发**:
- `plugin-dev:plugin-structure` - 插件结构指南
- `plugin-dev:command-development` - 命令开发
- `plugin-dev:skill-development` - 技能开发
- `plugin-dev:agent-development` - Agent开发
- `plugin-dev:hook-development` - Hook开发
- `plugin-dev:mcp-integration` - MCP集成

**规则与规范**:
- `rule-creator` - 创建行为规范和工作流规则

**其他工具**:
- `fire-employee` - 删除员工档案

## 快速开始

1. 调用 `/position-creator`
2. 回答职位相关问题
3. 查看生成的模板
4. 验证字数在800字以内
5. 保存到 `.codex/company/position/[role-name].md`

## 注意事项

1. **字数限制**: 800字以内
2. **doc-location-manager必需**: 所有职位模板都必须包含
3. **文档路径规范**: 使用相对路径,明确根目录
4. **规则可执行性**: 规则要具体可执行
5. **task-todo.md必需**: 每个职位模板必须包含任务跟踪文档
6. **每次任务完成后打钩**: 更新task-todo.md并标注完成时间
7. **执行后检查**: 每次任务完成后必须执行检查清单
8. **模板复用**: 创建员工时从模板复制

## 相关资源

- **职位模板**: `${CLAUDE_SKILL_ROOT}/assets/position-template.md`
- **示例职位**: `${CLAUDE_SKILL_ROOT}/examples/`
- **招聘员工**: `/hire-employee`
- **文档位置管理**: `.codex/skills/doc-location-manager`

---

**版本**: 3.0.0 | **更新**: 2026-02-06
**变更**: 简化文件夹结构,将 references 目录内容合并到 SKILL.md,examples 独立存放
