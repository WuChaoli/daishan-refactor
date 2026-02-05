#!/usr/bin/env python3
"""
File structure scanner for architecture generator.

Scans project directory and generates:
- File tree structure (ASCII art)
- File statistics (by extension, total count)
"""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from utils import (
    parse_gitignore,
    should_include_file,
    get_relative_path,
    normalize_path,
)


def scan_directory(
    root_path: Path,
    gitignore_path: Optional[Path] = None,
    max_depth: Optional[int] = None,
    base_dir: Optional[Path] = None
) -> Dict:
    """
    递归扫描目录，生成文件树和统计信息

    Args:
        root_path: 要扫描的目录路径
        gitignore_path: .gitignore 文件路径
        max_depth: 最大扫描深度（None 表示无限制）
        base_dir: 基础目录（用于相对路径计算）

    Returns:
        包含文件树和统计信息的字典
        {
            "tree": "ASCII 文件树",
            "stats": {
                "total_files": 100,
                "by_extension": {".py": 50, ".md": 20}
            }
        }
    """
    root_path = normalize_path(root_path, base_dir)
    if base_dir is None:
        base_dir = root_path

    # 解析 .gitignore
    exclude_patterns = parse_gitignore(gitignore_path)

    # 收集文件信息
    file_stats = Counter()
    total_files = 0
    tree_lines = []

    # 递归扫描
    def _scan_dir(current_path: Path, depth: int, prefix: str = ""):
        nonlocal total_files

        if max_depth is not None and depth > max_depth:
            return

        try:
            entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            # 跳过不应包含的文件
            if not should_include_file(entry, exclude_patterns, base_dir):
                continue

            # 计算树形前缀
            is_last = (i == len(entries) - 1)
            current_prefix = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            rel_path = get_relative_path(entry, base_dir)

            if entry.is_dir():
                # 目录
                tree_lines.append(f"{prefix}{current_prefix}{entry.name}/")
                _scan_dir(entry, depth + 1, prefix + child_prefix)
            else:
                # 文件
                tree_lines.append(f"{prefix}{current_prefix}{entry.name}")
                total_files += 1
                file_stats[entry.suffix.lower()] += 1

    # 从根目录开始扫描
    tree_lines.append(f"{root_path.name}/")
    _scan_dir(root_path, 0)

    # 生成文件树
    tree_str = "\n".join(tree_lines)

    # 生成统计信息
    stats = {
        "total_files": total_files,
        "by_extension": dict(file_stats.most_common())
    }

    return {
        "tree": tree_str,
        "stats": stats
    }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: scan_file_structure.py <project-path> [gitignore-path] [max-depth]")
        print("\nExamples:")
        print("  scan_file_structure.py /path/to/project")
        print("  scan_file_structure.py /path/to/project /path/to/project/.gitignore")
        print("  scan_file_structure.py /path/to/project .gitignore 3")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    gitignore_path = None
    if len(sys.argv) > 2:
        gitignore_path = Path(sys.argv[2])

    max_depth = None
    if len(sys.argv) > 3:
        max_depth = int(sys.argv[3])

    # 扫描目录
    result = scan_directory(project_path, gitignore_path, max_depth)

    # 输出 JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
