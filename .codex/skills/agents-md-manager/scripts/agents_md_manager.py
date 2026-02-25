#!/usr/bin/env python3
"""Manage AGENTS.md dynamic governance blocks."""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

BLOCK_PROJECT_STRUCTURE = "PROJECT_STRUCTURE_SNAPSHOT"
BLOCK_RULE_VERSION_HISTORY = "RULE_VERSION_HISTORY"
BLOCK_MAINTENANCE_OWNERSHIP = "MAINTENANCE_OWNERSHIP"
BLOCK_VALIDATION_COMMANDS = "VALIDATION_COMMANDS"
BLOCK_UPDATE_FREQUENCY_POLICY = "UPDATE_FREQUENCY_POLICY"
BLOCK_EXCEPTION_APPROVAL_PROCESS = "EXCEPTION_APPROVAL_PROCESS"
BLOCK_CONFLICT_PRIORITY = "CONFLICT_PRIORITY"
BLOCK_GLOSSARY = "GLOSSARY"
BLOCK_CHANGE_IMPACT_SCOPE = "CHANGE_IMPACT_SCOPE"

BLOCK_ORDER: Sequence[Tuple[str, str]] = (
    (BLOCK_PROJECT_STRUCTURE, "项目结构快照（动态）"),
    (BLOCK_RULE_VERSION_HISTORY, "规则版本历史"),
    (BLOCK_MAINTENANCE_OWNERSHIP, "维护责任"),
    (BLOCK_VALIDATION_COMMANDS, "校验命令清单"),
    (BLOCK_UPDATE_FREQUENCY_POLICY, "更新频率策略"),
    (BLOCK_EXCEPTION_APPROVAL_PROCESS, "例外审批流程"),
    (BLOCK_CONFLICT_PRIORITY, "冲突优先级"),
    (BLOCK_GLOSSARY, "术语表"),
    (BLOCK_CHANGE_IMPACT_SCOPE, "变更影响范围"),
)

GOVERNANCE_BLOCK_IDS = {
    BLOCK_RULE_VERSION_HISTORY,
    BLOCK_MAINTENANCE_OWNERSHIP,
    BLOCK_VALIDATION_COMMANDS,
    BLOCK_UPDATE_FREQUENCY_POLICY,
    BLOCK_EXCEPTION_APPROVAL_PROCESS,
    BLOCK_CONFLICT_PRIORITY,
    BLOCK_GLOSSARY,
    BLOCK_CHANGE_IMPACT_SCOPE,
}

BLOCK_IDS = {block_id for block_id, _ in BLOCK_ORDER}
KEY_ROOT_FILES = (
    "AGENTS.md",
    "README.md",
    "README.en.md",
    "main.py",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
)

IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
}

THRESHOLD_FILE_COUNT = 200
THRESHOLD_MAX_DEPTH = 6


@dataclass(frozen=True)
class RepoStats:
    file_count: int
    max_depth: int
    mode: str
    tree_text: str
    generated_date: str
    root_name: str


def begin_marker(block_id: str) -> str:
    return f"<!-- BEGIN AGENTS-DYNAMIC:{block_id} -->"


def end_marker(block_id: str) -> str:
    return f"<!-- END AGENTS-DYNAMIC:{block_id} -->"


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def should_skip_dir(name: str) -> bool:
    if name in IGNORE_DIR_NAMES:
        return True
    if name.startswith("tmpclaude-"):
        return True
    return False


def should_skip_file(name: str) -> bool:
    return name.endswith(".pyc")


def compute_file_count_and_depth(root: Path) -> Tuple[int, int]:
    file_count = 0
    max_depth = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        rel_dir = dirpath.relative_to(root)
        if rel_dir != Path("."):
            max_depth = max(max_depth, len(rel_dir.parts))

        for filename in filenames:
            if should_skip_file(filename):
                continue
            file_count += 1
            rel_file = (dirpath / filename).relative_to(root)
            max_depth = max(max_depth, len(rel_file.parts))

    return file_count, max_depth


def add_dir(tree: Dict[str, dict], rel_parts: Iterable[str]) -> None:
    cursor = tree
    for part in rel_parts:
        cursor = cursor.setdefault(part, {})


