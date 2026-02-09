# Serena MCP 集成指南

本技能提供符号索引功能，当前使用 SQLite 作为后端。Serena MCP 集成正在开发中。

## 当前实现

### SQLite 索引（已实现）

本技能使用 Python AST 和正则表达式提取代码符号：

**支持的语言**：
- Python (AST 解析)
- JavaScript/TypeScript (正则表达式)

**符号类型**：
- 类 (class)
- 函数 (function)
- 文件 (file)

**功能**：
- 符号定义定位
- 符号引用统计
- 文件符号列表
- 符号搜索

## Serena MCP 集成（开发中）

### 使用场景

Serena MCP 提供 LSP 级别的符号分析能力，相比 SQLite 有以下优势：

### 符号级精度

- **精确跳转**: 直接定位到符号定义，而非文本搜索
- **类型感知**: 理解类型继承、接口实现
- **跨文件引用**: 准确追踪跨文件的符号引用

### 性能优势

- **索引缓存**: Serena 维护项目索引，无需重复解析
- **增量更新**: 只重新解析修改的文件
- **LSP 集成**: 利用语言服务器的完整能力

### 支持的语言

Serena 通过 LSP 支持，覆盖更多语言：

- **TypeScript/JavaScript**: 完整类型信息
- **Python**: 类型提示支持
- **Go**: 模块和包管理
- **Rust**: trait 和所有权
- **Java**: 类层次结构
- **C/C++**: 预处理和宏

## 在 Claude Code 中使用 Serena

### 激活项目

在 Claude Code 对话中：

```
请帮我激活当前项目作为 Serena 项目
```

### 符号查找

```
使用 Serena 查找名为 "UserService" 的符号
```

### 查看引用

```
使用 Serena 查找所有调用 "processData" 的地方
```

## 配置选项

### 配置文件

`.architecture-generator.yaml` 中的 `index_type` 选项：

```yaml
# 符号索引类型：auto, sqlite, serena
index_type: auto  # 当前使用 sqlite
```

**说明**：
- `auto`: 自动选择（当前使用 SQLite，未来优先 Serena）
- `sqlite`: 强制使用 SQLite（当前默认）
- `serena`: 保留用于未来 Serena MCP 深度集成

## 未来规划

### Phase 1: Claude Code 集成

- ✅ 文档说明如何在 Claude Code 中使用 Serena
- ✅ 提供 SQLite 索引作为备选方案
- 🔄 用户可在 Claude Code 中直接调用 Serena MCP

### Phase 2: Python 脚本集成（规划中）

- Serena CLI 集成到 Python 脚本
- 支持 Serena 索引导出为 SQLite 格式
- 双模式运行（Serena + SQLite 混合）

### Phase 3: 深度集成（规划中）

- 直接从 Python 调用 Serena MCP API
- 实时符号同步
- 统一查询接口

## 故障排除

### SQLite 索引问题

**症状**: 找不到符号或位置错误

**原因**: AST 解析限制或语法错误

**解决**:
```bash
# 重新生成索引
python scripts/build_symbol_index.py . --output docs/architecture/.cache/symbols.db
```

### Serena 不可用

**说明**: 当前 Python 脚本无法直接调用 Serena MCP

**临时方案**:
1. 使用 SQLite 索引（已实现）
2. 在 Claude Code 中通过自然语言使用 Serena

**示例**:
```
使用 Serena 查找项目中的所有类定义
使用 Serena 分析这个文件的依赖关系
```

### 性能问题

**症状**: 大型项目查询缓慢

**优化**:
1. 使用增量扫描
2. 限制扫描深度
3. 在 Claude Code 中使用 Serena（LSP 缓存）
