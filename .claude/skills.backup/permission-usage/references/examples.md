# 权限配置示例

## 场景 1: 保护敏感文件

防止 Claude 访问包含密钥、凭证和敏感配置的文件。

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)"
    ]
  }
}
```

## 场景 2: 开发环境配置

允许常见的开发命令，同时保护敏感操作。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(npm install:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(pytest:*)",
      "Read(./src/**)",
      "Read(./tests/**)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git commit:*)",
      "Bash(rm:*)",
      "Bash(docker:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

## 场景 3: CI/CD 环境

自动化构建和测试，但阻止部署操作。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run build)",
      "Bash(npm run test:*)",
      "Bash(npm run lint)",
      "Bash(git diff:*)",
      "Read(./src/**)",
      "Read(./package.json)"
    ],
    "deny": [
      "Bash(npm publish:*)",
      "Bash(git push:*)",
      "Bash(docker push:*)",
      "WebFetch"
    ]
  }
}
```

## 场景 4: 代码审查模式

允许读取和分析，但阻止所有修改操作。

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)"
    ],
    "deny": [
      "Edit",
      "Write",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(rm:*)"
    ]
  }
}
```

## 场景 5: 生产环境访问

严格限制，只允许只读操作和安全的诊断命令。

```json
{
  "permissions": {
    "allow": [
      "Bash(kubectl get:*)",
      "Bash(kubectl describe:*)",
      "Bash(docker ps:*)",
      "Bash(docker logs:*)",
      "Read(./logs/**)"
    ],
    "ask": [
      "Bash(kubectl exec:*)",
      "Bash(docker exec:*)"
    ],
    "deny": [
      "Bash(kubectl delete:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker rm:*)",
      "Bash(docker stop:*)",
      "Edit",
      "Write"
    ]
  }
}
```

## 场景 6: 结合 Sandbox 的安全配置

使用沙箱模式增强安全性，同时保护敏感文件。

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
      "Read(.envrc)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)"
    ]
  }
}
```

## 场景 7: 多项目工作区

允许访问多个相关项目目录。

```json
{
  "permissions": {
    "additionalDirectories": [
      "../shared-lib/",
      "../docs/",
      "../config/"
    ],
    "allow": [
      "Read(../shared-lib/**)",
      "Read(../docs/**)"
    ],
    "deny": [
      "Edit(../shared-lib/**)",
      "Write(../shared-lib/**)"
    ]
  }
}
```

## 场景 8: Web 开发环境

允许前端开发工具，限制网络访问。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run dev)",
      "Bash(npm run build)",
      "Bash(npm run test:*)",
      "Bash(npx:*)",
      "WebFetch(domain:localhost)",
      "WebFetch(domain:127.0.0.1)"
    ],
    "ask": [
      "WebFetch"
    ],
    "deny": [
      "Bash(npm publish:*)"
    ]
  }
}
```

## 完整配置示例

包含权限、环境变量和公司公告的完整配置：

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Read(~/.zshrc)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git commit:*)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  },
  "companyAnnouncements": [
    "欢迎来到 Acme Corp！在 docs.acme.com 查看我们的代码指南",
    "提醒：所有 PR 都需要代码审查"
  ]
}
```