def add_file(tree: Dict[str, dict], rel_parts: Sequence[str]) -> None:
    if not rel_parts:
        return
    cursor = tree
    for part in rel_parts[:-1]:
        cursor = cursor.setdefault(part, {})
    files = cursor.setdefault("__files__", [])
    if rel_parts[-1] not in files:
        files.append(rel_parts[-1])


def render_tree(root_name: str, tree: Dict[str, dict]) -> str:
    lines = [f"{root_name}/"]

    def walk(node: Dict[str, dict], prefix: str) -> None:
        dir_names = sorted(k for k in node.keys() if k != "__files__")
        file_names = sorted(node.get("__files__", []))
        entries: List[Tuple[str, str]] = [("dir", name) for name in dir_names]
        entries.extend(("file", name) for name in file_names)

        for index, (kind, name) in enumerate(entries):
            is_last = index == len(entries) - 1
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")
            if kind == "dir":
                lines.append(f"{prefix}{connector}{name}/")
                walk(node[name], next_prefix)
            else:
                lines.append(f"{prefix}{connector}{name}")

    walk(tree, "")
    return "\n".join(lines)


def build_full_tree(root: Path) -> str:
    tree: Dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        rel_dir = dirpath.relative_to(root)
        if rel_dir != Path("."):
            add_dir(tree, rel_dir.parts)

        for filename in filenames:
            if should_skip_file(filename):
                continue
            rel_file = (dirpath / filename).relative_to(root)
            add_file(tree, rel_file.parts)

    return render_tree(root.name, tree)


def build_directory_level_tree(root: Path) -> str:
    tree: Dict[str, dict] = {}

    for file_name in KEY_ROOT_FILES:
        file_path = root / file_name
        if file_path.is_file():
            add_file(tree, (file_name,))

    top_dirs = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if should_skip_dir(child.name):
            continue
        top_dirs.append(child)

    for top_dir in sorted(top_dirs, key=lambda p: p.name):
        add_dir(tree, (top_dir.name,))
        level1_dirs = []
        for child in top_dir.iterdir():
            if not child.is_dir():
                continue
            if should_skip_dir(child.name):
                continue
            level1_dirs.append(child)

        for level1 in sorted(level1_dirs, key=lambda p: p.name):
            add_dir(tree, (top_dir.name, level1.name))
            if top_dir.name in {"src", "docs", "openspec", "test", ".codex", ".company"}:
                level2_dirs = []
                for child in level1.iterdir():
                    if not child.is_dir():
                        continue
                    if should_skip_dir(child.name):
                        continue
                    level2_dirs.append(child)
                for level2 in sorted(level2_dirs, key=lambda p: p.name):
                    add_dir(tree, (top_dir.name, level1.name, level2.name))

    return render_tree(root.name, tree)


def collect_repo_stats(root: Path) -> RepoStats:
    file_count, max_depth = compute_file_count_and_depth(root)
    mode = (
        "full-recursive"
        if file_count <= THRESHOLD_FILE_COUNT and max_depth <= THRESHOLD_MAX_DEPTH
        else "directory-plus-key-files"
    )
    tree_text = build_full_tree(root) if mode == "full-recursive" else build_directory_level_tree(root)
    generated_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return RepoStats(
        file_count=file_count,
        max_depth=max_depth,
        mode=mode,
        tree_text=tree_text,
        generated_date=generated_date,
        root_name=root.name,
    )


