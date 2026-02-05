# 员工删除详细指南

## 查找员工档案

### 按员工ID查找
```bash
# 直接访问
cat company/employee/E2026020201.md

# 检查是否存在
ls company/employee/E2026020201.md
```

### 按员工姓名查找
```bash
# 查找包含该姓名的所有档案
grep -l "name: 张三" company/employee/*.md

# 显示匹配的档案内容
grep -l "name: 张三" company/employee/*.md | xargs cat
```

### 按职位查找
```bash
# 查找某个职位的所有员工
grep -l "position: test-engineer" company/employee/*.md
```

### 列出所有员工
```bash
# 查看所有员工档案
ls -1 company/employee/

# 显示所有员工的基本信息
for file in company/employee/*.md; do
  echo "=== $(basename $file .md) ==="
  grep -E "^(name|position|personality):" "$file"
  echo ""
done
```

## 确定激活命令文件名

### 从档案提取信息
```bash
# 读取员工档案
EMPLOYEE_FILE="company/employee/E2026020201.md"

# 提取姓名（用于拼音转换）
NAME=$(grep "^name:" "$EMPLOYEE_FILE" | awk '{print $2}')

# 提取职位（用于命令前缀）
POSITION=$(grep "^position:" "$EMPLOYEE_FILE" | awk '{print $2}')

# 组合命令文件名
COMMAND_FILE="commands/load-${POSITION}-${NAME拼音}.md"
```

### 查找相关命令文件
```bash
# 按职位查找命令
ls commands/load-${POSITION}-*

# 按姓名关键词查找
ls commands/ | grep "load.*zhang.*san"

# 列出所有load命令
ls commands/load-*
```

## 删除操作详解

### 标准删除流程
```bash
# 1. 确认档案存在
EMPLOYEE_ID="E2026020201"
if [ -f "company/employee/$EMPLOYEE_ID.md" ]; then
  echo "找到员工档案：$EMPLOYEE_ID"

  # 2. 读取档案信息
  NAME=$(grep "^name:" "company/employee/$EMPLOYEE_ID.md" | awk '{print $2}')
  POSITION=$(grep "^position:" "company/employee/$EMPLOYEE_ID.md" | awk '{print $2}')

  # 3. 构建命令文件名（需要手动转换为拼音）
  COMMAND_FILE="commands/load-${POSITION}-zhang-san.md"

  # 4. 显示即将删除的文件
  echo "即将删除："
  echo "  - company/employee/$EMPLOYEE_ID.md"
  echo "  - $COMMAND_FILE"

  # 5. 删除档案
  rm "company/employee/$EMPLOYEE_ID.md"
  echo "✓ 员工档案已删除"

  # 6. 删除命令（如果存在）
  if [ -f "$COMMAND_FILE" ]; then
    rm "$COMMAND_FILE"
    echo "✓ 激活命令已删除"
  else
    echo "⚠ 激活命令不存在：$COMMAND_FILE"
  fi
else
  echo "错误：员工档案不存在"
fi
```

### 处理异常情况

#### 情况1：命令文件名不符合规范
```bash
# 手动查找可能的命令文件
EMPLOYEE_NAME="张三"
ls commands/ | grep -i "load.*test.*engineer"

# 根据查找结果手动删除
rm commands/实际文件名.md
```

#### 情况2：多个同名员工
```bash
# 列出所有匹配的员工
grep -l "name: 张三" company/employee/*.md

# 根据ID或职位区分
grep -l "name: 张三" company/employee/*.md | xargs -I {} sh -c 'echo "File: {}"; grep "^position:" {}'
```

#### 情况3：档案已删除，命令残留
```bash
# 查找孤立的命令文件
for cmd in commands/load-*.md; do
  EMPLOYEE_ID=$(grep "员工ID" "$cmd" | awk '{print $2}')
  if [ ! -f "company/employee/$EMPLOYEE_ID.md" ]; then
    echo "孤立命令: $cmd (员工ID: $EMPLOYEE_ID)"
  fi
done

# 删除孤立命令
rm commands/孤立命令文件.md
```

## 归档而非删除

如果需要保留员工记录，可以归档：

```bash
# 创建归档目录
mkdir -p company/employee/archived
mkdir -p commands/archived

# 移动到归档
mv company/employee/E2026020201.md company/employee/archived/
mv commands/load-test-engineer-zhang-san.md commands/archived/

# 更新档案状态（可选）
sed -i '' 's/status: active/status: archived/' "company/employee/archived/E2026020201.md"
```

## 批量操作

### 按职位批量删除
```bash
# 删除所有测试工程师（危险操作，需谨慎）
grep -l "position: test-engineer" company/employee/*.md | while read file; do
  EMPLOYEE_ID=$(basename "$file" .md)
  echo "删除：$EMPLOYEE_ID"
  rm "$file"
done
```

### 按状态批量清理
```bash
# 删除所有已归档员工
grep -l "status: archived" company/employee/*.md | while read file; do
  EMPLOYEE_ID=$(basename "$file" .md)
  echo "删除：$EMPLOYEE_ID"
  rm "$file"
done
```

## 恢复误删除

### 从Git恢复
```bash
# 查看删除历史
git log --all --full-history -- company/employee/E2026020201.md

# 恢复文件
git checkout HEAD~1 -- company/employee/E2026020201.md
```

### 从备份恢复
```bash
# 如果有定期备份
cp /path/to/backup/company/employee/E2026020201.md company/employee/
```

## 安全检查清单

执行删除前，确认：
- [ ] 员工ID或姓名正确
- [ ] 档案文件路径存在
- [ ] 激活命令文件已定位
- [ ] 已向用户确认删除操作
- [ ] 不需要保留该员工记录
- [ ] 相关项目或任务已交接完毕

## 常见错误及解决

### 错误：找不到员工档案
**原因**：员工ID错误或档案已删除
**解决**：
```bash
# 按姓名查找
ls company/employee/ | grep -i "关键词"

# 查看所有员工
ls company/employee/
```

### 错误：命令文件不存在
**原因**：命令文件命名不规范或已被删除
**解决**：
```bash
# 列出所有load命令
ls commands/load-*

# 按关键词查找
ls commands/ | grep "test.*engineer"
```

### 错误：权限不足
**原因**：文件被锁定或权限问题
**解决**：
```bash
# 检查文件权限
ls -l company/employee/E2026020201.md

# 修改权限（如果需要）
chmod 644 company/employee/E2026020201.md

# 强制删除
rm -f company/employee/E2026020201.md
```
