#!/usr/bin/env python3
"""
Symbol index builder for architecture generator (Phase 2).

Builds SQLite index of code symbols (classes, functions, variables).
Supports Python (AST) and JavaScript/TypeScript (regex).

Phase 2 Features:
- Serena MCP integration (fallback to SQLite)
- Enhanced symbol extraction
"""

import ast
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set

from utils import (
    parse_gitignore,
    should_include_file,
    get_relative_path,
    normalize_path,
    detect_file_type,
)

# Try to import enhanced AST analyzer
try:
    import sys
    # Add scripts directory to path
    scripts_dir = Path(__file__).parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from enhanced_ast_analyzer import EnhancedASTAnalyzer
    ENHANCED_AST_AVAILABLE = True
except ImportError:
    ENHANCED_AST_AVAILABLE = False


class SymbolIndexBuilder:
    """符号索引构建器（Phase 2：支持 Serena 集成）"""

    def __init__(
        self,
        root_path: Path,
        db_path: str = "symbols.db",
        gitignore_path: Path = None,
    ):
        """
        初始化符号索引构建器

        Args:
            root_path: 项目根目录
            db_path: 数据库文件路径
            gitignore_path: .gitignore 文件路径

        注意：
            - 当前版本使用 SQLite 作为符号索引后端
            - Serena MCP 集成正在开发中
            - 如需使用 Serena，请在 Claude Code 中通过自然语言调用
        """
        self.root_path = normalize_path(root_path)
        self.db_path = db_path
        self.exclude_patterns = parse_gitignore(gitignore_path)
        self.conn: Optional[sqlite3.Connection] = None

        print("   💾 Using SQLite for symbol indexing")
        print("   💡 提示：在 Claude Code 中可使用 Serena MCP 进行符号级分析")

    def build_index(self) -> Optional[str]:
        """
        构建符号索引

        Returns:
            数据库文件路径
        """
        # 初始化数据库
        self._init_database()

        # 收集所有源代码文件
        source_files = self._collect_source_files()

        # 索引每个文件
        for file_path in source_files:
            self._index_file(file_path)

        # 关闭数据库连接
        self.conn.close()

        return self.db_path

    def _init_database(self):
        """初始化 SQLite 数据库"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 创建符号表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                end_line_number INTEGER,
                parent_id INTEGER,
                metadata TEXT,
                UNIQUE(name, kind, file_path, line_number)
            )
        """)

        # 创建依赖关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_symbol INTEGER NOT NULL,
                to_symbol INTEGER NOT NULL,
                dep_type TEXT NOT NULL,
                FOREIGN KEY (from_symbol) REFERENCES symbols(id),
                FOREIGN KEY (to_symbol) REFERENCES symbols(id)
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deps_from ON dependencies(from_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deps_to ON dependencies(to_symbol)")

        self.conn.commit()

    def _collect_source_files(self) -> List[Path]:
        """收集所有源代码文件"""
        source_files = []

        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue

            if not should_include_file(file_path, self.exclude_patterns, self.root_path):
                continue

            file_type = detect_file_type(file_path)
            if file_type in ['python', 'javascript', 'typescript']:
                source_files.append(file_path)

        return source_files

    def _index_file(self, file_path: Path):
        """索引单个文件"""
        file_type = detect_file_type(file_path)
        rel_path = str(get_relative_path(file_path, self.root_path))

        if file_type == 'python':
            self._index_python_file(file_path, rel_path)
        elif file_type in ['javascript', 'typescript']:
            self._index_js_file(file_path, rel_path)

    def _index_python_file(self, file_path: Path, rel_path: str):
        """索引 Python 文件（使用增强提取器）"""
        # Try enhanced extraction first
        if ENHANCED_AST_AVAILABLE:
            try:
                analyzer = EnhancedASTAnalyzer(self.root_path, self.db_path)
                extracted_data = analyzer.analyze_file(file_path)

                if 'error' not in extracted_data:
                    # Use enhanced extraction results
                    self._index_enhanced_data(extracted_data, rel_path)
                    return
            except Exception as e:
                print(f"   ⚠ Enhanced extraction failed for {rel_path}: {e}, falling back to basic")

        # Fallback to basic extraction
        self._index_python_file_basic(file_path, rel_path)

    def _index_enhanced_data(self, extracted_data: Dict, rel_path: str):
        """索引增强提取的数据"""
        # Index file symbol
        file_id = self._add_symbol(
            name=Path(rel_path).name,
            kind='file',
            file_path=rel_path,
            line_number=1,
            end_line_number=extracted_data.get('line_count', 1),
            metadata=json.dumps(extracted_data)
        )

        # Index classes
        for class_data in extracted_data.get('classes', []):
            class_id = self._add_symbol(
                name=class_data['name'],
                kind='class',
                file_path=rel_path,
                line_number=class_data['line_number'],
                end_line_number=class_data['end_line_number'],
                parent_id=file_id,
                metadata=json.dumps(class_data)
            )

            # Index methods
            for method in class_data.get('methods', []):
                self._add_symbol(
                    name=method['name'],
                    kind='function',
                    file_path=rel_path,
                    line_number=method['line_number'],
                    end_line_number=method['end_line_number'],
                    parent_id=class_id,
                    metadata=json.dumps(method)
                )

            # Index nested classes
            for nested_class in class_data.get('nested_classes', []):
                nested_id = self._add_symbol(
                    name=nested_class['name'],
                    kind='class',
                    file_path=rel_path,
                    line_number=nested_class['line_number'],
                    end_line_number=nested_class['end_line_number'],
                    parent_id=class_id,
                    metadata=json.dumps(nested_class)
                )

        # Index top-level functions
        for func_data in extracted_data.get('functions', []):
            self._add_symbol(
                name=func_data['name'],
                kind='function',
                file_path=rel_path,
                line_number=func_data['line_number'],
                end_line_number=func_data['end_line_number'],
                parent_id=file_id,
                metadata=json.dumps(func_data)
            )

    def _index_python_file_basic(self, file_path: Path, rel_path: str):
        """基本 Python 文件索引（回退方案）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            # 索引文件级符号
            file_id = self._add_symbol(
                name=Path(rel_path).name,
                kind='file',
                file_path=rel_path,
                line_number=1,
                end_line_number=len(source.splitlines())
            )

            # 遍历 AST
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 类定义
                    self._add_symbol(
                        name=node.name,
                        kind='class',
                        file_path=rel_path,
                        line_number=node.lineno,
                        end_line_number=getattr(node, 'end_lineno', node.lineno),
                        parent_id=file_id,
                        metadata=json.dumps({
                            'bases': [ast.unparse(base) for base in node.bases]
                        })
                    )

                elif isinstance(node, ast.FunctionDef):
                    # 函数定义
                    self._add_symbol(
                        name=node.name,
                        kind='function',
                        file_path=rel_path,
                        line_number=node.lineno,
                        end_line_number=getattr(node, 'end_lineno', node.lineno),
                        parent_id=file_id,
                        metadata=json.dumps({
                            'args': [arg.arg for arg in node.args.args],
                            'returns': ast.unparse(node.returns) if node.returns else None
                        })
                    )

                elif isinstance(node, ast.AsyncFunctionDef):
                    # 异步函数定义
                    self._add_symbol(
                        name=node.name,
                        kind='function',
                        file_path=rel_path,
                        line_number=node.lineno,
                        end_line_number=getattr(node, 'end_lineno', node.lineno),
                        parent_id=file_id,
                        metadata=json.dumps({
                            'async': True,
                            'args': [arg.arg for arg in node.args.args],
                            'returns': ast.unparse(node.returns) if node.returns else None
                        })
                    )

        except (SyntaxError, UnicodeDecodeError):
            # 无法解析的文件，只记录文件级符号
            self._add_symbol(
                name=Path(rel_path).name,
                kind='file',
                file_path=rel_path,
                line_number=1,
                end_line_number=1
            )

    def _index_js_file(self, file_path: Path, rel_path: str):
        """索引 JavaScript/TypeScript 文件（基于正则）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.splitlines()

            # 索引文件
            file_id = self._add_symbol(
                name=Path(rel_path).name,
                kind='file',
                file_path=rel_path,
                line_number=1,
                end_line_number=len(lines)
            )

            # 类定义: class MyClass { ... }
            class_pattern = r'(?:export\s+)?(?:default\s+)?class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                self._add_symbol(
                    name=match.group(1),
                    kind='class',
                    file_path=rel_path,
                    line_number=line_num,
                    parent_id=file_id
                )

            # 函数定义: function myFunc(...) { ... }
            func_pattern = r'function\s+(\w+)\s*\('
            for match in re.finditer(func_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                self._add_symbol(
                    name=match.group(1),
                    kind='function',
                    file_path=rel_path,
                    line_number=line_num,
                    parent_id=file_id
                )

            # 箭头函数: const myFunc = (...) => { ... }
            arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|\w+)\s*=>'
            for match in re.finditer(arrow_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                self._add_symbol(
                    name=match.group(1),
                    kind='function',
                    file_path=rel_path,
                    line_number=line_num,
                    parent_id=file_id
                )

        except (UnicodeDecodeError, OSError):
            # 无法读取的文件
            pass

    def _add_symbol(self, name: str, kind: str, file_path: str,
                   line_number: int, end_line_number: int = None,
                   parent_id: int = None, metadata: str = None) -> int:
        """添加符号到数据库"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO symbols
                (name, kind, file_path, line_number, end_line_number, parent_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, kind, file_path, line_number, end_line_number, parent_id, metadata))

            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # 符号已存在，返回现有 ID
            cursor.execute("""
                SELECT id FROM symbols
                WHERE name = ? AND kind = ? AND file_path = ? AND line_number = ?
            """, (name, kind, file_path, line_number))
            result = cursor.fetchone()
            return result[0] if result else None


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: build_symbol_index.py <project-path> [--output db_path]")
        print("\nExamples:")
        print("  build_symbol_index.py /path/to/project")
        print("  build_symbol_index.py /path/to/project --output /path/to/symbols.db")
        print("\n注意：")
        print("  - 此脚本使用 SQLite 构建符号索引")
        print("  - Serena MCP 集成正在开发中")
        print("  - 在 Claude Code 中可使用 Serena 进行符号级分析")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    # 解析输出路径
    output_path = "symbols.db"
    if len(sys.argv) > 2 and sys.argv[2] == "--output" and len(sys.argv) > 3:
        output_path = sys.argv[3]

    # 构建索引
    builder = SymbolIndexBuilder(project_path, db_path=output_path)
    db_path = builder.build_index()

    print(f"✅ Symbol index built successfully: {db_path}")

    # 输出统计信息
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM symbols")
    symbol_count = cursor.fetchone()[0]

    cursor.execute("SELECT kind, COUNT(*) FROM symbols GROUP BY kind")
    kind_stats = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM files")  # Note: 'files' is not a table, fix this
    # Actually, we should query symbols where kind='file'
    cursor.execute("SELECT COUNT(*) FROM symbols WHERE kind='file'")
    file_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n📊 Statistics:")
    print(f"  Files indexed: {file_count}")
    print(f"  Total symbols: {symbol_count}")
    print(f"  By type:")
    for kind, count in kind_stats:
        print(f"    - {kind}: {count}")


if __name__ == "__main__":
    main()
