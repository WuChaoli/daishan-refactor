---
name: architecture-generator
description: 自动生成项目架构文档，包括文件结构树、分层依赖关系图（Mermaid）和符号索引。支持 10+ 种编程语言。在以下场景使用：(1) 用户需要理解项目整体架构时，(2) 开始新项目开发前了解代码组织时，(3) 代码审查或重构前分析依赖关系时，(4) 生成项目文档时。支持增量扫描、配置文件（.architecture-generator.yaml）、分层依赖图。优先使用 Serena MCP（符号级精度），自动降级到 SQLite。输出到 docs/architecture/ 目录。
---

# Architecture Generator

自动生成项目架构文档，帮助 Claude 和开发者快速理解代码库结构。

## 核心功能

1. **文件结构扫描** - 生成项目文件树（遵循 .gitignore）
2. **分层依赖分析** - 自动按节点阈值拆分，生成多层 Mermaid 依赖关系图
3. **符号索引** - 构建可查询的符号数据库（类、函数、变量）
4. **增量扫描** - 只处理修改过的文件，大幅提升性能（80-90%）
5. **多语言支持** - Python、JavaScript、TypeScript、Go、Rust、Java、Ruby、C/C++、C#、PHP

## 快速开始

### 基本用法

```bash
cd /path/to/project
python .claude/skills/architecture-generator/scripts/generate.py .
```

输出到 `docs/architecture/` 目录，包含：
- `README.md` - 主入口（目录和概览）
- `file-structure.md` - 文件结构树
- `dependencies/` - 分层依赖关系图（Mermaid）
- `symbols-index.md` - 符号索引说明

### 使用 Serena MCP（推荐）

本技能优先使用 Serena MCP 提供符号级代码分析。

**重要说明**：
- Serena MCP 是 Claude Code 的扩展，需要在 Claude Code 中激活
- Python 脚本无法直接调用 Serena MCP 工具
- 当前版本使用 SQLite 作为符号索引后端
- 未来版本将支持与 Serena MCP 的深度集成

**在 Claude Code 中使用 Serena**：
```
请帮我激活当前项目作为 Serena 项目
```

**查看 Serena 索引**：
```
使用 Serena 查找项目中的所有类定义
```

如果 Serena 不可用，技能会自动使用 SQLite 模式生成符号索引。

详细配置参见 [Serena 集成指南](references/serena-integration.md)。

### 高级选项

```bash
# 指定输出目录
python scripts/generate.py . --output ./docs/arch

# 限制扫描深度
python scripts/generate.py . --max-depth 3

# 设置依赖图节点阈值（自动分层）
python scripts/generate.py . --threshold 30

# 强制全量扫描
python scripts/generate.py . --full-scan

# 禁用增量扫描
python scripts/generate.py . --no-incremental
```

### 配置文件

创建 `.architecture-generator.yaml`：

```yaml
# 依赖图节点数阈值（自动分层）
node_threshold: 25

# 最大扫描深度
max_depth: null

# 是否启用增量扫描
incremental: true

# 额外的排除模式
exclude:
  - node_modules/
  - __pycache__/

# 输出目录
output_dir: docs/architecture

# 符号索引类型：auto, sqlite, serena
index_type: auto
```

生成示例配置：
```bash
python scripts/config_manager.py /path/to/project --example
```

## 工作流程

### 1. 生成文档

```bash
python scripts/generate.py .
```

### 2. 查看文档

从 [docs/architecture/README.md](docs/architecture/README.md) 开始浏览。

### 3. 查询符号

```bash
# 查找特定符号
python scripts/query_index.py . find User

# 搜索符号
python scripts/query_index.py . search parse

# 查看文件中的符号
python scripts/query_index.py . file src/main.py

# 查看统计信息
python scripts/query_index.py . stats
```

## 典型使用场景

### 场景 1: 理解新项目

**用户**: "帮我理解这个项目的架构"

**Claude 执行流程**:
1. 读取 `docs/architecture/README.md` 获取项目概览
2. 查看 `file-structure.md` 了解文件组织
3. 分析 `dependencies/level-0.md` 理解模块依赖
4. 使用 `query_index.py` 查询关键符号

