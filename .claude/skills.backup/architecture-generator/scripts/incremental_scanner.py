#!/usr/bin/env python3
"""
Incremental scanner for architecture generator (Phase 3).

Tracks file modifications and only scans changed files for faster updates.

Features:
- File modification time tracking
- Cached scan results
- Incremental updates
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class IncrementalScanner:
    """增量扫描器（Phase 3）"""

    def __init__(self, project_path: Path, cache_dir: Path = None):
        """
        初始化增量扫描器

        Args:
            project_path: 项目根目录
            cache_dir: 缓存目录（默认: docs/architecture/.cache）
        """
        self.project_path = Path(project_path).resolve()
        if cache_dir is None:
            cache_dir = self.project_path / "docs" / "architecture" / ".cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "scan_cache.json"
        self.file_hashes: Dict[str, str] = {}
        self.last_scan_time: Optional[float] = None

        # 加载缓存
        self._load_cache()

    def _load_cache(self):
        """加载扫描缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.file_hashes = cache_data.get('file_hashes', {})
                    self.last_scan_time = cache_data.get('last_scan_time')
            except (json.JSONDecodeError, KeyError):
                # 缓存文件损坏，重新开始
                self.file_hashes = {}
                self.last_scan_time = None

    def _save_cache(self):
        """保存扫描缓存"""
        cache_data = {
            'last_scan_time': datetime.now().timestamp(),
            'file_hashes': self.file_hashes
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """
        计算文件哈希值（基于修改时间和大小）

        Args:
            file_path: 文件路径

        Returns:
            哈希字符串
        """
        if not file_path.exists():
            return None

        stat = file_path.stat()
        # 使用修改时间、文件大小和文件名生成哈希
        hash_input = f"{stat.st_mtime}:{stat.st_size}:{file_path}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def get_changed_files(self, file_list: List[Path]) -> List[Path]:
        """
        获取自上次扫描以来修改过的文件

        Args:
            file_list: 要检查的文件列表

        Returns:
            修改过的文件列表
        """
        changed_files = []

        for file_path in file_list:
            rel_path = str(file_path.relative_to(self.project_path))
            current_hash = self._get_file_hash(file_path)

            if current_hash is None:
                # 文件不存在，跳过
                continue

            if rel_path not in self.file_hashes:
                # 新文件
                changed_files.append(file_path)
            elif self.file_hashes[rel_path] != current_hash:
                # 文件已修改
                changed_files.append(file_path)

        return changed_files

    def get_deleted_files(self, file_list: List[Path]) -> List[str]:
        """
        获取已删除的文件

        Args:
            file_list: 当前存在的文件列表

        Returns:
            已删除文件的相对路径列表
        """
        current_files = set()
        for file_path in file_list:
            rel_path = str(file_path.relative_to(self.project_path))
            current_files.add(rel_path)

        deleted_files = []
        for cached_file in self.file_hashes.keys():
            if cached_file not in current_files:
                deleted_files.append(cached_file)

        return deleted_files

    def update_cache(self, scanned_files: List[Path]):
        """
        更新缓存

        Args:
            scanned_files: 已扫描的文件列表
        """
        for file_path in scanned_files:
            if file_path.exists():
                rel_path = str(file_path.relative_to(self.project_path))
                self.file_hashes[rel_path] = self._get_file_hash(file_path)

        self._save_cache()

    def clear_cache(self):
        """清空缓存"""
        self.file_hashes = {}
        self.last_scan_time = None
        if self.cache_file.exists():
            self.cache_file.unlink()

    def needs_full_scan(self, file_list: List[Path], threshold: float = 0.5) -> bool:
        """
        判断是否需要全量扫描

        Args:
            file_list: 文件列表
            threshold: 变更比例阈值（超过此比例则全量扫描）

        Returns:
            如果需要全量扫描则返回 True
        """
        if not self.file_hashes:
            # 首次扫描
            return True

        changed_files = self.get_changed_files(file_list)
        change_ratio = len(changed_files) / len(file_list) if file_list else 0

        return change_ratio > threshold

    def get_scan_stats(self) -> Dict:
        """
        获取扫描统计信息

        Returns:
            统计信息字典
        """
        return {
            "last_scan_time": datetime.fromtimestamp(self.last_scan_time).isoformat() if self.last_scan_time else None,
            "cached_files": len(self.file_hashes),
            "cache_file": str(self.cache_file)
        }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: incremental_scanner.py <project-path> [--clear]")
        print("\nExamples:")
        print("  incremental_scanner.py /path/to/project")
        print("  incremental_scanner.py /path/to/project --clear")
        sys.exit(1)

    project_path = Path(sys.argv[1])

    scanner = IncrementalScanner(project_path)

    if len(sys.argv) > 2 and sys.argv[2] == "--clear":
        print("🗑️  Clearing scan cache...")
        scanner.clear_cache()
        print("   ✅ Cache cleared")
        return

    # 显示统计信息
    stats = scanner.get_scan_stats()
    print(f"📊 Scan Cache Statistics:")
    print(f"   Last scan: {stats['last_scan_time'] or 'Never'}")
    print(f"   Cached files: {stats['cached_files']}")
    print(f"   Cache file: {stats['cache_file']}")


if __name__ == "__main__":
    main()
