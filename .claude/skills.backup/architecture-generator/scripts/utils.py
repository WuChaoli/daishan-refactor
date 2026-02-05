#!/usr/bin/env python3
"""
Utility functions for architecture generator.

Provides common functionality for:
- Parsing .gitignore files
- Detecting file types (programming languages)
- Path matching and exclusion
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple


def parse_gitignore(gitignore_path: Optional[Path] = None) -> List[str]:
    """
    解析 .gitignore 文件，返回排除模式列表

    Args:
        gitignore_path: .gitignore 文件路径，如果为 None 则返回空列表

    Returns:
        排除模式字符串列表

    Examples:
        >>> patterns = parse_gitignore(Path(".gitignore"))
        >>> print(patterns)
        ['node_modules/', '*.pyc', '__pycache__/']
    """
    if not gitignore_path or not gitignore_path.exists():
        return []

    patterns = []
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            patterns.append(line)

    return patterns


def is_excluded(path: Path, patterns: List[str], base_dir: Optional[Path] = None) -> bool:
    """
    检查路径是否匹配任何排除模式

    Args:
        path: 要检查的路径
        patterns: .gitignore 风格的排除模式列表
        base_dir: 基础目录，用于相对路径计算

    Returns:
        如果路径被排除则返回 True

    Examples:
        >>> patterns = ['node_modules/', '*.pyc']
        >>> is_excluded(Path('src/main.py'), patterns)
        False
        >>> is_excluded(Path('test.pyc'), patterns)
        True
    """
    if not patterns:
        return False

    # 计算相对路径
    if base_dir:
        try:
            rel_path = str(path.relative_to(base_dir))
        except ValueError:
            # 路径不在 base_dir 下
            rel_path = str(path)
    else:
        rel_path = str(path)

    # 标准化路径分隔符
    rel_path = rel_path.replace('\\', '/')

    for pattern in patterns:
        if _match_pattern(rel_path, pattern):
            return True

    return False


def _match_pattern(path: str, pattern: str) -> bool:
    """
    匹配路径与 .gitignore 模式

    简化版实现，支持常见模式：
    - *.ext: 文件扩展名匹配
    - dir/: 目录匹配
    - /path: 根路径匹配
    - **/: 递归匹配
    """
    # 标准化模式
    pattern = pattern.strip()
    if not pattern:
        return False

    # 目录模式（以 / 结尾）
    if pattern.endswith('/'):
        # 检查是否在该目录下
        dir_name = pattern.rstrip('/')
        return path.startswith(dir_name + '/') or path == dir_name

    # 根路径模式（以 / 开头）
    if pattern.startswith('/'):
        # 精确匹配从根开始的路径
        pattern = pattern[1:]
        return path == pattern or path.startswith(pattern + '/')

    # 递归目录模式 (**/)
    if '**/' in pattern:
        # 简化处理：匹配任意层级
        sub_pattern = pattern.replace('**/', '(.*/)?')
        return bool(re.match(sub_pattern, path))

    # 通配符模式
    if '*' in pattern:
        # 转换为正则表达式
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
        # 匹配完整路径或路径的任何部分
        return bool(re.match(regex_pattern, path)) or bool(re.search(f'/({regex_pattern})', path))

    # 精确匹配或前缀匹配
    return path == pattern or path.startswith(pattern + '/')


def detect_file_type(file_path: Path) -> str:
    """
    检测文件类型/编程语言（Phase 3：扩展多语言支持）

    Args:
        file_path: 文件路径

    Returns:
        文件类型字符串：'python', 'javascript', 'typescript', 'go', 'rust', 'java', 'other'

    Examples:
        >>> detect_file_type(Path('src/main.py'))
        'python'
        >>> detect_file_type(Path('app.js'))
        'javascript'
        >>> detect_file_type(Path('component.tsx'))
        'typescript'
        >>> detect_file_type(Path('main.go'))
        'go'
    """
    suffix = file_path.suffix.lower()

    # Python
    if suffix == '.py':
        return 'python'

    # JavaScript
    if suffix in ['.js', '.jsx', '.mjs', '.cjs']:
        return 'javascript'

    # TypeScript
    if suffix in ['.ts', '.tsx']:
        return 'typescript'

    # Go
    if suffix == '.go':
        return 'go'

    # Rust
    if suffix == '.rs':
        return 'rust'

    # Java
    if suffix in ['.java', '.kt', '.scala']:
        return 'java'

    # C/C++
    if suffix in ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp']:
        return 'c'

    # C#
    if suffix == '.cs':
        return 'csharp'

    # Ruby
    if suffix == '.rb':
        return 'ruby'

    # PHP
    if suffix == '.php':
        return 'php'

    # 其他
    return 'other'


def is_typescript_project(root_path: Path) -> bool:
    """
    检测项目是否为 TypeScript 项目

    Args:
        root_path: 项目根目录

    Returns:
        如果检测到 tsconfig.json 则返回 True
    """
    tsconfig_path = root_path / 'tsconfig.json'
    return tsconfig_path.exists()


def get_default_excludes() -> List[str]:
    """
    获取默认排除的目录和文件

    Returns:
        默认排除模式列表
    """
    return [
        'node_modules/',
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '.git/',
        '.svn/',
        '.hg/',
        'venv/',
        'env/',
        '.venv/',
        'dist/',
        'build/',
        '*.egg-info/',
        '.tox/',
        '.mypy_cache/',
        '.pytest_cache/',
        '*.min.js',
        '*.min.css',
        'coverage/',
        '.cache/',
    ]


def should_include_file(file_path: Path, patterns: Optional[List[str]] = None,
                       base_dir: Optional[Path] = None) -> bool:
    """
    判断文件是否应该被包含在扫描中

    Args:
        file_path: 文件路径
        patterns: 额外的排除模式（会与默认模式合并）
        base_dir: 基础目录

    Returns:
        如果文件应该被包含则返回 True
    """
    # 跳过隐藏文件（除了特定配置文件）
    if file_path.name.startswith('.') and file_path.name not in {'.gitignore', '.env', '.eslintrc', '.prettierrc'}:
        return False

    # 合并默认排除模式和用户提供的模式
    all_patterns = get_default_excludes()
    if patterns:
        all_patterns.extend(patterns)

    # 检查是否被排除
    if is_excluded(file_path, all_patterns, base_dir):
        return False

    return True


def normalize_path(path: Path, base_dir: Optional[Path] = None) -> Path:
    """
    标准化路径，解析相对路径和绝对路径

    Args:
        path: 要标准化的路径
        base_dir: 基础目录（用于相对路径）

    Returns:
        标准化后的绝对路径
    """
    if path.is_absolute():
        return path.resolve()

    if base_dir:
        return (base_dir / path).resolve()

    return path.resolve()


def get_relative_path(path: Path, base_dir: Path) -> Path:
    """
    获取相对于基础目录的路径

    Args:
        path: 文件路径
        base_dir: 基础目录

    Returns:
        相对路径
    """
    try:
        return path.relative_to(base_dir)
    except ValueError:
        # 如果 path 不在 base_dir 下，返回绝对路径
        return path


if __name__ == '__main__':
    # 测试代码
    import sys

    # 测试 .gitignore 解析
    if len(sys.argv) > 1:
        gitignore_path = Path(sys.argv[1])
        patterns = parse_gitignore(gitignore_path)
        print(f"Found {len(patterns)} patterns in {gitignore_path}")
        for pattern in patterns[:10]:
            print(f"  - {pattern}")

    # 测试文件类型检测
    test_files = [
        'main.py',
        'app.js',
        'component.tsx',
        'README.md',
        'style.css'
    ]
    print("\nFile type detection:")
    for f in test_files:
        print(f"  {f}: {detect_file_type(Path(f))}")