def block_content_from_stats(stats: RepoStats) -> Dict[str, str]:
    return {
        BLOCK_PROJECT_STRUCTURE: (
            "### 结构展示策略（阈值）\n"
            f"- 文件数阈值：`<= {THRESHOLD_FILE_COUNT}`\n"
            f"- 目录深度阈值：`<= {THRESHOLD_MAX_DEPTH}`\n"
            f"- 当前文件数：`{stats.file_count}`\n"
            f"- 当前最大深度：`{stats.max_depth}`\n"
            f"- 当前展示模式：`{stats.mode}`\n"
            f"- 生成日期（UTC）：`{stats.generated_date}`\n\n"
            "### 当前结构快照\n"
            "```text\n"
            f"{stats.tree_text}\n"
            "```"
        ),
        BLOCK_RULE_VERSION_HISTORY: (
            "- version: `2.1.0`\n"
            f"- last_updated: `{stats.generated_date}`\n"
            "- change_note: `agents-md-manager sync governance blocks`\n"
            "- previous_baseline: `2.0.0`"
        ),
        BLOCK_MAINTENANCE_OWNERSHIP: (
            "- owner: `项目维护者`\n"
            "- reviewer: `代码评审负责人`\n"
            "- 修改权限边界: `仅允许通过 agents-md-manager 修改动态区块；静态规范由人工评审修改`"
        ),
        BLOCK_VALIDATION_COMMANDS: (
            "- `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py init-blocks --agents AGENTS.md`：初始化缺失区块，成功返回 `0`。\n"
            "- `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py sync --agents AGENTS.md --root .`：重算并同步动态区块，成功返回 `0`。\n"
            "- `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py check --agents AGENTS.md --root .`：校验标记、缺失区块、结构统计一致性；失败返回 `1`。\n"
            "- `python .codex/skills/agents-md-manager/scripts/agents_md_manager.py diff --agents AGENTS.md --root .`：输出即将变更的区块和摘要行数，成功返回 `0`。"
        ),
        BLOCK_UPDATE_FREQUENCY_POLICY: (
            "- 结构快照：每次执行 `sync` 必须重算并刷新。\n"
            "- 治理区块：规则内容变更后立即执行 `sync`。\n"
            "- 提交前校验：必须执行 `check`，失败禁止提交。"
        ),
        BLOCK_EXCEPTION_APPROVAL_PROCESS: (
            "- 允许例外条件：`紧急故障、合规强制、生产止损`。\n"
            "- 审批记录模板：`[date][approver][reason][expiry][scope]`。\n"
            "- 失效时间：默认 `24h`，到期后必须回归 AGENTS 基线并补充复盘。"
        ),
        BLOCK_CONFLICT_PRIORITY: (
            "1. 系统/平台指令\n"
            "2. 开发者指令\n"
            "3. `AGENTS.md` 项目规则\n"
            "4. Skill 局部规则"
        ),
        BLOCK_GLOSSARY: (
            "- `context-id`：上下文目录唯一标识，格式 `YYYY-MM-DD_<task>`。\n"
            "- `active/archived`：上下文状态，分别对应进行中与归档。\n"
            "- `dynamic block`：由 marker 包裹、允许脚本自动改写的区块。\n"
            "- `baseline`：当前生效规范基线版本。"
        ),
        BLOCK_CHANGE_IMPACT_SCOPE: (
            "- 影响范围：`AGENTS.md` 动态区块、提交前校验流程、项目结构快照。\n"
            "- 不自动修复：`CLAUDE.md`、`activate-*`、`project-init` 等外部引用漂移。\n"
            "- 审计要求：`diff` 输出变更区块与行数摘要，供评审记录。"
        ),
    }


def extract_block_body(text: str, block_id: str) -> str | None:
    pattern = re.compile(
        re.escape(begin_marker(block_id)) + r"\n(.*?)\n" + re.escape(end_marker(block_id)),
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1)


def replace_block_body(text: str, block_id: str, body: str) -> str:
    replacement = f"{begin_marker(block_id)}\n{body.rstrip()}\n{end_marker(block_id)}"
    pattern = re.compile(
        re.escape(begin_marker(block_id)) + r"\n.*?\n" + re.escape(end_marker(block_id)),
        re.DOTALL,
    )
    return pattern.sub(replacement, text, count=1)


