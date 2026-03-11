from __future__ import annotations

import json
from pathlib import Path


def test_fixed_question_prompt_mapping_should_cover_all_daishan_fixed_questions():
    project_src_dir = Path(__file__).resolve().parents[2]
    source_path = (
        project_src_dir
        / "DaiShanSQL"
        / "DaiShanSQL"
        / "SQL"
        / "岱山固定查询.jsonl"
    )
    mapping_path = (
        project_src_dir
        / "rag_stream"
        / "src"
        / "services"
        / "data"
        / "fixed_question_prompt_mapping.json"
    )

    source_questions = {
        json.loads(line)["question"].strip()
        for line in source_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    mapping_questions = set(
        json.loads(mapping_path.read_text(encoding="utf-8")).keys()
    )

    missing_questions = sorted(source_questions - mapping_questions)

    assert not missing_questions, (
        "fixed_question_prompt_mapping.json 缺少以下固定问题映射: "
        f"{missing_questions}"
    )


def test_fixed_question_prompt_mapping_should_not_have_empty_template_content():
    mapping_path = (
        Path(__file__).resolve().parents[2]
        / "rag_stream"
        / "src"
        / "services"
        / "data"
        / "fixed_question_prompt_mapping.json"
    )

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    invalid_questions: list[str] = []

    for question, prompt in mapping.items():
        if "<回答模板>" not in prompt or "</回答模板>" not in prompt:
            continue

        inner = prompt.split("<回答模板>", 1)[1].split("</回答模板>", 1)[0].strip()
        if not inner or "[]" in inner:
            invalid_questions.append(question)

    assert not invalid_questions, (
        "fixed_question_prompt_mapping.json 存在回答模板为空或占位符缺失的问题: "
        f"{invalid_questions}"
    )
