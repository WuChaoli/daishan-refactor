---
name: git-pr
description: "安全执行 Git 提交与 PR 流程，包含分支保护、提交、同步、推送与 PR 创建更新。用于“git-pr”“创建PR”“提交并发起PR”等场景。"
---

# Git PR Workflow (Safe v2)

自动化 Git 提交流程（增强版）：
1) 保护主分支、2) 提交更改、3) 同步 `main`、4) 审查与验证、5) 推送分支、6) 创建或更新 PR。

> 目标：避免“直接在 main 开发”“重复 PR”“网络/权限报错后中断”的常见问题。

## Usage

```bash
/git-pr [commit-message]
```

可选扩展（如实现方支持）：

```bash
/git-pr [commit-message] [--base=main] [--skip-review]
```

## Arguments

- `commit-message`：可选提交消息；未提供时自动生成 Conventional Commit。

## Workflow

### 0) Preflight（执行前检查）

```bash
# 当前分支与工作区
CURRENT_BRANCH=$(git branch --show-current)
git status --short --branch

# 远端与认证
# gh 可选；没有 gh 时只做 push，不创建 PR
git remote -v
gh auth status || true
```

检查点：
- 必须在 Git 仓库中（`git rev-parse --is-inside-work-tree`）。
- 不在 detached HEAD。
- 若 `gh` 未安装/未登录，后续跳过 PR 创建并给出提示。

---

### 1) Branch Guard（主分支保护）

如果当前在 `main/master`，**先切功能分支再继续**：

```bash
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  SAFE_BRANCH="chore-$(date +%Y%m%d-%H%M%S)-git-pr"
  git checkout -b "$SAFE_BRANCH"
  CURRENT_BRANCH="$SAFE_BRANCH"
fi
```

推荐分支命名：
- `feat-<topic>`
- `fix-<topic>`
- `chore-<topic>`

---

### 2) Commit Changes（提交本地改动）

```bash
# 有改动才提交
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "<commit-message>"
else
  echo "No uncommitted changes"
fi
```

#### Commit Message 规范

未传入 `commit-message` 时，可按变更自动生成：

| 变更类型 | 提交消息格式 | 示例 |
|---------|-------------|------|
| 新功能 | `feat: <description>` | `feat: add user authentication` |
| Bug修复 | `fix: <description>` | `fix: resolve login timeout` |
| 重构 | `refactor: <description>` | `refactor: simplify prompt workflow` |
| 文档 | `docs: <description>` | `docs: update git-pr workflow` |
| 测试 | `test: <description>` | `test: add PR command tests` |
| 样式 | `style: <description>` | `style: normalize markdown format` |

---

### 3) Sync with Main（同步主分支）

```bash
BASE_BRANCH="main"
git fetch origin "$BASE_BRANCH"
git merge "origin/$BASE_BRANCH"
```

若出现冲突：
1. 手动解决冲突（删除 `<<<<<<<`/`=======`/`>>>>>>>`）。
2. `git add <resolved-files>`
3. `git commit`
4. 重新执行 `/git-pr`

---

### 4) Review Gate（合并前审查门禁）

至少执行与改动直接相关的最小验证：

```bash
# 示例（按项目类型替换）
# npm test -- <changed-scope>
# pytest tests/path/to/changed
# pnpm lint <changed-files>
```

建议在创建 PR 前做一次审查：
- 使用 `/requesting-code-review`（或等效代码审查流程）。
- Critical/Important 问题先修复再继续。

> 文档或配置类小改动，可记录“最小验证步骤 + 结果”。

---

### 5) Push to Remote（推送分支）

```bash
git push -u origin "$CURRENT_BRANCH"
```

推送失败处理：

```bash
# 推荐：先变基后推送
git pull --rebase origin "$CURRENT_BRANCH"
git push

# 仅在确认安全时使用
git push --force-with-lease
```

---

### 6) Create or Update PR（创建或更新 PR）

先检查该分支是否已有 PR：

```bash
EXISTING_PR_URL=$(gh pr list --head "$CURRENT_BRANCH" --state open --json url --jq '.[0].url')
```

#### 6.1 已存在 PR（推荐更新）

```bash
if [ -n "$EXISTING_PR_URL" ] && [ "$EXISTING_PR_URL" != "null" ]; then
  echo "PR already exists: $EXISTING_PR_URL"
  # 可选：更新标题和正文
  # gh pr edit "$EXISTING_PR_URL" --title "<new-title>" --body-file /tmp/pr_body.md
fi
```

#### 6.2 不存在 PR（创建新 PR）

```bash
COMMIT_MESSAGE=$(git log -1 --pretty=%s)
COMMIT_RANGE="origin/main...$CURRENT_BRANCH"

{
  echo "## Summary"
  git log "$COMMIT_RANGE" --pretty=format:"- %s" | head -10
  echo
  echo
  echo "## Changes"
  git diff "$COMMIT_RANGE" --stat
  echo
  echo "## Test plan"
  echo "- [ ] Unit tests pass"
  echo "- [ ] Integration tests pass"
  echo "- [ ] Manual testing completed"
} > /tmp/pr_body.md

gh pr create \
  --base main \
  --head "$CURRENT_BRANCH" \
  --title "$COMMIT_MESSAGE" \
  --body-file /tmp/pr_body.md
```

---

## Codex 环境注意事项（实战经验）

### 1) `Operation not permitted` / `index.lock` / `FETCH_HEAD`

在受限沙箱中，Git 写入 `.git` 可能被拦截。处理方式：
- 对关键命令申请提权后重试（如 `git checkout -b`、`git add`、`git commit`、`git fetch`、`git push`）。
- 不要绕过安全策略执行破坏性命令。

### 2) `Could not resolve host: github.com`

网络受限导致无法访问 GitHub。处理方式：
- 申请网络权限后重试 `git push` / `gh pr create`。

### 3) 在 `main` 上有未提交改动

务必先切新分支再提交，避免直接污染主分支。

### 4) 文档删除后残留引用

PR 前建议扫描一次引用：

```bash
rg -n "<deleted-keyword>" -S .
```

---

## Output Template

建议最终输出包含：

```markdown
## Git PR Workflow

- Branch: <current-branch>
- Commit: <latest-sha> <latest-message>
- Sync: merged origin/main (or already up to date)
- Push: success -> origin/<branch>
- PR: <url or skipped reason>
- Validation: <what was checked>
```

---

## Error Handling

### `gh` CLI 未安装

```bash
Error: gh CLI not found
Install: https://cli.github.com/
```

### `gh` 未登录

```bash
Error: GitHub authentication failed
Run: gh auth login
```

### 合并冲突

```bash
⚠️ Merge conflict detected
Resolve conflicts, commit, then rerun /git-pr
```

### 远端分支存在新提交

```bash
git pull --rebase origin <branch>
git push
```

---

## Tips

1. **先审查后合并**：PR 创建前完成最小验证与代码审查。
2. **避免重复 PR**：优先复用已存在 PR。
3. **提交要可读**：保持 Conventional Commit，便于追踪。
4. **失败要可恢复**：每一步都输出可执行下一步。
5. **默认安全策略**：不用 `--force`，必要时才 `--force-with-lease`。

## Related Commands

- `/checkpoint` - 创建检查点
- `/context-archive` - 归档上下文
- `git commit` - Git 提交
- `gh pr create` - 创建 Pull Request
