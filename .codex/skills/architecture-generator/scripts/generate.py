#!/usr/bin/env python3
"""
Architecture generator main script (Phase 3).

Orchestrates the complete architecture documentation generation process:
1. Scan file structure (with incremental support)
2. Analyze dependencies
3. Build symbol index
4. Generate documentation from templates

Phase 3 Features:
- Incremental scanning (only modified files)
- Multi-language support extensions
- Performance optimizations
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from scan_file_structure import scan_directory
from analyze_dependencies import DependencyAnalyzer
from build_symbol_index import SymbolIndexBuilder
from query_index import SymbolIndex
from incremental_scanner import IncrementalScanner
from config_manager import load_config


def load_template(template_path: Path) -> str:
    """加载模板文件"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template: str, **kwargs) -> str:
    """渲染模板（支持 Jinja2 或简单替换）"""
    if HAS_JINJA2:
        # 使用 Jinja2
        return Template(template).render(**kwargs)
    else:
        # 降级到简单替换（只支持 {{ variable }}）
        result = template
        for key, value in kwargs.items():
            placeholder = "{{ " + key + " }}"
            result = result.replace(placeholder, str(value))

        # 处理简单的 for 循环（仅用于基本支持）
        import re
        # 匹配 {% for ext, count in stats.by_extension.items() %}
        for_loop_pattern = r'{%\s+for\s+(\w+),\s*(\w+)\s+in\s+(\w+)\.(\w+)\.items\(\)\s+%}([\s\S]*?){%\s+endfor\s+%}'

        def replace_for_loop(match):
            var1, var2, dict_name, dict_key, body = match.groups()
            items = kwargs.get(dict_name, {}).items()
            result_lines = []
            for k, v in items:
                body_replaced = body.replace(f"{{{{{var1}}}}}", str(k))
                body_replaced = body_replaced.replace(f"{{{{{var2}}}}}", str(v))
                result_lines.append(body_replaced)
            return "\n".join(result_lines)

        result = re.sub(for_loop_pattern, replace_for_loop, result)
        return result


