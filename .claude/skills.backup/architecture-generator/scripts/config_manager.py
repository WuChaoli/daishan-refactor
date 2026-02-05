#!/usr/bin/env python3
"""
Configuration file support for architecture generator (Phase 3).

Supports .architecture-generator.yaml configuration files.

Configuration options:
- node_threshold: Dependency graph node threshold
- max_depth: Maximum scan depth
- incremental: Enable/disable incremental scanning
- exclude: Additional exclude patterns
- output_dir: Custom output directory
- index_type: 'auto', 'sqlite' (future: 'serena')
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_CONFIG = {
    'node_threshold': 25,
    'max_depth': None,
    'incremental': True,
    'exclude': [],
    'output_dir': 'docs/architecture',
    'index_type': 'auto',
    'include_tests': True,
}


class Config:
    """配置管理器"""

    def __init__(self, project_path: Path, config_file: Path = None):
        """
        初始化配置

        Args:
            project_path: 项目根目录
            config_file: 配置文件路径（默认: .architecture-generator.yaml）
        """
        self.project_path = Path(project_path).resolve()

        if config_file is None:
            config_file = self.project_path / '.architecture-generator.yaml'

        self.config_file = config_file
        self.config = DEFAULT_CONFIG.copy()

        # 加载配置文件
        if self.config_file.exists():
            self._load_config()

    def _load_config(self):
        """加载 YAML 配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)

            if user_config:
                # 合并配置
                self.config.update(user_config)

        except (yaml.YAMLError, IOError) as e:
            print(f"⚠️  Warning: Failed to load config file: {e}")
            print(f"   Using default configuration")

    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self.config.copy()

    def save_example(self):
        """保存示例配置文件到项目根目录"""
        example_config = """# Architecture Generator Configuration
# 配置文件说明：此文件控制架构文档生成行为

# 依赖图节点数阈值（当节点数超过此值时，自动拆分为多层图）
node_threshold: 25

# 最大扫描深度（null 表示无限制）
max_depth: null

# 是否启用增量扫描（只扫描修改过的文件）
incremental: true

# 额外的排除模式（遵循 .gitignore 语法）
exclude:
  - node_modules/
  - __pycache__/
  - "*.min.js"
  - "*.min.css"

# 输出目录（相对于项目根目录）
output_dir: docs/architecture

# 符号索引类型：auto, sqlite, serena
# - auto: 自动选择（优先 Serena，降级到 SQLite）
# - sqlite: 强制使用 SQLite
# - serena: 强制使用 Serena MCP（需要 Serena 可用）
index_type: auto

# 是否包含测试文件
include_tests: true
"""

        example_file = self.project_path / '.architecture-generator.yaml.example'
        example_file.write_text(example_config, encoding='utf-8')
        print(f"✅ Example configuration saved to: {example_file}")
        print(f"   To use it, rename to: .architecture-generator.yaml")

    def __repr__(self) -> str:
        return f"Config({self.config_file})"


def load_config(project_path: Path, config_file: Path = None) -> Config:
    """
    便捷函数：加载项目配置

    Args:
        project_path: 项目根目录
        config_file: 配置文件路径

    Returns:
        Config 实例
    """
    return Config(project_path, config_file)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: config_manager.py <project-path> [--example]")
        print("\nExamples:")
        print("  config_manager.py /path/to/project")
        print("  config_manager.py /path/to/project --example")
        sys.exit(1)

    project_path = Path(sys.argv[1])

    if len(sys.argv) > 2 and sys.argv[2] == "--example":
        # 生成示例配置
        config = Config(project_path)
        config.save_example()
    else:
        # 显示当前配置
        config = Config(project_path)
        print(f"📋 Configuration for: {project_path}")
        print(f"   Config file: {config.config_file}")

        if config.config_file.exists():
            print(f"   Status: ✅ Loaded")
            print(f"\nCurrent settings:")
            for key, value in config.get_all().items():
                if value is not None and value != []:
                    print(f"   - {key}: {value}")
        else:
            print(f"   Status: ⚠️  Not found (using defaults)")
            print(f"\nTo create a config file, run:")
            print(f"   python {sys.argv[0]} {project_path} --example")


if __name__ == "__main__":
    main()
