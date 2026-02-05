# Serena MCP 工具参考

本文档提供 Serena MCP 所有可用工具的完整参考。

---

## 目录

1. [项目管理工具](#项目管理工具)
2. [符号导航工具](#符号导航工具)
3. [代码编辑工具](#代码编辑工具)
4. [分析和诊断工具](#分析和诊断工具)
5. [上下文管理工具](#上下文管理工具)
6. [模式切换工具](#模式切换工具)

---

## 项目管理工具

### activate_project

**描述**: 激活项目以开始使用 Serena 工具

**参数**:
- `project_path` (string, required): 项目根目录的绝对路径

**示例**:
```
激活项目 /Users/username/myproject
```

**注意事项**:
- Serena 同时只能处理一个项目
- 激活后会自动执行入职流程（如果是首次使用）
- 大型项目建议先运行 `serena project index`

---

### index_project

**描述**: 为项目建立索引以加速工具运行

**使用方法**:
```bash
uvx --from git+https://github.com/oraios/serena serena project index
```

**何时使用**:
- 大型项目（>10,000 文件）
- 工具响应缓慢时
- 首次使用新项目时

**效果**:
- 显著提升符号搜索速度
- 减少响应时间
- 优化内存使用

---

## 符号导航工具

### find_symbol

**描述**: 通过符号名精确定位定义和引用

**参数**:
- `symbol_name` (string, required): 要查找的符号名称
- `symbol_type` (string, optional): 符号类型（如 `function`, `class`, `variable`）
- `file_path` (string, optional): 限制在特定文件中查找

**使用场景**:
- "找出所有调用 UserService 的地方"
- "显示这个函数的完整定义"
- "查找这个类的所有子类"

**返回信息**:
- 符号定义位置
- 所有引用位置
- 符号类型和签名
- 相关上下文

**示例用法**:
```
查找符号 "UserService"
找出 "processData" 函数的所有调用
```

---

### get_symbol_definition

**描述**: 获取符号的完整定义

**参数**:
- `symbol_name` (string, required): 符号名称
- `file_path` (string, optional): 文件路径（如果符号名称不唯一）

**返回信息**:
- 完整的函数/类实现
- 参数和返回类型
- 文档注释
- 定义位置

---

### get_symbol_references

**描述**: 获取符号的所有引用位置

**参数**:
- `symbol_name` (string, required): 符号名称
- `include_definition` (boolean, optional): 是否包含定义位置

**返回信息**:
- 所有引用位置的列表
- 每个引用的上下文
- 引用类型（读/写/调用）

---

## 代码编辑工具

### replace_symbol_body

**描述**: 替换符号的完整主体（核心编辑操作）

**参数**:
- `symbol_name` (string, required): 要替换的符号名称
- `new_body` (string, required): 新的实现代码
- `file_path` (string, optional): 文件路径（如果符号名称不唯一）

**优势**:
- 比文本替换更准确
- 保持代码结构完整性
- 避免误改相似代码

**示例用法**:
```
替换 "processData" 函数的实现
重构 "UserService" 类的方法
```

**注意**: 只替换符号主体，不改变签名

---

### insert_after_symbol

**描述**: 在符号后插入代码

**参数**:
- `symbol_name` (string, required): 目标符号名称
- `code` (string, required): 要插入的代码
- `file_path` (string, optional): 文件路径

**使用场景**:
- 在函数后添加新函数
- 在类中添加新方法
- 在语句后添加额外逻辑

---

### rename_symbol

**描述**: 重命名符号及其所有引用

**参数**:
- `old_name` (string, required): 当前符号名称
- `new_name` (string, required): 新符号名称
- `file_path` (string, optional): 文件路径

**效果**:
- 同时更新符号定义
- 更新所有引用位置
- 保持代码一致性

---

## 分析和诊断工具

### analyze_codebase

**描述**: 分析代码库结构和质量

**参数**:
- `scope` (string, optional): 分析范围（`entire` 或 `file`）
- `depth` (integer, optional): 分析深度（默认: 3）

**分析内容**:
- 代码结构
- 依赖关系
- 潜在问题
- 架构模式

**示例用法**:
```
分析整个项目的架构
分析当前文件的结构
```

---

### detect_issues

**描述**: 检测代码中的潜在问题

**检测类型**:
- 潜在 Bug
- 内存泄漏
- 代码异味
- 安全漏洞
- 性能问题

**返回信息**:
- 问题列表
- 严重程度
- 建议修复方案
- 影响范围

**示例用法**:
```
检查这段代码是否存在内存泄漏
检测项目中的潜在 Bug
```

---

### suggest_refactoring

**描述**: 提供重构建议

**参数**:
- `target` (string, required): 目标符号或文件
- `focus` (string, optional): 关注点（如 `performance`, `readability`, `maintainability`）

**建议类型**:
- 提取重复逻辑
- 简化复杂函数
- 改进命名
- 优化性能

---

## 上下文管理工具

### prepare_for_new_conversation

**描述**: 创建当前状态摘要并保存为记忆

**使用场景**:
- 对话接近上下文限制时
- 需要在新对话中继续工作时
- 想保存当前进度时

**工作流程**:
1. 创建当前状态摘要
2. 保存为记忆文件到 `.serena/memories/`
3. 在新对话中要求读取该记忆

**示例用法**:
```
准备新对话摘要
保存当前工作状态
```

---

### read_memory

**描述**: 读取项目记忆文件

**参数**:
- `memory_file` (string, optional): 记忆文件名称（不指定则读取最新）

**记忆内容**:
- 项目架构信息
- 业务逻辑摘要
- 重要决策记录
- 代码风格指南

---

### write_memory

**描述**: 写入新的记忆文件

**参数**:
- `content` (string, required): 记忆内容
- `title` (string, required): 记忆标题
- `category` (string, optional): 记忆分类

**使用场景**:
- 记录重要架构决策
- 保存业务逻辑说明
- 存储项目特定知识

---

## 模式切换工具

### switch_mode

**描述**: 切换工作模式

**参数**:
- `mode` (string, required): 目标模式

**可用模式**:
- `planning`: 规划模式 - 专注于分析和规划
- `editing`: 编辑模式 - 专注于代码修改
- `one-shot`: 一次性完成任务

**示例用法**:
```
切换到规划模式
切换到编辑模式
```

---

## 通用工具

### execute_shell_command

**描述**: 执行 shell 命令（用于自主纠错）

**安全注意事项**:
- 允许执行任意代码
- 使用时应检查执行参数
- 只分析任务可设置 `read_only: true`

**典型用途**:
- 运行测试
- 执行构建
- 安装依赖
- 验证修改

**自主纠错流程**:
1. 尝试修改代码
2. 运行测试验证
3. 如果失败，分析错误
4. 自动修正问题
5. 重新运行测试

---

## 记忆系统工具

### create_onboarding

**描述**: 执行项目入职流程（自动）

**分析内容**:
- 项目结构
- 技术栈
- 关键业务逻辑
- 重要架构决策

**存储位置**:
- `.serena/memories/onboarding.md`

**何时执行**:
- 首次激活项目时自动执行
- 可手动触发重新分析

---

### get_project_context

**描述**: 获取项目上下文信息

**返回信息**:
- 项目类型和语言
- 主要框架和库
- 目录结构
- 重要文件说明

---

## 使用示例

### 场景 1: 符号导航和重构

```
用户: 帮我找出所有调用 UserService.authenticate 的地方

Serena:
1. 使用 find_symbol 查找 "UserService.authenticate"
2. 返回所有引用位置
3. 显示每个引用的上下文

用户: 重构这个函数，添加日志记录

Serena:
1. 使用 get_symbol_definition 获取函数定义
2. 使用 replace_symbol_body 替换实现
3. 确保所有引用处保持一致
```

### 场景 2: 项目分析

```
用户: 分析这个项目的架构

Serena:
1. 使用 activate_project 激活项目
2. 使用 analyze_codebase 分析结构
3. 使用 detect_issues 检测问题
4. 提供优化建议
```

### 场景 3: 上下文延续

```
用户: （接近上下文限制）准备新对话

Serena:
1. 使用 prepare_for_new_conversation 创建摘要
2. 保存到 .serena/memories/
3. 告知用户新对话中如何继续

（新对话）
用户: 读取上次的工作记忆

Serena:
1. 使用 read_memory 读取最新记忆
2. 恢复上下文
3. 继续未完成的任务
```

---

## 工具组合模式

### 分析-修改-验证循环

1. `analyze_codebase` - 分析现状
2. `suggest_refactoring` - 获取建议
3. `replace_symbol_body` - 实施修改
4. `execute_shell_command` - 运行测试
5. `detect_issues` - 验证结果

### 符号探索流程

1. `find_symbol` - 定位符号
2. `get_symbol_definition` - 查看定义
3. `get_symbol_references` - 查看引用
4. `analyze_codebase` - 理解上下文

### 重构工作流

1. `switch_mode(planning)` - 切换到规划模式
2. `analyze_codebase` - 分析代码
3. `suggest_refactoring` - 获取建议
4. `switch_mode(editing)` - 切换到编辑模式
5. `replace_symbol_body` - 实施重构
6. `execute_shell_command` - 运行测试

---

## 最佳实践

### 1. 始终先激活项目

使用任何工具前，先运行：
```
激活项目 /path/to/project
```

### 2. 大型项目先索引

```bash
uvx --from git+https://github.com/oraios/serena serena project index
```

### 3. 利用记忆系统

- 让 Serena 自动执行入职流程
- 在 `.serena/memories/` 中存储重要信息
- 跨对话维持上下文

### 4. 使用模式切换

- 规划阶段: `planning` 模式
- 实施阶段: `editing` 模式
- 简单任务: `one-shot` 模式

### 5. 上下文管理

- 接近限制时使用 `prepare_for_new_conversation`
- 在新对话中读取记忆继续工作

### 6. 安全第一

- 只分析任务设置 `read_only: true`
- 检查 `execute_shell_command` 的参数
- 使用版本控制保护代码

---

## 故障排除

### 工具不响应

**可能原因**:
1. 项目未激活
2. MCP 服务器未启动
3. 项目未索引（大型项目）

**解决方案**:
1. 运行"激活项目 /path/to/project"
2. 检查 http://localhost:24282/dashboard/index.html
3. 运行 `serena project index`

### 符号查找失败

**可能原因**:
1. 符号名称拼写错误
2. LSP 服务器未完全索引
3. 符号在未包含的文件中

**解决方案**:
1. 检查符号名称拼写
2. 等待 LSP 索引完成
3. 确认文件路径正确

### 编辑操作失败

**可能原因**:
1. `read_only` 模式启用
2. 文件权限问题
3. 符号不存在

**解决方案**:
1. 检查 `.serena/config.json` 中的 `read_only` 设置
2. 确认文件可写
3. 使用 `find_symbol` 验证符号存在

---

## 相关资源

- **[完整指南](full-guide.md)** - 安装和配置教程
- **[客户端配置](client-config.md)** - 各客户端配置方法
- **GitHub**: https://github.com/oraios/serena