def generate_architecture_docs(
    project_path: Path,
    output_dir: Path = None,
    gitignore_path: Path = None,
    max_depth: int = None,
    node_threshold: int = 25,
    incremental: bool = True
):
    """
    生成项目架构文档

    Args:
        project_path: 项目根目录
        output_dir: 输出目录（默认: docs/static/architecture/）
        gitignore_path: .gitignore 文件路径
        max_depth: 最大扫描深度
        node_threshold: 依赖图节点数阈值（默认: 25）
        incremental: 是否使用增量扫描（默认: True）
    """
    project_path = project_path.resolve()

    # 加载配置文件（Phase 3）
    config = load_config(project_path)

    # 应用配置文件中的设置（如果没有命令行参数覆盖）
    if output_dir is None and config.get('output_dir'):
        output_dir = project_path / config.get('output_dir')
    if max_depth is None and config.get('max_depth'):
        max_depth = config.get('max_depth')
    if node_threshold == 25 and config.get('node_threshold'):
        node_threshold = config.get('node_threshold')
    if not incremental and config.get('incremental'):
        incremental = config.get('incremental')

    # 设置输出目录
    if output_dir is None:
        output_dir = project_path / "docs" / "static" / "architecture"
    else:
        output_dir = output_dir.resolve()

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dependencies").mkdir(exist_ok=True)
    (output_dir / ".cache").mkdir(exist_ok=True)

    print(f"🚀 Generating architecture documentation for: {project_path}")
    print(f"📁 Output directory: {output_dir}\n")

    # 初始化增量扫描器
    incremental_scanner = IncrementalScanner(project_path, output_dir / ".cache")

    # 1. 扫描文件结构（支持增量）
    print("📂 Step 1: Scanning file structure...")
    if gitignore_path is None:
        gitignore_path = project_path / ".gitignore"

    # 检查是否需要全量扫描
    from utils import get_default_excludes, should_include_file, detect_file_type

    all_files = list(project_path.rglob('*'))
    source_files = [f for f in all_files if f.is_file() and should_include_file(f, get_default_excludes(), project_path)]

    use_incremental = incremental and not incremental_scanner.needs_full_scan(source_files)

    if use_incremental:
        print("   🔄 Using incremental scan (only modified files)")
        changed_files = incremental_scanner.get_changed_files(source_files)
        deleted_files = incremental_scanner.get_deleted_files(source_files)

        if changed_files:
            print(f"   📝 {len(changed_files)} modified files detected")
        if deleted_files:
            print(f"   🗑️  {len(deleted_files)} deleted files detected")
    else:
        print("   🔄 Performing full scan")

    file_structure = scan_directory(project_path, gitignore_path, max_depth, project_path)
    print(f"   ✅ Found {file_structure['stats']['total_files']} files\n")

    # 2. 分析依赖关系（支持分层）
    print("🔗 Step 2: Analyzing dependencies...")
    dep_analyzer = DependencyAnalyzer(project_path, gitignore_path, node_threshold)
    dependencies = dep_analyzer.analyze_project()

    # 输出分层信息
    level_count = len([k for k in dependencies.keys() if k.startswith("level_")])
    print(f"   ✅ Generated {level_count} level(s) of dependency graphs")
    for level_key in sorted(dependencies.keys()):
        if level_key.startswith("level_"):
            level_data = dependencies[level_key]
            if isinstance(level_data, dict) and "stats" in level_data:
                print(f"      - {level_key}: {level_data['stats']['node_count']} nodes, {level_data['stats']['edge_count']} edges")
            elif isinstance(level_data, dict):
                # 子层级
                for sub_key, sub_data in level_data.items():
                    if isinstance(sub_data, dict) and "stats" in sub_data:
                        print(f"      - {level_key}/{sub_key}: {sub_data['stats']['node_count']} nodes, {sub_data['stats']['edge_count']} edges")
    print()

    # 3. 构建符号索引
    print("📊 Step 3: Building symbol index...")
    db_path = output_dir / ".cache" / "symbols.db"

    # 使用自动降级模式（非交互环境）
    index_builder = SymbolIndexBuilder(
        project_path,
        str(db_path),
        gitignore_path,
        auto_fallback=True  # 自动降级，不询问用户
    )

    result_db_path = index_builder.build_index()

    if result_db_path is None:
        print("   ⏭️  Symbol index generation skipped")
        # 创建空的统计信息
        stats = {
            "total_symbols": 0,
            "total_files": 0,
            "by_kind": {}
        }
    else:
        # 获取统计信息
        index = SymbolIndex(str(project_path), str(db_path))
        stats = index.get_statistics()
        print(f"   ✅ Indexed {stats['total_symbols']} symbols in {stats['total_files']} files\n")
        index.close()

    # 4. 生成文档
    print("📝 Step 4: Generating documentation...")

    # 获取模板目录
    script_dir = Path(__file__).parent
    templates_dir = script_dir / ".." / "assets" / "templates"
    templates_dir = templates_dir.resolve()

    # 准备模板变量
    try:
        relative_output = output_dir.relative_to(project_path)
    except ValueError:
        # 输出目录不在项目内，使用绝对路径
        relative_output = output_dir

    template_vars = {
        "project_name": project_path.name,
        "project_path": str(project_path),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "docs_dir": str(relative_output),
        "index_db_path": str(relative_output / ".cache" / "symbols.db"),
        "scripts_dir": ".architecture-generator",  # 相对路径
        "stats": file_structure["stats"],
        "max_depth": max_depth if max_depth else "无限制",
        "total_symbols": stats["total_symbols"],
        "total_files": stats["total_files"],
        "by_kind": stats["by_kind"],
        "db_path": str(relative_output / ".cache" / "symbols.db"),
    }

    # 生成 README.md
    readme_template = load_template(templates_dir / "README.md.j2")
    readme_content = render_template(readme_template, **template_vars)
    (output_dir / "README.md").write_text(readme_content, encoding='utf-8')
    print(f"   ✅ Generated README.md")

    # 生成 file-structure.md
    file_tree_template = load_template(templates_dir / "file-structure.md.j2")
    template_vars["file_tree"] = file_structure["tree"]
    file_tree_content = render_template(file_tree_template, **template_vars)
    (output_dir / "file-structure.md").write_text(file_tree_content, encoding='utf-8')
    print(f"   ✅ Generated file-structure.md")

    # 生成依赖关系文档（支持分层）
    deps_template = load_template(templates_dir / "dependency-graph.md.j2")

    # 生成 level-0（顶层依赖）
    if "level_0" in dependencies:
        level_0 = dependencies["level_0"]
        template_vars.update({
            "mermaid_graph": level_0["mermaid"],
            "stats": level_0["stats"],
            "nodes": level_0["nodes"],
            "edges": level_0["edges"],
            "level": 0,
        })
        deps_content = render_template(deps_template, **template_vars)
        (output_dir / "dependencies" / "level-0.md").write_text(deps_content, encoding='utf-8')
        print(f"   ✅ Generated dependencies/level-0.md")

    # 生成 level-1（文件夹级依赖）
    if "level_1" in dependencies:
        for folder, folder_data in dependencies["level_1"].items():
            if isinstance(folder_data, dict) and "stats" in folder_data:
                # 这是文件夹级图
                template_vars.update({
                    "mermaid_graph": folder_data["mermaid"],
                    "stats": folder_data["stats"],
                    "nodes": folder_data["nodes"],
                    "edges": folder_data["edges"],
                    "level": 1,
                    "folder": folder,
                })
                deps_content = render_template(deps_template, **template_vars)
                (output_dir / "dependencies" / f"level-1-{folder}.md").write_text(deps_content, encoding='utf-8')
                print(f"   ✅ Generated dependencies/level-1-{folder}.md")

    # 生成 level-2（子文件夹级依赖）
    if "level_2" in dependencies:
        for subfolder, subfolder_data in dependencies["level_2"].items():
            if isinstance(subfolder_data, dict) and "stats" in subfolder_data:
                template_vars.update({
                    "mermaid_graph": subfolder_data["mermaid"],
                    "stats": subfolder_data["stats"],
                    "nodes": subfolder_data["nodes"],
                    "edges": subfolder_data["edges"],
                    "level": 2,
                    "folder": subfolder,
                })
                deps_content = render_template(deps_template, **template_vars)
                # 安全的文件名
                safe_name = subfolder.replace("/", "-")
                (output_dir / "dependencies" / f"level-2-{safe_name}.md").write_text(deps_content, encoding='utf-8')
                print(f"   ✅ Generated dependencies/level-2-{safe_name}.md")

    print()

    # 生成 symbols-index.md
    symbols_template = load_template(templates_dir / "symbols-index.md.j2")
    symbols_content = render_template(symbols_template, **template_vars)
    (output_dir / "symbols-index.md").write_text(symbols_content, encoding='utf-8')
    print(f"   ✅ Generated symbols-index.md\n")

    # 更新增量扫描缓存
    if use_incremental:
        print("💾 Updating scan cache...")
        incremental_scanner.update_cache(source_files)
        print("   ✅ Cache updated\n")

    # 完成
    print("=" * 60)
    print("✅ Architecture documentation generated successfully!")
    print("=" * 60)
    print(f"\n📚 View the documentation:")
    print(f"   {output_dir / 'README.md'}")
    print(f"\n🔍 Query symbols:")
    print(f"   python {script_dir / 'query_index.py'} {project_path} stats")


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate architecture documentation for a project"
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to the project root directory"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory (default: docs/static/architecture/)"
    )
    parser.add_argument(
        "--gitignore",
        type=Path,
        default=None,
        help="Path to .gitignore file (default: <project>/.gitignore)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum scan depth (default: unlimited)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=25,
        help="Dependency graph node threshold for splitting (default: 25)"
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Force a full scan (ignore incremental cache)"
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="Disable incremental scanning"
    )

    args = parser.parse_args()

    if not args.project_path.exists():
        print(f"❌ Error: Project path does not exist: {args.project_path}")
        sys.exit(1)

    incremental = not (args.full_scan or args.no_incremental)

    generate_architecture_docs(
        project_path=args.project_path,
        output_dir=args.output,
        gitignore_path=args.gitignore,
        max_depth=args.max_depth,
        node_threshold=args.threshold,
        incremental=incremental
    )


if __name__ == "__main__":
    main()
