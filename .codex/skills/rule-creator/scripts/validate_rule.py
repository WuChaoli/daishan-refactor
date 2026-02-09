#!/usr/bin/env python3
"""验证规则文件的完整性和质量"""
import sys
import re
from pathlib import Path


def validate_rule(file_path):
    """验证规则文件结构

    Args:
        file_path: 规则文件路径

    Returns:
        tuple: (errors, warnings)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return [f"文件不存在: {file_path}"], []

    errors = []
    warnings = []

    # 检查必需章节
    if "## 绝对禁令" not in content and "## 必须遵守" not in content:
        errors.append("缺少约束性章节（至少需要'绝对禁令'或'必须遵守'之一）")

    # 检查约束性词汇
    constraints = re.findall(r'\*\*(禁止|必须|应该|可以)\*\*', content)
    if not constraints:
        warnings.append("未发现约束性词汇（禁止/必须/应该/可以）")

    # 检查表格格式
    if '|' in content:
        tables = re.findall(r'\|[^\n]+\|[^\n]+\|[^\n]+\|', content)
        if not tables:
            warnings.append("表格格式可能不正确（应至少有4列）")

    # 检查规则长度
    lines = content.split('\n')
    long_lines = []
    for i, line in enumerate(lines, 1):
        if len(line) > 100 and not line.startswith('#') and not line.startswith('|'):
            long_lines.append(f"行{i}: {len(line)}字符")

    if long_lines:
        warnings.append(f"发现{len(long_lines)}行过长（建议≤100字符）: {', '.join(long_lines[:3])}")

    # 统计约束性规则数量（包括代码块中的内容）
    ban_count = len(re.findall(r'\*\*禁止\*\*', content))
    must_count = len(re.findall(r'\*\*必须\*\*', content))
    should_count = len(re.findall(r'\*\*应该\*\*', content))

    # 检查是否在示例中有这些词汇（示例不算作错误）
    has_real_rules = ban_count > 0 or must_count > 0
    in_code_block = False
    real_ban_count = 0
    real_must_count = 0

    for line in content.split('\n'):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
        if not in_code_block:
            real_ban_count += line.count('**禁止**')
            real_must_count += line.count('**必须**')

    if real_ban_count + real_must_count == 0:
        errors.append("缺少强制性规则（禁止或必须）")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_rule.py <规则文件路径>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    errors, warnings = validate_rule(file_path)

    if errors:
        print(f"❌ 验证失败 ({file_path})")
        for error in errors:
            print(f"  错误: {error}")
        sys.exit(1)

    if warnings:
        print(f"⚠️  验证通过，但有{len(warnings)}个警告 ({file_path})")
        for warning in warnings:
            print(f"  警告: {warning}")
    else:
        print(f"✅ 验证通过 ({file_path})")

    # 输出统计信息
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    ban_count = len(re.findall(r'\*\*禁止\*\*', content))
    must_count = len(re.findall(r'\*\*必须\*\*', content))
    should_count = len(re.findall(r'\*\*应该\*\*', content))

    print(f"\n📊 规则统计:")
    print(f"   禁止: {ban_count}")
    print(f"   必须: {must_count}")
    print(f"   应该: {should_count}")


if __name__ == '__main__':
    main()
