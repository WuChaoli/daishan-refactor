#!/usr/bin/env python3
"""
Dependency analyzer for architecture generator (Phase 2).

Analyzes import/require dependencies between files and generates layered Mermaid graphs.

Supports:
- Python: AST-based import analysis
- JavaScript/TypeScript: Regex-based import/require matching
- Other languages: Basic file-level dependency tracking

Phase 2 Features:
- Layered dependency analysis with node threshold control
- Automatic splitting by folder when threshold exceeded
- Multi-level graph generation (level-0, level-1, level-2, ...)
"""

import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from utils import (
    parse_gitignore,
    should_include_file,
    get_relative_path,
    normalize_path,
    detect_file_type,
    is_typescript_project,
)


class DependencyAnalyzer:
    """依赖关系分析器（Phase 2：支持分层）"""

    def __init__(self, root_path: Path, gitignore_path: Path = None, node_threshold: int = 25):
        self.root_path = normalize_path(root_path)
        self.exclude_patterns = parse_gitignore(gitignore_path)
        self.file_dependencies: Dict[str, Set[str]] = {}
        self.file_types: Dict[str, str] = {}
        self.node_threshold = node_threshold  # 节点数阈值

    def analyze_project(self) -> Dict:
        """
        分析整个项目的依赖关系（分层）

        Returns:
            分层依赖关系数据字典
            {
                "level_0": {"nodes": [...], "edges": [...], "mermaid": "..."},
                "level_1": {
                    "src": {"nodes": [...], "edges": [...], "mermaid": "..."},
                    "tests": {...}
                },
                ...
            }
        """
        # 收集所有源代码文件
        source_files = self._collect_source_files()

        # 分析每个文件的依赖
        for file_path in source_files:
            self._analyze_file(file_path)

        # 构建分层依赖图
        layered_graph = self._build_layered_dependency_graph()

        return layered_graph

    def _collect_source_files(self) -> List[Path]:
        """收集项目中所有源代码文件"""
        source_files = []

        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue

            if not should_include_file(file_path, self.exclude_patterns, self.root_path):
                continue

            # 只处理源代码文件
            file_type = detect_file_type(file_path)
            if file_type in ['python', 'javascript', 'typescript']:
                source_files.append(file_path)
                self.file_types[str(file_path)] = file_type

        return source_files

    def _analyze_file(self, file_path: Path):
        """分析单个文件的依赖（Phase 3：扩展多语言）"""
        file_type = self.file_types.get(str(file_path), 'other')
        rel_path = str(get_relative_path(file_path, self.root_path))

        if file_type == 'python':
            dependencies = self._analyze_python_file(file_path)
        elif file_type in ['javascript', 'typescript']:
            dependencies = self._analyze_js_file(file_path)
        elif file_type == 'go':
            dependencies = self._analyze_go_file(file_path)
        elif file_type == 'rust':
            dependencies = self._analyze_rust_file(file_path)
        elif file_type == 'java':
            dependencies = self._analyze_java_file(file_path)
        elif file_type == 'ruby':
            dependencies = self._analyze_ruby_file(file_path)
        else:
            # 其他语言使用基础分析
            dependencies = self._analyze_generic_file(file_path)

        self.file_dependencies[rel_path] = dependencies

    def _analyze_python_file(self, file_path: Path) -> Set[str]:
        """分析 Python 文件的 import 依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            for node in ast.walk(tree):
                # import xxx
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split('.')[0])

                # from xxx import yyy
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module.split('.')[0])

        except (SyntaxError, UnicodeDecodeError):
            # 无法解析的文件，跳过
            pass

        return dependencies

    def _analyze_js_file(self, file_path: Path) -> Set[str]:
        """分析 JavaScript/TypeScript 文件的依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # ES6 import: import xxx from 'xxx'
            import_patterns = [
                r"import\s+(?:(?:\w+|\{[^}]*\}|\*\s+as\s+\w+)\s+from\s+)?['\"]([^'\"]+)['\"]",
                r"import\(['\"]([^'\"]+)['\"]\)",
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # 提取模块名（忽略相对路径和内置模块）
                    if not match.startswith('.') and not match.startswith('/'):
                        # 取第一段作为依赖
                        dep = match.split('/')[0].split('@')[0]
                        if dep:
                            dependencies.add(dep)

            # CommonJS: require('xxx')
            require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
            matches = re.findall(require_pattern, content)
            for match in matches:
                if not match.startswith('.') and not match.startswith('/'):
                    dep = match.split('/')[0]
                    if dep:
                        dependencies.add(dep)

        except (UnicodeDecodeError, OSError):
            # 无法读取的文件，跳过
            pass

        return dependencies

    def _build_layered_dependency_graph(self) -> Dict:
        """构建分层依赖关系图"""
        # 获取所有文件的顶层文件夹
        file_folders = defaultdict(list)
        for file_path in self.file_dependencies.keys():
            folder = file_path.split('/')[0] if '/' in file_path else '.'
            file_folders[folder].append(file_path)

        # Level 0: 顶层依赖（文件夹级别）
        level_0_graph = self._build_folder_level_graph(file_folders)

        # 检查是否需要分层
        total_files = len(self.file_dependencies)
        if total_files <= self.node_threshold:
            # 文件数不超过阈值，只生成单层图
            return {"level_0": level_0_graph}

        # 文件数超过阈值，需要分层
        layered_graph = {"level_0": level_0_graph}
        layered_graph["level_1"] = {}

        # 对每个文件夹生成子图
        for folder, files in file_folders.items():
            if len(files) > self.node_threshold:
                # 文件夹内文件数仍然超过阈值，进一步分层
                subfolders = self._split_folder_by_subfolder(files)
                layered_graph["level_1"][folder] = {
                    "type": "split",
                    "subfolders": subfolders
                }

                # Level 2: 子文件夹级别
                if "level_2" not in layered_graph:
                    layered_graph["level_2"] = {}

                for subfolder, subfiles in subfolders.items():
                    subgraph = self._build_file_level_graph(subfiles)
                    layered_graph["level_2"][f"{folder}/{subfolder}"] = subgraph
            else:
                # 文件夹内文件数未超过阈值，生成文件级图
                file_graph = self._build_file_level_graph(files)
                layered_graph["level_1"][folder] = file_graph

        return layered_graph

    def _build_folder_level_graph(self, file_folders: Dict[str, List[str]]) -> Dict:
        """构建文件夹级别的依赖图"""
        # 文件夹作为节点
        nodes = []
        for folder in file_folders.keys():
            nodes.append({
                "id": folder,
                "label": folder + "/",
                "type": "folder"
            })

        # 分析文件夹间的依赖
        folder_deps = defaultdict(set)
        for file_path, dependencies in self.file_dependencies.items():
            from_folder = file_path.split('/')[0] if '/' in file_path else '.'
            for dep in dependencies:
                # 找到依赖对应的文件夹
                to_folder = self._find_dependency_folder(dep)
                if to_folder and to_folder != from_folder:
                    folder_deps[from_folder].add(to_folder)

        # 生成边
        edges = []
        for from_folder, to_folders in folder_deps.items():
            for to_folder in to_folders:
                edges.append({
                    "from": from_folder,
                    "to": to_folder,
                    "label": "depends"
                })

        # 生成 Mermaid 图
        mermaid_graph = self._generate_mermaid_graph(nodes, edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "mermaid": mermaid_graph,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }

    def _build_file_level_graph(self, files: List[str]) -> Dict:
        """构建文件级别的依赖图"""
        # 生成节点
        nodes = []
        for file_path in files:
            nodes.append({
                "id": file_path,
                "label": Path(file_path).name,
                "type": self.file_types.get(file_path, "unknown")
            })

        # 生成边
        edges = []
        for from_file in files:
            dependencies = self.file_dependencies.get(from_file, set())
            for dep in dependencies:
                to_file = self._find_dependency_file(dep, files)
                if to_file and to_file in files:
                    edges.append({
                        "from": from_file,
                        "to": to_file,
                        "label": dep
                    })

        # 生成 Mermaid 图
        mermaid_graph = self._generate_mermaid_graph(nodes, edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "mermaid": mermaid_graph,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }

    def _split_folder_by_subfolder(self, files: List[str]) -> Dict[str, List[str]]:
        """按子文件夹拆分文件列表"""
        subfolders = defaultdict(list)

        for file_path in files:
            parts = file_path.split('/')
            if len(parts) > 1:
                # 使用第二层作为子文件夹名
                subfolder = parts[1] if len(parts) > 1 else '.'
            else:
                subfolder = '.'
            subfolders[subfolder].append(file_path)

        return dict(subfolders)

    def _find_dependency_folder(self, dep_name: str) -> str:
        """查找依赖对应的文件夹"""
        for file_path in self.file_dependencies.keys():
            if dep_name.lower() in file_path.lower():
                return file_path.split('/')[0] if '/' in file_path else '.'
        return None

    def _find_dependency_file(self, dep_name: str, file_list: List[str] = None) -> str:
        """查找依赖对应的文件路径"""
        if file_list is None:
            file_list = list(self.file_dependencies.keys())

        for file_path in file_list:
            if dep_name.lower() in file_path.lower():
                return file_path
        return None

    def _generate_mermaid_graph(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """生成 Mermaid 格式的依赖图"""
        lines = ["graph TD"]

        # 添加节点
        for node in nodes:
            label = node["label"]
            node_id = node["id"].replace("/", "_").replace(".", "_")
            lines.append(f"    {node_id}[\"{label}\"]")

        # 添加边
        for edge in edges:
            from_id = edge["from"].replace("/", "_").replace(".", "_")
            to_id = edge["to"].replace("/", "_").replace(".", "_")
            label = edge.get("label", "")
            if label:
                lines.append(f"    {from_id} -->|{label}| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    # Phase 3: 多语言支持方法

    def _analyze_go_file(self, file_path: Path) -> Set[str]:
        """分析 Go 文件的依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # import "xxx" 或 import 'xxx'
            import_pattern = r'import\s+["\']([^"\']+)["\']'
            matches = re.findall(import_pattern, content)
            for match in matches:
                # 标准库以路径开头，第三方包通常是域名
                if match.startswith('.') or '/' in match:
                    dep = match.split('/')[0]
                else:
                    dep = match.split('/')[0]
                if dep:
                    dependencies.add(dep)

        except (UnicodeDecodeError, OSError):
            pass

        return dependencies

    def _analyze_rust_file(self, file_path: Path) -> Set[str]:
        """分析 Rust 文件的依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # use xxx::yyy;
            use_pattern = r'use\s+([^;]+);'
            matches = re.findall(use_pattern, content)
            for match in matches:
                # 提取 crate 名称
                parts = match.split('::')
                if parts:
                    # 处理 'crate::xxx' 或 'extern crate xxx'
                    crate = parts[0].strip()
                    if crate.startswith('crate '):
                        crate = crate.replace('crate ', '').strip()
                    elif crate.startswith('extern crate '):
                        crate = crate.replace('extern crate ', '').strip()
                    if crate and crate not in ['std', 'core', 'alloc']:
                        dependencies.add(crate)

        except (UnicodeDecodeError, OSError):
            pass

        return dependencies

    def _analyze_java_file(self, file_path: Path) -> Set[str]:
        """分析 Java 文件的依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # import xxx.yyy.Zzz;
            import_pattern = r'import\s+([^;]+);'
            matches = re.findall(import_pattern, content)
            for match in matches:
                # 提取包名
                package = match.split('.')[0].strip()
                if package and not package.startswith('java.lang'):
                    dependencies.add(package)

        except (UnicodeDecodeError, OSError):
            pass

        return dependencies

    def _analyze_ruby_file(self, file_path: Path) -> Set[str]:
        """分析 Ruby 文件的依赖"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # require 'xxx' 或 require "xxx" 或 require_relative "xxx"
            require_pattern = r'require\s+(["\'])([^"\']+)\1'
            matches = re.findall(require_pattern, content)
            for match in matches:
                if not match.startswith('relative'):
                    dep = match.split('/')[0]
                    if dep:
                        dependencies.add(dep)

        except (UnicodeDecodeError, OSError):
            pass

        return dependencies

    def _analyze_generic_file(self, file_path: Path) -> Set[str]:
        """通用依赖分析（用于不支持的语言）"""
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找常见的导入模式
            # import/from/include/#include
            generic_patterns = [
                r'(?:import|from|include)\s+["\']([^"\']+)["\']',
                r'#include\s*[<"]([^>"]+)[>"]',
                r'@import\s+["\']([^"\']+)["\']',
            ]

            for pattern in generic_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # 提取第一段作为依赖名
                    dep = match.split('/')[0].split('\\')[0]
                    if dep and len(dep) > 2:  # 过滤掉太短的匹配
                        dependencies.add(dep)

        except (UnicodeDecodeError, OSError):
            pass

        return dependencies


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: analyze_dependencies.py <project-path> [gitignore-path] [--threshold N]")
        print("\nExamples:")
        print("  analyze_dependencies.py /path/to/project")
        print("  analyze_dependencies.py /path/to/project /path/to/project/.gitignore")
        print("  analyze_dependencies.py /path/to/project .gitignore --threshold 30")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    gitignore_path = None
    node_threshold = 25

    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--threshold" and i + 1 < len(sys.argv):
            node_threshold = int(sys.argv[i + 1])
            i += 2
        elif not sys.argv[i].startswith("--"):
            gitignore_path = Path(sys.argv[i])
            i += 1
        else:
            i += 1

    # 分析依赖关系
    analyzer = DependencyAnalyzer(project_path, gitignore_path, node_threshold)
    result = analyzer.analyze_project()

    # 输出 JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
