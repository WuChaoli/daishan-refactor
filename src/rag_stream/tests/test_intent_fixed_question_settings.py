from __future__ import annotations

from pathlib import Path

from rag_stream.config.settings import Settings


def test_intent_fixed_question_settings_should_load_from_yaml(tmp_path: Path):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
intent:
  fixed_question_similarity_threshold: 0.61
  fixed_question_direct_threshold: 0.72
  fixed_question_top_k: 4
  fixed_question_table_name: "岱山-指令集-固定问题"
""".strip(),
        encoding="utf-8",
    )

    settings = Settings.load_from_yaml(yaml_path)

    assert settings.intent.fixed_question_similarity_threshold == 0.61
    assert settings.intent.fixed_question_direct_threshold == 0.72
    assert settings.intent.fixed_question_top_k == 4
    assert settings.intent.fixed_question_table_name == "岱山-指令集-固定问题"


def test_intent_fixed_question_settings_should_support_env_override(
    tmp_path: Path, monkeypatch
):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
intent:
  fixed_question_similarity_threshold: 0.6
  fixed_question_direct_threshold: 0.7
  fixed_question_top_k: 5
  fixed_question_table_name: "岱山-指令集-固定问题"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("INTENT_FIXED_QUESTION_SIMILARITY_THRESHOLD", "0.63")
    monkeypatch.setenv("INTENT_FIXED_QUESTION_DIRECT_THRESHOLD", "0.75")
    monkeypatch.setenv("INTENT_FIXED_QUESTION_TOP_K", "3")
    monkeypatch.setenv("INTENT_FIXED_QUESTION_TABLE_NAME", "custom-fixed-table")

    settings = Settings.load_from_yaml_with_env_override(yaml_path)

    assert settings.intent.fixed_question_similarity_threshold == 0.63
    assert settings.intent.fixed_question_direct_threshold == 0.75
    assert settings.intent.fixed_question_top_k == 3
    assert settings.intent.fixed_question_table_name == "custom-fixed-table"