### 场景 2: 代码导航

**用户**: "找到所有调用 `processData` 函数的地方"

**Claude**:
```bash
python scripts/query_index.py . find processData
```

### 场景 3: 重构支持

**用户**: "重构 `User` 类，需要了解它的所有依赖"

**Claude**:
1. 查看 `User` 类的定义位置（通过符号索引）
2. 分析依赖关系图（查看 dependencies/）
3. 找出所有引用 `User` 类的文件

## Serena MCP 集成

### 优势

- **符号级精度**: 直接定位到符号定义，而非文本搜索
- **类型感知**: 理解类型继承、接口实现
- **性能优势**: 利用 LSP 缓存索引，增量更新

### 降级策略

```python
# 自动检测和降级
if is_serena_available():
    使用 Serena MCP（符号级精度）
else:
    询问用户是否降级到 SQLite
    如果用户同意:
        使用 SQLite（基础符号提取）
    否则:
        跳过符号索引生成
```

详细说明参见 [Serena 集成指南](references/serena-integration.md)。

## 性能优化

### 增量扫描

- 首次运行：全量扫描
- 后续运行：仅扫描修改文件，节省 **80-90%** 时间
- 自动判断：变更比例超过 50% 时自动全量扫描

### 分层依赖图

- 默认节点阈值：25
- 自动按文件夹拆分大型项目的依赖图
- 最多支持 3 层嵌套（level-0, level-1, level-2）

### 性能基准

| 项目规模 | 首次运行 | 增量运行 | 提升 |
|---------|---------|---------|------|
| 小型（<100 文件） | ~2s | ~1s | 50% |
| 中型（100-1000 文件） | ~10s | ~2s | 80% |
| 大型（>1000 文件） | ~60s | ~6s | 90% |

## 资源文件说明

### scripts/

- `utils.py` - 工具函数（.gitignore 解析、文件类型检测）
- `scan_file_structure.py` - 文件结构扫描
- `analyze_dependencies.py` - 依赖关系分析（支持分层）
- `build_symbol_index.py` - 符号索引构建（支持 Serena MCP）
- `query_index.py` - 索引查询接口
- `generate.py` - 主脚本（协调整个流程）
- `incremental_scanner.py` - 增量扫描支持
- `config_manager.py` - 配置文件管理

### assets/templates/

- `README.md.j2` - 主文档模板
- `file-structure.md.j2` - 文件结构模板
- `dependency-graph.md.j2` - 依赖图模板
- `symbols-index.md.j2` - 符号索引说明模板

### references/

- [usage-guide.md](references/usage-guide.md) - 完整使用指南
- [serena-integration.md](references/serena-integration.md) - Serena 集成详细说明

## 故障排除

### 问题: 符号数据库找不到

```bash
# 确认数据库路径
ls docs/architecture/.cache/symbols.db

# 重新生成索引
python scripts/build_symbol_index.py . --output docs/architecture/.cache/symbols.db
```

### 问题: Serena MCP 不可用

**症状**: 看到 "⚠️ Serena MCP not available" 提示

**说明**:
- 当前版本使用 SQLite 作为符号索引后端
- Serena MCP 集成正在开发中
- SQLite 模式已经提供了完整的符号索引功能

**使用 Claude Code 与 Serena 集成**:
```
请使用 Serena 激活当前项目
```

然后可以使用 Serena 的符号查找功能：
```
使用 Serena 查找名为 "UserService" 的符号
```

### 问题: 依赖图为空

可能原因：
1. 项目中没有支持的源代码文件
2. 所有文件都被 .gitignore 排除
3. 依赖检测失败（语法错误）

解决方法：
```bash
# 检查扫描的文件
python scripts/scan_file_structure.py .

# 手动测试依赖分析
python scripts/analyze_dependencies.py . 2>&1 | head -50
```

## 参考资源

- [完整使用指南](references/usage-guide.md) - 详细的使用说明和示例
- [Serena 集成指南](references/serena-integration.md) - Serena MCP 配置和故障排除
- [Mermaid 图语法](https://mermaid.js.org/syntax/flowchart.html)
- [Python AST 模块](https://docs.python.org/3/library/ast.html)