def validate_markers(text: str) -> Tuple[List[str], Dict[str, int], Dict[str, int]]:
    errors: List[str] = []
    begin_counts: Dict[str, int] = {}
    end_counts: Dict[str, int] = {}

    begin_pattern = re.compile(r"<!-- BEGIN AGENTS-DYNAMIC:([A-Z0-9_]+) -->")
    end_pattern = re.compile(r"<!-- END AGENTS-DYNAMIC:([A-Z0-9_]+) -->")

    for block_id in begin_pattern.findall(text):
        begin_counts[block_id] = begin_counts.get(block_id, 0) + 1
    for block_id in end_pattern.findall(text):
        end_counts[block_id] = end_counts.get(block_id, 0) + 1

    unknown_markers = sorted((set(begin_counts) | set(end_counts)) - BLOCK_IDS)
    if unknown_markers:
        errors.append(f"Unknown block ids in markers: {', '.join(unknown_markers)}")

    for block_id in sorted(BLOCK_IDS):
        begin_count = begin_counts.get(block_id, 0)
        end_count = end_counts.get(block_id, 0)
        if begin_count != end_count:
            errors.append(
                f"Marker mismatch for {block_id}: begin={begin_count}, end={end_count}"
            )
        if begin_count > 1:
            errors.append(f"Duplicate markers for {block_id}: {begin_count}")

    return errors, begin_counts, end_counts


def append_missing_blocks(text: str) -> Tuple[str, List[str]]:
    existing = {
        block_id
        for block_id in BLOCK_IDS
        if begin_marker(block_id) in text and end_marker(block_id) in text
    }
    missing = [block_id for block_id, _ in BLOCK_ORDER if block_id not in existing]
    if not missing:
        return text, []

    lines = [text.rstrip(), "", "## AGENTS 动态治理区块（agents-md-manager）", ""]
    for block_id, title in BLOCK_ORDER:
        if block_id not in missing:
            continue
        lines.append(f"### {title}")
        lines.append(begin_marker(block_id))
        lines.append("TODO: run sync to populate this block.")
        lines.append(end_marker(block_id))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n", missing


def parse_structure_metadata(block_body: str) -> Tuple[int | None, int | None]:
    file_count_match = re.search(r"当前文件数：`(\d+)`", block_body)
    max_depth_match = re.search(r"当前最大深度：`(\d+)`", block_body)

    file_count = int(file_count_match.group(1)) if file_count_match else None
    max_depth = int(max_depth_match.group(1)) if max_depth_match else None
    return file_count, max_depth


def apply_sync_to_text(text: str, stats: RepoStats) -> Tuple[str, Dict[str, Tuple[str, str]]]:
    generated = block_content_from_stats(stats)
    changed: Dict[str, Tuple[str, str]] = {}
    updated = text

    for block_id, _ in BLOCK_ORDER:
        old_body = extract_block_body(updated, block_id)
        if old_body is None:
            continue
        new_body = generated[block_id]
        if old_body.rstrip() != new_body.rstrip():
            changed[block_id] = (old_body, new_body)
            updated = replace_block_body(updated, block_id, new_body)

    if not updated.endswith("\n"):
        updated += "\n"
    return updated, changed


def require_blocks(text: str) -> List[str]:
    missing = []
    for block_id, _ in BLOCK_ORDER:
        if begin_marker(block_id) not in text or end_marker(block_id) not in text:
            missing.append(block_id)
    return missing


