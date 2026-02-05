# 安全注意事项和最佳实践

## 安全警告

### ⚠️ Bash 参数约束的局限性

尝试约束命令参数的 Bash 权限模式很脆弱，不应作为安全边界。

**示例问题**:

```json
{
  "permissions": {
    "allow": ["Bash(curl http://github.com/:*)"]
  }
}
```

这个规则**不会**匹配：
- `curl -X GET http://github.com/...`（标志在 URL 之前）
- `curl https://github.com/...`（不同的协议）
- `curl "http://github.com/..."`（引号）
- `URL="http://github.com/..."; curl $URL`（使用变量）

**不要依赖参数约束模式作为安全边界**。

### 替代方案

1. **使用 Sandbox 模式**：提供更强的隔离
2. **使用工具级别的拒绝**：`deny: ["Bash"]` 完全阻止 Bash
3. **使用网络限制**：在 sandbox 配置中限制网络访问

## 最佳实践

### 1. 保护敏感文件

始终拒绝访问包含密钥和凭证的文件：

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)",
      "Read(~/.gnupg/**)"
    ]
  }
}
```

### 2. 使用 Ask 规则确认危险操作

对于可能造成数据丢失或不可逆更改的操作，使用 `ask` 规则：

```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)",
      "Bash(rm:*)",
      "Bash(docker rm:*)",
      "Bash(kubectl delete:*)",
      "Edit",
      "Write"
    ]
  }
}
```

### 3. 记住规则评估顺序

规则评估顺序：**Deny → Ask → Allow**

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
- `git status` → 允许（allow 规则）
- `git push` → 询问（ask 规则）
- `git push --force` → 拒绝（deny 规则优先）

### 4. 使用工具名称匹配所有使用

要匹配工具的所有使用，使用工具名称（不带括号）：

✅ **正确**: `"Bash"` 匹配所有 Bash 命令
❌ **错误**: `"Bash(*)"` 不匹配所有 Bash 命令

### 5. 使用 additionalDirectories 扩展访问

当需要访问工作目录外的文件时，使用 `additionalDirectories`：

```json
{
  "permissions": {
    "additionalDirectories": [
      "../shared-lib/",
      "../docs/"
    ],
    "allow": [
      "Read(../shared-lib/**)",
      "Read(../docs/**)"
    ]
  }
}
```

### 6. 结合 Sandbox 增强安全性

Sandbox 提供额外的安全层：

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker"],
    "network": {
      "allowUnixSockets": ["/var/run/docker.sock"],
      "allowLocalBinding": true
    }
  },
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  }
}
```

### 7. 使用 defaultMode 设置默认行为

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

可选值：
- `"acceptEdits"` - 自动接受编辑操作
- `"ask"` - 询问所有操作（默认）

### 8. 禁用 bypassPermissions 模式

在生产环境中，禁用绕过权限的能力：

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

这会禁用 `--dangerously-skip-permissions` 命令行标志。

## 安全检查清单

在部署权限配置前，检查以下项目：

- [ ] 所有敏感文件都在 deny 列表中
- [ ] 危险操作使用 ask 规则
- [ ] 没有依赖参数约束作为安全边界
- [ ] 规则评估顺序正确（deny 优先）
- [ ] 使用工具名称（不带括号）匹配所有使用
- [ ] 考虑启用 sandbox 模式
- [ ] 在生产环境中禁用 bypassPermissions
- [ ] 测试配置以确保按预期工作

## 常见安全错误

### 错误 1: 过度信任参数约束

❌ **不安全**:
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

### 错误 2: 忘记保护配置文件

❌ **不安全**:
```json
{
  "permissions": {
    "deny": ["Read(./.env)"]
  }
}
```

还应该保护：
- `.env.local`, `.env.production`
- `config/secrets.json`
- `credentials.yml`

### 错误 3: 允许过于宽泛的模式

❌ **不安全**:
```json
{
  "permissions": {
    "allow": ["Bash(git:*)"]
  }
}
```

这允许：
- `git push --force`
- `git reset --hard`
- `git clean -fd`

✅ **更安全**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git commit:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)"
    ]
  }
}
```

## 审计和监控

定期审查权限配置：

1. **检查 deny 规则** - 确保所有敏感文件都被保护
2. **审查 allow 规则** - 确认没有过于宽泛的权限
3. **测试配置** - 验证规则按预期工作
4. **更新文档** - 记录权限决策的原因

## 相关文档

- **Sandbox 设置**: 了解如何使用沙箱模式增强安全性
- **Managed Settings**: 了解如何在组织级别管理权限设置
- **Bash Permission Limitations**: 详细了解 Bash 权限的限制
