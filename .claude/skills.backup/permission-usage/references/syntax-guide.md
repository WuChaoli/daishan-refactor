# 权限规则语法指南

## 规则格式

权限规则遵循格式 `Tool` 或 `Tool(specifier)`。

## 规则评估顺序

当多个规则可能匹配相同的工具使用时，规则按以下顺序评估：

1. **Deny 规则首先被检查**
2. **Ask 规则其次被检查**
3. **Allow 规则最后被检查**

第一个匹配的规则确定行为。这意味着 **deny 规则始终优先于 allow 规则**。

## 匹配工具的所有使用

要匹配工具的所有使用，使用不带括号的工具名称：

| 规则 | 效果 |
|------|------|
| `Bash` | 匹配所有 Bash 命令 |
| `WebFetch` | 匹配所有网络获取请求 |
| `Read` | 匹配所有文件读取 |

⚠️ **重要**: `Bash(*)` 不匹配所有 Bash 命令。要允许或拒绝工具的所有使用，使用工具名称：`Bash`，而不是 `Bash(*)`。

## 使用指定符进行细粒度控制

在括号中添加指定符以匹配特定的工具使用：

| 规则 | 效果 |
|------|------|
| `Bash(npm run build)` | 匹配确切的命令 `npm run build` |
| `Read(./.env)` | 匹配读取当前目录中的 `.env` 文件 |
| `WebFetch(domain:example.com)` | 匹配对 `example.com` 的获取请求 |

## 通配符模式

Bash 规则有两种通配符语法：

### `:*` - 前缀匹配（带单词边界）

- **位置**: 仅在模式末尾
- **行为**: 前缀匹配带有单词边界。前缀后面必须跟空格或字符串末尾
- **示例**: `Bash(ls:*)` 匹配 `ls -la` 但不匹配 `lsof`

### `*` - Glob 匹配（无单词边界）

- **位置**: 模式中的任何位置
- **行为**: 匹配该位置处的任何字符序列
- **示例**: `Bash(ls*)` 匹配 `ls -la` 和 `lsof`

## 工具特定规则

### Bash 规则

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",      // 允许所有 npm run 命令
      "Bash(git commit:*)",   // 允许所有 git commit 命令
      "Bash(git * main)"      // 允许任何针对 main 的 git 命令
    ]
  }
}
```

### Read 规则

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",         // 拒绝读取 .env 文件
      "Read(./.env.*)",       // 拒绝读取 .env.* 文件
      "Read(./secrets/**)"    // 拒绝读取 secrets 目录下所有文件
    ]
  }
}
```

### WebFetch 规则

```json
{
  "permissions": {
    "allow": [
      "WebFetch(domain:github.com)",     // 允许访问 github.com
      "WebFetch(domain:*.example.com)"   // 允许访问 example.com 的所有子域
    ]
  }
}
```

## 常见陷阱

### 陷阱 1: 使用 `Bash(*)` 匹配所有命令

❌ **错误**: `Bash(*)` 不匹配所有 Bash 命令
✅ **正确**: 使用 `Bash` 匹配所有 Bash 命令

### 陷阱 2: 参数约束的安全限制

❌ **不安全**: `Bash(curl http://github.com/:*)` 不会匹配：
- `curl -X GET http://github.com/...`（标志在 URL 之前）
- `curl https://github.com/...`（不同的协议）
- 使用 shell 变量的命令

⚠️ **不要依赖参数约束模式作为安全边界**

### 陷阱 3: 忘记规则评估顺序

```json
{
  "permissions": {
    "allow": ["Bash(git push:*)"],
    "deny": ["Bash(git push:*)"]
  }
}
```

结果：deny 规则优先，所有 git push 命令被拒绝。
