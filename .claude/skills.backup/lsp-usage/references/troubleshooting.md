# LSP 故障排除指南

本文档提供 LSP 常见问题的诊断步骤和解决方案。

---

## 目录

- [常见错误及解决方案](#常见错误及解决方案)
- [诊断流程](#诊断流程)
- [环境问题](#环境问题)
- [插件问题](#插件问题)
- [性能问题](#性能问题)
- [已知问题](#已知问题)

---

## 常见错误及解决方案

### `No LSP server available for file type`

**含义:** Claude Code 找不到对应文件类型的 LSP 插件

**解决步骤:**

1. 确认插件已安装

   ```bash
   /plugin
   # 打开 "Installed" 标签
   ```

2. 如果未安装,安装对应语言插件

3. 如果已安装但仍报错,检查文件扩展名映射
   - 某些插件只对特定扩展名生效

4. **重启 Claude Code**

   ```bash
   exit
   claude
   ```

**最常见原因:** 安装插件后未重启 Claude Code

---

### `Executable not found in $PATH`

**含义:** Claude Code 找不到语言服务器的二进制文件

**解决步骤:**

1. 检查二进制文件是否存在

   ```bash
   which pyright
   which gopls
   which rust-analyzer
   which clangd
   ```

2. 如果命令未找到,安装语言服务器

   参考 [languages.md](languages.md) 中的安装命令

3. 确认 PATH 包含二进制文件位置

   ```bash
   echo $PATH
   ```

4. 特定语言的 PATH 配置:

   **Go:**
   ```bash
   export PATH=$PATH:$(go env GOPATH)/bin
   ```

   **PHP (Composer):**
   ```bash
   export PATH=$PATH:~/.composer/vendor/bin
   # 或
   export PATH=$PATH:~/.config/composer/vendor/bin
   ```

5. 将 PATH 导出添加到 shell 配置文件:

   ```bash
   # ~/.zshrc 或 ~/.bashrc
   export PATH=$PATH:$(go env GOPATH)/bin
   ```

6. **确认 Claude Code 使用的 shell 配置一致**

   - Claude Code 可能使用不同的 shell
   - 检查 `~/.zshenv` 或 `~/.bash_profile`

---

### 插件已安装但无法激活

**症状:** 插件显示安装成功,但 LSP 功能不可用

**解决步骤:**

1. 清除插件缓存

   ```bash
   rm -rf ~/.claude/plugins/cache
   ```

2. 重启 Claude Code

   ```bash
   exit
   claude
   ```

3. 重新安装插件 (如果需要)

   ```bash
   /plugin
   # 卸载后重新安装
   ```

4. 检查插件加载错误

   ```bash
   /plugin
   # 打开 "Errors" 标签
   ```

---

### LSP 服务器在大文件上崩溃

**症状:** 语言服务器崩溃或响应很慢

**解决步骤:**

1. 增加内存限制

   **Pyright:**
   ```bash
   export PYRIGHT_MEMORY_LIMIT=4096
   ```

2. 优化项目配置

   **Pyright** - 在 `pyrightconfig.json` 中:
   ```json
   {
     "exclude": [
       "**/node_modules",
       "**/.git",
       "large_files/**"
     ]
   }
   ```

   **rust-analyzer** - 在项目中创建 `.rust-analyzer.json`:
   ```json
   {
     "rust-analyzer": {
       "cargo": {
         "loadOutDirsFromCheck": true
       },
       "procMacro": {
         "enable": false
       }
     }
   }
   ```

3. 考虑拆分大文件

4. 对于极大型项目,可能需要:
   - 增加 RAM
   - 使用更快的存储
   - 配置 monorepo 支持

---

### 诊断信息不更新

**症状:** 修改代码后,错误高亮或诊断不刷新

**解决步骤:**

1. 在 Claude Code 中强制刷新

   ```
   > 刷新当前文件的诊断
   ```

2. 检查语言服务器状态

   ```bash
   /plugin
   # 打开 "Errors" 标签
   ```

3. 重启语言服务器

   ```bash
   exit
   claude
   ```

4. 如果问题持续,清除缓存:

   ```bash
   rm -rf ~/.claude/plugins/cache
   ```

---

## 诊断流程

### 步骤 1: 确认问题类型

**LSP 未工作** 的迹象:
- "我正在搜索代码库中的..."
- "在以下文件中找到了几个..."
- 响应时间超过 5 秒

**LSP 正常工作** 的迹象:
- "[符号] 在 [文件]:[行号] 定义"
- 响应时间 < 1 秒
- 精确的类型签名信息

### 步骤 2: 检查插件状态

```bash
/plugin
# 1. "Installed" - 插件是否已安装
# 2. "Errors" - 是否有加载错误
# 3. "Marketplaces" - 市场是否正确配置
```

### 步骤 3: 验证二进制文件

```bash
# 根据你的语言选择
which pyright      # Python
which vtsls        # TypeScript
which gopls        # Go
which rust-analyzer # Rust
which clangd       # C/C++
```

如果未找到,安装语言服务器。

### 步骤 4: 检查环境

```bash
# 检查 PATH
echo $PATH

# 检查 shell 配置
cat ~/.zshrc | grep PATH
cat ~/.bashrc | grep PATH

# 检查 Claude Code 版本
claude --version
```

### 步骤 5: 测试功能

在 Claude Code 中运行:

```
> 跳转到 [某个函数] 的定义
```

观察返回结果是:
- ✅ 精确位置 → LSP 正常
- ❌ 搜索结果 → LSP 未工作

### 步骤 6: 清除并重启

```bash
rm -rf ~/.claude/plugins/cache
exit
claude
```

---

## 环境问题

### Shell 配置不一致

**症状:** 终端中命令可用,但 Claude Code 找不到

**原因:** Claude Code 使用不同的 shell 或配置文件

**解决方案:**

1. 确认 Claude Code 使用的 shell

2. 将 PATH 导出添加到多个配置文件:

   ```bash
   # ~/.zshenv (所有 zsh 会话)
   # ~/.zshrc (交互式 zsh 会话)
   # ~/.bash_profile (登录 bash 会话)
   # ~/.bashrc (交互式 bash 会话)

   export PATH=$PATH:$(go env GOPATH)/bin
   ```

3. 或在 `~/.claude/settings.json` 中配置环境变量:

   ```json
   {
     "env": {
       "PATH": "/usr/local/bin:/usr/bin:/bin:$(go env GOPATH)/bin"
     }
   }
   ```

### 权限问题

**症状:** 无法安装或执行语言服务器

**解决方案:**

```bash
# macOS/Linux
chmod +x ~/.local/bin/*

# 或使用 sudo 谨慎安装
sudo npm install -g pyright
```

---

## 插件问题

### 插件加载失败

**诊断:**

```bash
/plugin
# 查看 "Errors" 标签
```

**常见原因:**
1. 二进制文件缺失 → 安装语言服务器
2. PATH 配置错误 → 修正 PATH
3. 插件版本不兼容 → 更新插件
4. 缓存损坏 → 清除缓存

### 插件市场无法访问

**解决步骤:**

1. 检查网络连接

2. 尝试手动添加市场:

   ```bash
   /plugin marketplace add Piebald-AI/claude-code-lsps
   ```

3. 检查 GitHub 访问:
   ```bash
   curl -I https://github.com
   ```

4. 如果使用代理,配置 Git:

   ```bash
   git config --global http.proxy http://proxy.example.com:8080
   ```

---

## 性能问题

### 内存占用过高

**诊断:**

```bash
# macOS/Linux
top | grep [language-server]

# 或使用 ps
ps aux | grep pyright
ps aux | grep gopls
```

**优化:**

1. 限制语言服务器内存

   ```bash
   export PYRIGHT_MEMORY_LIMIT=2048  # Pyright
   ```

2. 排除不必要的目录

   在配置文件中添加:
   ```json
   {
     "exclude": [
       "**/node_modules",
       "**/dist",
       "**/build",
       "**/.git"
     ]
   }
   ```

3. 对于大型项目:
   - 增加系统 RAM
   - 使用 SSD
   - 分离项目为子模块

### 响应慢

**可能原因:**
1. 首次索引项目
2. 大文件或复杂类型
3. 系统资源不足

**解决方案:**
- 等待初始索引完成
- 优化项目结构
- 关闭不必要的应用
- 增加 RAM

---

## 已知问题

### GitHub Issues

- **#14803**: LSP 插件配置正确但无法识别
- **#15359**: 官方插件缺少实现代码

查看这些问题获取临时解决方法:
[https://github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)

### LSP 功能不稳定

**症状:**
- 某些 LSP 操作有 bug
- UI 不显示 LSP 状态

**解决方案:**

使用 `tweakcc` 工具应用补丁:

```bash
tweakcc
```

该工具会:
1. 自动识别 Claude Code 安装方式 (npm 或原生)
2. 应用必要的修改
3. 修复 LSP 功能

---

## 获取帮助

如果以上方法无法解决问题:

1. **查看详细日志**

   ```bash
   # Claude Code 日志位置
   ~/.claude/logs/
   ```

2. **验证环境**

   ```bash
   # 检查所有环境
   which [language-server]
   echo $PATH
   claude --version
   ```

3. **参考官方文档**

   [https://code.claude.com](https://code.claude.com)

4. **搜索或报告问题**

   [https://github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)

报告问题时请包含:
- 操作系统和版本
- Claude Code 版本
- 语言和语言服务器版本
- 完整的错误信息
- 复现步骤
