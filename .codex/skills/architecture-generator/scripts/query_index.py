#!/usr/bin/env python3
"""
Symbol index query interface for architecture generator.

Provides a unified API for querying code symbols.
Supports both Serena MCP and SQLite backends.

Usage:
    query_index.py <project-path> <command> [args]

Commands:
    find <name>           Find symbols by name
    file <path>           List all symbols in a file
    search <keyword>      Search symbols by keyword
    stats                 Show index statistics
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SymbolIndex:
    """符号索引查询接口"""

    def __init__(self, project_path: str, db_path: str = "symbols.db"):
        """
        初始化符号索引

        Args:
            project_path: 项目根目录
            db_path: SQLite 数据库文件路径
        """
        self.project_path = Path(project_path)
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """连接到数据库"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def find_symbol(self, name: str, kind: Optional[str] = None) -> List[Dict]:
        """
        查找符号（类、函数、变量）

        Args:
            name: 符号名称
            kind: 符号类型过滤（'class', 'function', 'file' 等）

        Returns:
            符号列表
        """
        self.connect()
        cursor = self.conn.cursor()

        if kind:
            cursor.execute("""
                SELECT id, name, kind, file_path, line_number, end_line_number, parent_id, metadata
                FROM symbols
                WHERE name = ? AND kind = ?
                ORDER BY file_path, line_number
            """, (name, kind))
        else:
            cursor.execute("""
                SELECT id, name, kind, file_path, line_number, end_line_number, parent_id, metadata
                FROM symbols
                WHERE name = ?
                ORDER BY file_path, line_number
            """, (name,))

        results = cursor.fetchall()
        return [self._row_to_dict(row, cursor.description) for row in results]

    def search_symbols(self, keyword: str, kind: Optional[str] = None) -> List[Dict]:
        """
        搜索符号（模糊匹配）

        Args:
            keyword: 关键词
            kind: 符号类型过滤

        Returns:
            符号列表
        """
        self.connect()
        cursor = self.conn.cursor()

        if kind:
            cursor.execute("""
                SELECT id, name, kind, file_path, line_number, end_line_number, parent_id, metadata
                FROM symbols
                WHERE name LIKE ? AND kind = ?
                ORDER BY name, file_path, line_number
            """, (f"%{keyword}%", kind))
        else:
            cursor.execute("""
                SELECT id, name, kind, file_path, line_number, end_line_number, parent_id, metadata
                FROM symbols
                WHERE name LIKE ?
                ORDER BY name, file_path, line_number
            """, (f"%{keyword}%",))

        results = cursor.fetchall()
        return [self._row_to_dict(row, cursor.description) for row in results]

    def get_file_symbols(self, file_path: str) -> List[Dict]:
        """
        获取文件中的所有符号

        Args:
            file_path: 文件路径（相对路径）

        Returns:
            符号列表
        """
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, name, kind, file_path, line_number, end_line_number, parent_id, metadata
            FROM symbols
            WHERE file_path = ?
            ORDER BY line_number
        """, (file_path,))

        results = cursor.fetchall()
        return [self._row_to_dict(row, cursor.description) for row in results]

    def get_statistics(self) -> Dict:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        self.connect()
        cursor = self.conn.cursor()

        # 总符号数
        cursor.execute("SELECT COUNT(*) FROM symbols")
        total_symbols = cursor.fetchone()[0]

        # 按类型统计
        cursor.execute("""
            SELECT kind, COUNT(*) as count
            FROM symbols
            GROUP BY kind
            ORDER BY count DESC
        """)
        by_kind = {row[0]: row[1] for row in cursor.fetchall()}

        # 文件数
        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM symbols")
        total_files = cursor.fetchone()[0]

        # 按文件统计
        cursor.execute("""
            SELECT file_path, COUNT(*) as count
            FROM symbols
            GROUP BY file_path
            ORDER BY count DESC
            LIMIT 10
        """)
        top_files = [{"path": row[0], "symbols": row[1]} for row in cursor.fetchall()]

        return {
            "total_symbols": total_symbols,
            "total_files": total_files,
            "by_kind": by_kind,
            "top_files": top_files
        }

    def _row_to_dict(self, row: Tuple, description) -> Dict:
        """将数据库行转换为字典"""
        result = {}
        for i, col in enumerate(description):
            value = row[i]
            # 解析 JSON metadata
            if col[0] == 'metadata' and value:
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            result[col[0]] = value
        return result


def main():
    if len(sys.argv) < 3:
        print("Usage: query_index.py <project-path> <command> [args]")
        print("\nCommands:")
        print("  find <name>           Find symbols by name")
        print("  file <path>           List all symbols in a file")
        print("  search <keyword>      Search symbols by keyword")
        print("  stats                 Show index statistics")
        print("\nExamples:")
        print("  query_index.py /path/to/project find User")
        print("  query_index.py /path/to/project file src/main.py")
        print("  query_index.py /path/to/project search parse")
        print("  query_index.py /path/to/project stats")
        sys.exit(1)

    project_path = sys.argv[1]
    command = sys.argv[2]
    args = sys.argv[3:] if len(sys.argv) > 3 else []

    # 查找数据库文件
    db_path = None
    possible_paths = [
        Path(project_path) / "symbols.db",
        Path(project_path) / "docs" / "architecture" / ".cache" / "symbols.db",
    ]

    for path in possible_paths:
        if path.exists():
            db_path = str(path)
            break

    if not db_path:
        print(f"❌ Error: Symbol database not found in project")
        print(f"   Searched paths:")
        for path in possible_paths:
            print(f"     - {path}")
        sys.exit(1)

    # 创建索引实例
    index = SymbolIndex(project_path, db_path)

    try:
        if command == "find":
            if not args:
                print("❌ Error: 'find' command requires a symbol name")
                sys.exit(1)

            symbol_name = args[0]
            kind = args[1] if len(args) > 1 else None

            results = index.find_symbol(symbol_name, kind)

            if not results:
                print(f"❌ No symbols found with name: {symbol_name}")
            else:
                print(f"✅ Found {len(results)} symbol(s) with name: {symbol_name}\n")
                for symbol in results:
                    print(f"  - {symbol['kind']}: {symbol['name']}")
                    print(f"    Location: {symbol['file_path']}:{symbol['line_number']}")
                    if symbol.get('metadata'):
                        print(f"    Metadata: {json.dumps(symbol['metadata'], indent=6)}")
                    print()

        elif command == "search":
            if not args:
                print("❌ Error: 'search' command requires a keyword")
                sys.exit(1)

            keyword = args[0]
            kind = args[1] if len(args) > 1 else None

            results = index.search_symbols(keyword, kind)

            if not results:
                print(f"❌ No symbols found matching: {keyword}")
            else:
                print(f"✅ Found {len(results)} symbol(s) matching: {keyword}\n")
                for symbol in results[:20]:  # 限制输出数量
                    print(f"  - {symbol['kind']}: {symbol['name']}")
                    print(f"    Location: {symbol['file_path']}:{symbol['line_number']}")
                if len(results) > 20:
                    print(f"  ... and {len(results) - 20} more")

        elif command == "file":
            if not args:
                print("❌ Error: 'file' command requires a file path")
                sys.exit(1)

            file_path = args[0]
            results = index.get_file_symbols(file_path)

            if not results:
                print(f"❌ No symbols found in file: {file_path}")
            else:
                print(f"✅ Found {len(results)} symbol(s) in file: {file_path}\n")
                for symbol in results:
                    if symbol['kind'] != 'file':
                        print(f"  - {symbol['kind']}: {symbol['name']} (line {symbol['line_number']})")

        elif command == "stats":
            stats = index.get_statistics()

            print("📊 Symbol Index Statistics\n")
            print(f"Total symbols: {stats['total_symbols']}")
            print(f"Total files: {stats['total_files']}")
            print("\nBy type:")
            for kind, count in stats['by_kind'].items():
                print(f"  - {kind}: {count}")

            print("\nTop files by symbol count:")
            for file_info in stats['top_files']:
                print(f"  - {file_info['path']}: {file_info['symbols']} symbols")

        else:
            print(f"❌ Error: Unknown command: {command}")
            sys.exit(1)

    finally:
        index.close()


if __name__ == "__main__":
    main()
