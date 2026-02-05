# Architecture Generator - 使用指南

本文档详细说明如何使用 architecture-generator 技能生成项目架构文档。

## 前置条件

### Serena MCP 集成（推荐）

本技能优先使用 Serena MCP 提供符号级代码分析能力。

**重要说明**：
- 当前版本使用 SQLite 作为符号索引后端
- Serena MCP 是 Claude Code 的扩展，需要在 Claude Code 中使用
- Python 脚本无法直接调用 Serena MCP 工具

**在 Claude Code 中使用 Serena**：

```
请帮我激活当前项目作为 Serena 项目
```

**使用 SQLite 索引**（当前默认）：

本技能会自动使用 SQLite 构建符号索引，无需额外配置。

## 完整工作流

### 步骤 1: 生成架构文档

```bash
# 基本用法
cd /path/to/project
python .claude/skills/architecture-generator/scripts/generate.py .

# 输出到 docs/architecture/ 目录
```

**命令行参数**：

```bash
python scripts/generate.py <project-path> [options]

选项：
  --output DIR          输出目录（默认: docs/architecture）
  --max-depth N         最大扫描深度（默认: 无限制）
  --threshold N         依赖图节点阈值（默认: 25）
  --full-scan           强制全量扫描（忽略增量缓存）
  --no-incremental      禁用增量扫描
  --gitignore PATH      自定义 .gitignore 文件
```

### 步骤 2: 查看生成的文档

生成的文档结构：

```
docs/architecture/
├── README.md              # 主入口（从这里开始）
├── file-structure.md      # 文件结构树
├── dependencies/
│   ├── level-0.md        # 顶层依赖关系图
│   ├── level-1-*.md      # 模块级依赖图（自动分层）
│   └── level-2-*.md      # 子模块依赖图（如果需要）
├── symbols-index.md       # 符号索引说明
└── .cache/
    ├── symbols.db        # SQLite 符号数据库
    └── scan_cache.json   # 增量扫描缓存
```

### 步骤 3: 查询符号索引

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

## 配置文件

创建 `.architecture-generator.yaml` 自定义行为：

```yaml
# 依赖图节点数阈值（自动分层）
node_threshold: 25

# 最大扫描深度（null 表示无限制）
max_depth: null

# 是否启用增量扫描
incremental: true

# 额外的排除模式
exclude:
  - node_modules/
  - __pycache__/
  - "*.min.js"

# 输出目录
output_dir: docs/architecture

# 符号索引类型：auto, sqlite, serena
# - auto: 自动选择（当前使用 SQLite，未来优先 Serena）
# - sqlite: 强制使用 SQLite（当前默认）
# - serena: 保留用于未来 Serena MCP 深度集成
index_type: auto

# 是否包含测试文件
include_tests: true
```

**生成示例配置**：

```bash
python scripts/config_manager.py /path/to/project --example
```

**查看当前配置**：

```bash
python scripts/config_manager.py /path/to/project
```

## 高级功能

### 增量扫描

自动跟踪文件修改，只扫描变更的文件：

```bash
# 查看扫描缓存状态
python scripts/incremental_scanner.py /path/to/project

# 清除缓存（下次执行全量扫描）
python scripts/incremental_scanner.py /path/to/project --clear
```

**性能提升**：
- 首次运行：全量扫描
- 后续运行：仅扫描修改文件，节省 80-90% 时间
- 自动判断：变更比例超过 50% 时自动全量扫描

### 分层依赖图

自动按节点阈值拆分大型项目的依赖图：

```bash
# 自定义阈值（默认 25）
python scripts/generate.py . --threshold 50
```

**分层规则**：
- Level 0: 文件夹级别依赖
- Level 1: 子文件夹/模块依赖
- Level 2: 文件级别依赖

### 单独使用各个脚本

#### 文件结构扫描

```bash
python scripts/scan_file_structure.py /path/to/project
```

**输出**：JSON 格式的文件树和统计信息

#### 依赖关系分析

```bash
python scripts/analyze_dependencies.py /path/to/project [gitignore-path] [--threshold N]
```

**支持的依赖检测**：
- **Python**: 基于 AST 的 import 分析（精确）
- **JavaScript/TypeScript**: 正则匹配 import/require（快速）
- **Go**: 解析 import 语句
- **Rust**: 解析 use 语句
- **Java**: 解析 import 语句
- **Ruby**: 解析 require 语句
- **C/C++**: 解析 #include 指令
- **C#**: 解析 using 语句
- **PHP**: 解析 require/include 语句

#### 构建符号索引

```bash
python scripts/build_symbol_index.py /path/to/project --output symbols.db
```

**索引内容**：
- **Python**: 类、函数、异步函数（包含参数和返回类型）
- **JavaScript/TypeScript**: 类、函数、箭头函数
- **Go**: 函数、方法、结构体
- **Rust**: 函数、结构体、trait
- **Java**: 类、接口、方法
- **其他语言**: 基础符号提取

**索引类型选择**：
- **auto**: 自动选择（当前使用 SQLite，未来优先 Serena）
- **sqlite**: 强制使用 SQLite（当前默认）
- **serena**: 保留用于未来 Serena MCP 深度集成

## 性能与优化

### 大型项目支持

- **增量扫描**: 只处理修改过的文件
- **分层依赖**: 避免单图过大
- **深度限制**: 使用 `--max-depth` 控制扫描深度
- **排除模式**: 通过配置文件排除不必要的目录

### 性能基准

| 项目规模 | 首次运行 | 增量运行 | 提升 |
|---------|---------|---------|------|
| 小型（<100 文件） | ~2s | ~1s | 50% |
| 中型（100-1000 文件） | ~10s | ~2s | 80% |
| 大型（>1000 文件） | ~60s | ~6s | 90% |

## 故障排除

### 问题: 符号数据库找不到

```bash
# 确认数据库路径
ls docs/architecture/.cache/symbols.db

# 重新生成索引
python scripts/build_symbol_index.py . --output docs/architecture/.cache/symbols.db
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

### 问题: Serena MCP 当前不可用

**说明**：当前版本使用 SQLite 作为符号索引后端。

**Serena MCP 集成**（规划中）：

Serena MCP 是 Claude Code 的扩展，需要在 Claude Code 中通过自然语言使用：

```
请使用 Serena 激活当前项目
```

**当前方案**（已实现）：

本技能自动使用 SQLite 构建完整的符号索引，无需额外配置。

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
1. 查看 `User` 类的定义位置
2. 分析依赖关系图
3. 找出所有引用 `User` 类的文件

## 参考资源

- [Mermaid 图语法](https://mermaid.js.org/syntax/flowchart.html)
- [Python AST 模块](https://docs.python.org/3/library/ast.html)
- [Serena MCP 文档](../references/serena-integration.md)