def command_init_blocks(args: argparse.Namespace) -> int:
    agents_path = Path(args.agents).resolve()
    if not agents_path.exists():
        print(f"[ERROR] AGENTS file not found: {agents_path}", file=sys.stderr)
        return 2

    original = normalize_text(agents_path.read_text(encoding="utf-8"))
    marker_errors, _, _ = validate_markers(original)
    if marker_errors:
        for error in marker_errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    with_missing, missing = append_missing_blocks(original)
    if not missing:
        print("[OK] All dynamic blocks already exist.")
        return 0

    agents_path.write_text(with_missing, encoding="utf-8")
    print(f"[OK] Added missing blocks: {', '.join(missing)}")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    agents_path = Path(args.agents).resolve()
    root = Path(args.root).resolve()

    if not agents_path.exists():
        print(f"[ERROR] AGENTS file not found: {agents_path}", file=sys.stderr)
        return 2
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}", file=sys.stderr)
        return 2

    original = normalize_text(agents_path.read_text(encoding="utf-8"))
    marker_errors, _, _ = validate_markers(original)
    if marker_errors:
        for error in marker_errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    missing = require_blocks(original)
    if missing:
        print(
            "[ERROR] Missing dynamic blocks. Run init-blocks first: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    stats = collect_repo_stats(root)
    updated, changed = apply_sync_to_text(original, stats)

    if not changed:
        print("[OK] No block changes detected. AGENTS.md is up to date.")
        return 0

    agents_path.write_text(updated, encoding="utf-8")
    print(f"[OK] Synced {len(changed)} block(s): {', '.join(sorted(changed.keys()))}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    agents_path = Path(args.agents).resolve()
    root = Path(args.root).resolve()

    if not agents_path.exists():
        print(f"[ERROR] AGENTS file not found: {agents_path}", file=sys.stderr)
        return 2
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}", file=sys.stderr)
        return 2

    text = normalize_text(agents_path.read_text(encoding="utf-8"))
    errors, _, _ = validate_markers(text)

    missing = require_blocks(text)
    if missing:
        errors.append("Missing blocks: " + ", ".join(missing))

    structure_body = extract_block_body(text, BLOCK_PROJECT_STRUCTURE)
    if structure_body is None:
        errors.append("Project structure block not found.")
    else:
        expected_stats = collect_repo_stats(root)
        saved_count, saved_depth = parse_structure_metadata(structure_body)
        if saved_count is None or saved_depth is None:
            errors.append(
                "Project structure metadata missing required fields: 当前文件数/当前最大深度."
            )
        else:
            if saved_count != expected_stats.file_count or saved_depth != expected_stats.max_depth:
                errors.append(
                    "Project structure stats are stale: "
                    f"saved=({saved_count},{saved_depth}) "
                    f"current=({expected_stats.file_count},{expected_stats.max_depth})."
                )

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("[OK] AGENTS dynamic blocks are valid.")
    return 0


def command_diff(args: argparse.Namespace) -> int:
    agents_path = Path(args.agents).resolve()
    root = Path(args.root).resolve()

    if not agents_path.exists():
        print(f"[ERROR] AGENTS file not found: {agents_path}", file=sys.stderr)
        return 2
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}", file=sys.stderr)
        return 2

    text = normalize_text(agents_path.read_text(encoding="utf-8"))
    errors, _, _ = validate_markers(text)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    missing = require_blocks(text)
    if missing:
        print(
            "[ERROR] Missing dynamic blocks. Run init-blocks first: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    stats = collect_repo_stats(root)
    updated, changed = apply_sync_to_text(text, stats)

    if not changed:
        print("[OK] No differences. AGENTS.md is already synced.")
        return 0

    print("[INFO] Changed blocks:")
    for block_id in sorted(changed.keys()):
        old_body, new_body = changed[block_id]
        before_lines = len(old_body.splitlines())
        after_lines = len(new_body.splitlines())
        print(f"- {block_id}: before_lines={before_lines}, after_lines={after_lines}")

    print("\n[INFO] Unified diff preview:")
    for line in difflib.unified_diff(
        text.splitlines(),
        updated.splitlines(),
        fromfile=str(agents_path),
        tofile=str(agents_path),
        lineterm="",
    ):
        print(line)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AGENTS.md dynamic governance blocks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_sync = subparsers.add_parser("sync", help="Sync all dynamic blocks in AGENTS.md.")
    parser_sync.add_argument("--agents", default="AGENTS.md", help="Path to AGENTS.md")
    parser_sync.add_argument("--root", default=".", help="Repository root for structure scan")
    parser_sync.set_defaults(func=command_sync)

    parser_check = subparsers.add_parser("check", help="Validate markers and structure freshness.")
    parser_check.add_argument("--agents", default="AGENTS.md", help="Path to AGENTS.md")
    parser_check.add_argument("--root", default=".", help="Repository root for structure scan")
    parser_check.set_defaults(func=command_check)

    parser_diff = subparsers.add_parser("diff", help="Preview block changes without writing.")
    parser_diff.add_argument("--agents", default="AGENTS.md", help="Path to AGENTS.md")
    parser_diff.add_argument("--root", default=".", help="Repository root for structure scan")
    parser_diff.set_defaults(func=command_diff)

    parser_init = subparsers.add_parser("init-blocks", help="Append missing dynamic blocks.")
    parser_init.add_argument("--agents", default="AGENTS.md", help="Path to AGENTS.md")
    parser_init.set_defaults(func=command_init_blocks)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
