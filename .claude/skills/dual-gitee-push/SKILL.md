---
name: dual-gitee-push
description: Manage dual Gitee repository push workflows for projects that need to synchronize code to both personal and organization repositories. Use when the user needs to push code to multiple Gitee repositories simultaneously, handle PR merges between repositories, or set up dual-push configurations. Triggers include "push to gitee", "dual push", "sync gitee repositories", "gitee PR merge".
---

# Dual Gitee Push

## Overview

This skill provides workflows for managing code synchronization across multiple Gitee repositories, specifically designed for projects that maintain both personal and organization repositories.

## Core Workflows

### 1. Daily Push Workflow

Use the `git push-double-gitee` alias to push local main branch to both repositories' master branches simultaneously.

**Command:**
```bash
git push-double-gitee
```

**What it does:**
- Pushes local `main` branch to `gitee` remote's `master` branch
- Pushes local `main` branch to `gitee-org` remote's `master` branch
- Stops if either push fails

**Common scenarios:**
- After committing new features
- After bug fixes
- Regular code synchronization

### 2. PR Merge Workflow

When pushing to organization repository is rejected (non-fast-forward), create a feature branch and submit a Pull Request.

**Steps:**

1. **Create feature branch:**
   ```bash
   git checkout -b feat/feature-name
   ```

2. **Push to organization repository:**
   ```bash
   git push -u gitee-org feat/feature-name
   ```

3. **Create PR on Gitee:**
   - Visit the PR link provided in push output
   - Or manually create PR at: `https://gitee.com/ORG/REPO/pulls`

4. **Merge PR locally (if you have permissions):**
   ```bash
   # Create local master branch based on remote
   git checkout -b master gitee-org/master

   # Merge feature branch (allow unrelated histories if needed)
   git merge feat/feature-name --allow-unrelated-histories --no-edit

   # Resolve conflicts if any (typically in .gitignore or similar files)
   # After resolving:
   git add <conflicted-files>
   git commit -m "Merge feat/feature-name into master"

   # Push to organization repository
   git push gitee-org master

   # Switch back to main branch
   git checkout main

   # Clean up feature branch
   git branch -d feat/feature-name
   ```

### 3. Conflict Resolution

When merge conflicts occur (common in .gitignore, config files):

1. **Check conflict status:**
   ```bash
   git status
   ```

2. **Edit conflicted files** to resolve conflicts (remove conflict markers)

3. **Stage resolved files:**
   ```bash
   git add <resolved-files>
   ```

4. **Complete merge:**
   ```bash
   git commit -m "Resolve merge conflicts"
   ```

## Repository Configuration

### Remote Repositories

Typical setup includes three remotes:

- **origin**: GitHub backup repository
- **gitee**: Personal Gitee repository
- **gitee-org**: Organization Gitee repository

**View remotes:**
```bash
git remote -v
```

### Branch Mapping

- Local `main` branch → Remote `master` branch
- This mapping is handled by the `push-double-gitee` alias

## Troubleshooting

### Push Rejected (Non-Fast-Forward)

**Symptom:** Error message "Updates were rejected because a pushed branch tip is behind its remote"

**Solution:** Use PR Merge Workflow (see above)

### SSH Authentication Failed

**Symptom:** "Permission denied (publickey)"

**Solution:** Verify SSH key is added to Gitee account at https://gitee.com/profile/sshkeys

### Merge Conflicts

**Symptom:** "Automatic merge failed; fix conflicts"

**Solution:** Follow Conflict Resolution workflow (see above)

## Best Practices

1. **Always commit before pushing:**
   ```bash
   git add .
   git commit -m "descriptive message"
   git push-double-gitee
   ```

2. **For organization repository changes, use feature branches:**
   - Avoids direct master branch conflicts
   - Enables code review through PRs
   - Maintains clean history

3. **Keep local main branch clean:**
   - Don't work directly on master branch
   - Use main for development, master for merging

4. **Regular synchronization:**
   - Push frequently to keep repositories in sync
   - Reduces merge conflicts

## Quick Reference

| Task | Command |
|------|---------|
| Push to both repos | `git push-double-gitee` |
| Create feature branch | `git checkout -b feat/name` |
| Push feature branch | `git push gitee-org feat/name` |
| View remotes | `git remote -v` |
| Check status | `git status` |
| View recent commits | `git log --oneline -5` |
