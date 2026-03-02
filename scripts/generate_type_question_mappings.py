#!/usr/bin/env python3
"""Generate type1/type2 question mappings from Excel files."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "src" / "rag_stream" / "src" / "services" / "data"


@dataclass
class BuildStats:
    scanned: int = 0
    processed: int = 0
    skipped_empty: int = 0
    conflicts: int = 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate type1/type2 question mappings from Excel files "
            "using fixed_question_prompt_mapping.json style"
        ),
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing source Excel files.",
    )
    parser.add_argument(
        "--type1-excel",
        type=str,
        default="岱山-指令集.xlsx",
        help="Type1 source Excel filename in data-dir.",
    )
    parser.add_argument(
        "--type2-excel",
        type=str,
        default="岱山-数据库问题.xlsx",
        help="Type2 source Excel filename in data-dir.",
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default="Sheet1",
        help="Excel sheet name to read.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Output directory for mapping and report files.",
    )
    return parser.parse_args()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _build_mapping_from_excel(excel_path: Path, sheet_name: str) -> tuple[dict[str, str], list[dict[str, Any]], BuildStats]:
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    data_frame = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    mapping: dict[str, str] = {}
    conflicts: list[dict[str, Any]] = []
    stats = BuildStats()

    for index, row in data_frame.iterrows():
        stats.scanned += 1

        question = str(row.iloc[0] if len(row) > 0 else "").strip()
        prompt = str(row.iloc[1] if len(row) > 1 else "").strip()

        if not question or not prompt:
            stats.skipped_empty += 1
            continue

        existing_prompt = mapping.get(question)
        if existing_prompt is not None:
            if existing_prompt != prompt:
                stats.conflicts += 1
                conflicts.append(
                    {
                        "question": question,
                        "kept_prompt": existing_prompt,
                        "discarded_prompt": prompt,
                        "source_row": int(index) + 1,
                    }
                )
            continue

        mapping[question] = prompt
        stats.processed += 1

    return mapping, conflicts, stats


def _load_existing_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        return {}

    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_data_dir(data_dir: Path) -> Path:
    return data_dir


def _get_worktree_fallback_data_dir() -> Path | None:
    if ".worktrees" not in PROJECT_ROOT.parts:
        return None

    try:
        worktrees_index = PROJECT_ROOT.parts.index(".worktrees")
        main_repo_root = Path(*PROJECT_ROOT.parts[:worktrees_index])
        fallback = main_repo_root / "src" / "rag_stream" / "src" / "services" / "data"
        return fallback if fallback.exists() else None
    except Exception:
        return None


def _resolve_excel_path(data_dir: Path, file_name: str) -> Path:
    primary_path = data_dir / file_name
    if primary_path.exists():
        return primary_path

    fallback_dir = _get_worktree_fallback_data_dir()
    if fallback_dir is not None:
        fallback_path = fallback_dir / file_name
        if fallback_path.exists():
            return fallback_path

    return primary_path


def main() -> int:
    args = _parse_args()

    data_dir = _resolve_data_dir(args.data_dir)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    type1_excel_path = _resolve_excel_path(data_dir, args.type1_excel)
    type2_excel_path = _resolve_excel_path(data_dir, args.type2_excel)

    type1_mapping, type1_conflicts, type1_stats = _build_mapping_from_excel(
        type1_excel_path,
        args.sheet,
    )
    type2_mapping, type2_conflicts, type2_stats = _build_mapping_from_excel(
        type2_excel_path,
        args.sheet,
    )

    type1_mapping_path = output_dir / "type1_question_mapping.json"
    type2_mapping_path = output_dir / "type2_question_mapping.json"
    type1_conflict_path = output_dir / "type1_question_mapping_conflicts.json"
    type2_conflict_path = output_dir / "type2_question_mapping_conflicts.json"
    summary_path = output_dir / "question_mapping_generation_summary.json"

    _write_json(type1_mapping_path, type1_mapping)
    _write_json(type2_mapping_path, type2_mapping)
    _write_json(type1_conflict_path, type1_conflicts)
    _write_json(type2_conflict_path, type2_conflicts)

    summary = _load_existing_summary(summary_path)
    summary["type1"] = {
        "scanned": type1_stats.scanned,
        "processed": type1_stats.processed,
        "skipped_empty": type1_stats.skipped_empty,
        "skipped_error": 0,
        "conflicts": type1_stats.conflicts,
        "source": str(type1_excel_path),
        "format": "question_to_prompt",
    }
    summary["type2"] = {
        "scanned": type2_stats.scanned,
        "processed": type2_stats.processed,
        "skipped_empty": type2_stats.skipped_empty,
        "skipped_error": 0,
        "conflicts": type2_stats.conflicts,
        "source": str(type2_excel_path),
        "format": "question_to_prompt",
    }

    _write_json(summary_path, summary)

    print("Generated mapping files:")
    print(f"- {type1_mapping_path}")
    print(f"- {type2_mapping_path}")
    print(f"- {type1_conflict_path}")
    print(f"- {type2_conflict_path}")
    print(f"- {summary_path}")
    print("Stats:")
    print(f"- type1: {vars(type1_stats)}")
    print(f"- type2: {vars(type2_stats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
