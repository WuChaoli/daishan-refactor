---
name: permission-usage
description: Claude Code 权限设置配置和使用指南。当用户需要配置权限规则、理解权限语法、保护敏感文件、自动化命令执行、解决权限问题，或提到"permissions"、"权限设置"、"allow/ask/deny规则"、"保护文件"、"自动接受权限"、"权限配置"时使用。涵盖权限规则语法（allow、ask、deny）、通配符模式（:* 和 *）、规则评估顺序、安全最佳实践、常见配置场景和模板。
---

# Claude Code 权限设置

配置和使用 Claude Code 权限系统，控制 Claude 可以执行的操作。

## 快速开始

### 基本配置

在 `~/.claude/settings.json` 或项目的 `.claude/settings.local.json` 中配置权限：

```json
{
  "permissions": {
    "allow": ["Bash(npm run:*)"],
    "ask": ["Bash(git push:*)"],
    "deny": ["Read(./.env)"]
  }
}
```

### 配置文件位置

- **全局配置**: `~/.claude/settings.json` - 应用于所有项目
- **项目配置**: `.claude/settings.local.json` - 仅应用于当前项目

项目配置会覆盖全局配置。

## 核心概念

### 三种权限类型

| 类型 | 行为 | 使用场景 |
|------|------|----------|
| `allow` | 自动允许 | 安全的常用操作 |
| `ask` | 询问确认 | 需要用户确认的操作 |
| `deny` | 拒绝执行 | 危险或敏感操作 |

### 规则评估顺序

**Deny → Ask → Allow**

第一个匹配的规则确定行为。Deny 规则始终优先。

```json
{
  "permissions": {
    "allow": ["Bash(git:*)"],
    "ask": ["Bash(git push:*)"],
    "deny": ["Bash(git push --force:*)"]
  }
}
```

结果：
- `git status` → 允许
- `git push` → 询问
- `git push --force` → 拒绝

## 权限规则语法

### 匹配所有使用

使用工具名称（不带括号）：

```json
{
  "permissions": {
    "allow": ["Bash", "Read", "Grep"]
  }
}
```

⚠️ **注意**: `Bash(*)` 不匹配所有 Bash 命令，使用 `Bash` 代替。

### 细粒度控制

使用指定符匹配特定操作：

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run build)",
      "Read(./src/**)",
      "WebFetch(domain:github.com)"
    ]
  }
}
```

### 通配符模式

#### `:*` - 前缀匹配（带单词边界）

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(git commit:*)"
    ]
  }
}
```

- `npm run test` ✅ 匹配
- `npm install` ❌ 不匹配

#### `*` - Glob 匹配（无单词边界）

```json
{
  "permissions": {
    "allow": [
      "Bash(git * main)",
      "Bash(* --version)"
    ]
  }
}
```

- `git checkout main` ✅ 匹配
- `node --version` ✅ 匹配

## 常见使用场景

### 场景 1: 保护敏感文件

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)"
    ]
  }
}
```

### 场景 2: 开发环境

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Read(./src/**)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Edit",
      "Write"
    ]
  }
}
```

### 场景 3: 代码审查模式

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(git diff:*)"
    ],
    "deny": [
      "Edit",
      "Write",
      "Bash(git push:*)"
    ]
  }
}
```

## 配置模板

使用预定义模板快速开始：

### 基础模板

```bash
cp assets/template-basic.json ~/.claude/settings.json
```

适用于一般开发，平衡安全性和便利性。

### 安全模板

```bash
cp assets/template-secure.json ~/.claude/settings.json
```

严格的安全配置，保护敏感文件和危险操作。

### 开发模板

```bash
cp assets/template-development.json ~/.claude/settings.json
```

优化的开发环境配置，自动接受编辑操作。

## 详细文档

### 语法规则

详细的权限规则语法、通配符模式和工具特定规则：

```bash
Read references/syntax-guide.md
```

### 配置示例

8+ 种常见场景的完整配置示例：

```bash
Read references/examples.md
```

### 安全最佳实践

安全注意事项、常见错误和审计指南：

```bash
Read references/security.md
```

## 高级配置

### 额外目录访问

```json
{
  "permissions": {
    "additionalDirectories": [
      "../shared-lib/",
      "../docs/"
    ]
  }
}
```

### 默认模式

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

### 禁用绕过权限

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

## 安全警告

⚠️ **Bash 参数约束的局限性**

不要依赖参数约束作为安全边界：

```json
{
  "permissions": {
    "allow": ["Bash(curl https://api.example.com/:*)"]
  }
}
```

这不能防止：
- `curl -X DELETE https://api.example.com/users/1`
- `curl https://api.example.com/../admin`

**替代方案**:
- 使用 Sandbox 模式
- 使用工具级别的拒绝：`deny: ["Bash"]`
- 在 sandbox 配置中限制网络访问

## 故障排除

### 规则不生效

1. 检查配置文件位置（全局 vs 项目）
2. 验证 JSON 语法
3. 确认规则评估顺序（Deny → Ask → Allow）
4. 重启 Claude Code 会话

### 意外被拒绝

1. 检查是否有 deny 规则匹配
2. 验证通配符模式是否正确
3. 使用 `Bash` 而不是 `Bash(*)` 匹配所有命令

### 敏感文件仍可访问

1. 确认 deny 规则语法正确
2. 检查文件路径是否匹配
3. 使用 `**` 匹配子目录

## 最佳实践

1. ✅ 始终保护敏感文件（.env、secrets、credentials）
2. ✅ 对危险操作使用 ask 规则（git push、rm、docker）
3. ✅ 记住规则评估顺序（Deny → Ask → Allow）
4. ✅ 使用工具名称匹配所有使用（`Bash` 不是 `Bash(*)`）
5. ✅ 结合 Sandbox 模式增强安全性
6. ❌ 不要依赖参数约束作为安全边界
7. ❌ 不要使用过于宽泛的 allow 规则

## 相关资源

- **Sandbox 设置**: 了解如何使用沙箱模式增强安全性
- **Managed Settings**: 组织级别的权限管理
- **Bash Permission Limitations**: Bash 权限的详细限制说明
