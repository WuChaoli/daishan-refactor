---
name: lsp-usage
description: Claude Code LSP 安装、配置和使用指南。使用 LSP 后,Claude Code 能进行语义级别的代码理解,包括跳转到定义、查找引用、实时诊断等功能,而不是依赖文本搜索。当需要为编程语言配置 LSP 支持、验证 LSP 功能、排查 LSP 故障时使用此技能。
---

# LSP Setup - Claude Code 语言服务器协议配置指南

## 概述

LSP (Language Server Protocol) 为 Claude Code 提供了语义级别的代码理解能力。启用 LSP 后,代码导航从数十秒的文本搜索缩短到毫秒级的语义跳转 (~50ms),显著提升中大型项目的开发效率。

**核心能力:**
- 精确跳转到定义 (goToDefinition)
- 查找所有引用 (findReferences)
- 实时诊断和错误提示
- 悬停类型信息 (hover)
- 文档符号概览 (documentSymbol)
- 工作区符号搜索 (workspaceSymbol)

## 快速入门

### 步骤 1: 添加插件市场

```bash
# 添加 Piebald-AI 社区市场
/plugin marketplace add Piebald-AI/claude-code-lsps
```

### 步骤 2: 安装语言插件

```bash
# 在 Claude Code 中运行
/plugin
# 在 "Marketplaces" 标签中找到对应语言插件并安装
# 例如: Python (Pyright)、TypeScript (vtsls)、Go (gopls) 等
```

安装后重启 Claude Code 使插件生效。

### 步骤 3: 验证安装

在 Claude Code 中测试:

```
> 跳转到 [function_name] 的定义

# 预期结果: 直接跳转到精确位置
"[function_name] 函数在 src/utils/helpers.ts 的第 42 行定义"

# 如果看到文本搜索提示,说明 LSP 未正常工作
"我在以下文件中找到了几个 [name] 的引用..."
```

## 语言服务器安装

详细的安装命令和配置说明请参考:

- **[languages.md](references/languages.md)** - 主流编程语言的 LSP 服务器安装命令
- **[troubleshooting.md](references/troubleshooting.md)** - 故障排除和常见问题解决

### 常用语言快速安装

```bash
# Python (Pyright)
npm install -g pyright

# TypeScript/JavaScript (vtsls)
npm install -g @vtsls/language-server typescript

# Go (gopls)
go install golang.org/x/tools/gopls@latest

# Rust (rust-analyzer)
rustup component add rust-analyzer

# C/C++ (clangd)
brew install llvm  # macOS
sudo apt-get install clangd  # Ubuntu

# Java (jdtls)
brew install jdtls  # macOS
```

## 核心功能

### goToDefinition - 跳转到定义

精确跳转到函数、类、变量的定义位置。

```
> 跳转到 handleRequest 的定义
> processData 中使用的 ReturnType 的定义是什么?
```

**LSP 工作:** 直接返回精确位置
**文本搜索:** 返回多个可能的匹配结果

### findReferences - 查找引用

列出符号在代码库中的所有引用位置。

```
> 查找 UserService 类的所有引用
> formatDate 函数的引用有哪些? 按文件分类显示
```

**LSP 工作:** 精确的引用位置和类型
**文本搜索:** 可能误匹配字符串或注释

### documentSymbol - 文档符号

获取文件的层次结构视图。

```
> auth.service.ts 中定义了哪些类和函数?
> DatabaseConnection 类中有哪些公共方法?
```

### workspaceSymbol - 工作区符号

跨整个项目查找符号定义。

```
> ConfigurationManager 类在哪里定义?
> 查找 PaymentProcessor 接口
```

### 诊断信息

实时显示代码错误和警告。

```
> 当前文件中有任何类型错误吗?
> 第 23 行的类型错误是什么?
```

## 验证 LSP 功能

### 测试清单

运行以下测试确认 LSP 正常工作:

```bash
# 1. 测试 goToDefinition
> 跳转到 [任意函数] 的定义
# 应返回: "函数在 [文件]:[行号] 定义"

# 2. 测试 findReferences
> 查找 [某个类] 的所有引用
# 应返回: 精确的位置列表,而非搜索结果

# 3. 测试 hover 信息
> [函数名] 的类型签名是什么?
# 应返回: 函数的类型签名

# 4. 检查插件状态
/plugin
# 在 "Installed" 标签查看已安装插件
# 在 "Errors" 标签查看加载错误
```

### 常见错误信号

- ❌ "我正在搜索代码库中的..." → LSP 未工作,回退到文本搜索
- ❌ "在以下文件中找到了几个..." → LSP 未工作,返回多个匹配
- ✅ "[符号] 在 [文件]:[行号] 定义" → LSP 正常工作

## 工作流集成

结合多个 LSP 操作进行复杂代码分析:

```
> 帮我理解这个代码库的身份验证机制
> 1. 用 workspaceSymbol 查找主要的身份验证类
> 2. 跳转到 AuthService 的定义
> 3. 查找所有引用,看看它在哪里被使用
> 4. 检查身份验证模块中的诊断或类型错误
```

手动操作可能需要 10-15 分钟,LSP 结合 Claude 几秒钟完成。

## 多语言项目

Claude Code 根据文件扩展名自动切换语言服务器:

- Python 文件 (.py) → 使用 Pyright
- TypeScript 文件 (.ts) → 使用 vtsls
- Go 文件 (.go) → 使用 gopls

无需手动配置,安装对应插件即可。

## 增强功能

如果遇到 LSP 功能不稳定,可以使用 `tweakcc` 工具应用补丁:

```bash
tweakcc
```

该工具会自动识别 Claude Code 安装方式(npm 或原生)并应用必要修改。

## 禁用 LSP

临时禁用 LSP:

```bash
ENABLE_LSP_TOOL=0 claude
```

插件不会被卸载,只是在当前会话中不激活。

## 故障排除

遇到问题时的排查步骤:

### 1. 确认插件已安装

```bash
/plugin
# 查看 "Installed" 标签
```

### 2. 检查语言服务器二进制

```bash
which pyright      # 检查是否在 PATH 中
which gopls
which rust-analyzer
```

### 3. 清除插件缓存

```bash
rm -rf ~/.claude/plugins/cache
exit
claude  # 重启
```

### 4. 查看错误详情

```bash
/plugin
# 打开 "Errors" 标签
```

详细的故障排除指南请参考 [troubleshooting.md](references/troubleshooting.md)

## 团队配置

将插件市场配置添加到项目 `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": [
    "Piebald-AI/claude-code-lsps"
  ],
  "enabledPlugins": ["language-python"]
}
```

协作者信任仓库后,Claude Code 会提示安装配置的插件。

## 常见问题

**Q: LSP 是免费的吗?**
A: 是的。插件开源,无需额外付费。只需为 Claude Code 的使用量付费。

**Q: 可以为不支持的语言创建自定义插件吗?**
A: 可以。通过 `.lsp.json` 配置文件指定语言服务器命令。详见官方文档。

**Q: LSP 可以离线工作吗?**
A: 可以。LSP 服务器本地运行,但 Claude Code 的 AI 功能仍需联网。

**Q: 性能影响有多大?**
A: 中小项目额外消耗 200-500MB 内存。相比从几十秒缩短到 50ms 的语义导航,这个开销是值得的。

## 参考资料

- **[languages.md](references/languages.md)** - 各语言 LSP 服务器安装命令
- **[troubleshooting.md](references/troubleshooting.md)** - 详细故障排除指南
- 官方文档: [code.claude.com](https://code.claude.com)
