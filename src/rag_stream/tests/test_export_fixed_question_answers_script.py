from __future__ import annotations

import importlib.util
from pathlib import Path

from openpyxl import load_workbook


def _load_script_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "export_fixed_question_answers.py"
    spec = importlib.util.spec_from_file_location(
        "export_fixed_question_answers", script_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_questions_from_mapping_file():
    module = _load_script_module()
    repo_root = Path(__file__).resolve().parents[3]
    mapping_path = (
        repo_root
        / "src"
        / "rag_stream"
        / "src"
        / "services"
        / "data"
        / "fixed_question_prompt_mapping.json"
    )

    exporter = module.FixedQuestionAnswerExporter(mapping_path=mapping_path)

    questions = exporter.load_questions()

    assert questions
    assert "园区地址在哪" in questions
    assert len(questions) == len(set(questions))


def test_parse_sse_answer_from_incremental_answer_events():
    module = _load_script_module()
    exporter = module.FixedQuestionAnswerExporter(mapping_path=Path("unused.json"))

    answer = exporter.parse_sse_answer(
        [
            'data: {"code": 0, "data": {"answer": "岱山", "flag": 1, "end": 0}}',
            'data: {"code": 0, "data": {"answer": "经开区", "flag": 1, "end": 0}}',
            'data: {"code": 0, "data": {"answer": "", "flag": 0, "end": 1}}',
            'data: [DONE]',
        ]
    )

    assert answer == "岱山经开区"


def test_load_script_config_and_build_exporter(tmp_path: Path):
    module = _load_script_module()
    config_path = tmp_path / "fixed_question_test_config.yaml"
    config_path.write_text(
        """
base_url: http://10.0.0.8:11028
log_source_path: /tmp/rag_stream.log
request_timeout: 90
question_limit: 3
""".strip(),
        encoding="utf-8",
    )

    config = module.load_script_config(config_path)
    exporter = module.build_exporter_from_config(config)

    assert config["base_url"] == "http://10.0.0.8:11028"
    assert exporter.base_url == "http://10.0.0.8:11028"
    assert exporter.log_source_path == Path("/tmp/rag_stream.log")
    assert exporter.request_timeout == 90.0
    assert exporter.question_limit == 3
    assert exporter.manage_server is False


def test_capture_run_logs_should_only_write_new_content(tmp_path: Path):
    module = _load_script_module()
    source_log_path = tmp_path / "service.log"
    source_log_path.write_text("old line\n", encoding="utf-8")

    exporter = module.FixedQuestionAnswerExporter(
        mapping_path=Path("unused.json"),
        output_path=tmp_path / "fixed_question_answers.xlsx",
        log_source_path=source_log_path,
    )

    exporter.mark_log_start()
    source_log_path.write_text("old line\nnew line 1\nnew line 2\n", encoding="utf-8")

    captured_log_path = exporter.capture_run_logs()

    assert captured_log_path == exporter.captured_log_path
    assert captured_log_path.read_text(encoding="utf-8") == "new line 1\nnew line 2\n"


def test_write_results_to_excel(tmp_path: Path):
    module = _load_script_module()
    output_path = tmp_path / "fixed_question_answers.xlsx"
    exporter = module.FixedQuestionAnswerExporter(
        mapping_path=Path("unused.json"),
        output_path=output_path,
    )

    exporter.write_results(
        [
            {"question": "园区地址在哪", "answer": "位于浙江省舟山市岱山县"},
            {"question": "园区负责人是谁", "answer": "张三"},
        ]
    )

    workbook = load_workbook(output_path)
    worksheet = workbook.active

    assert worksheet.title == "answers"
    assert worksheet["A1"].value == "question"
    assert worksheet["B1"].value == "answer"
    assert worksheet["A2"].value == "园区地址在哪"
    assert worksheet["B2"].value == "位于浙江省舟山市岱山县"
    assert worksheet["A3"].value == "园区负责人是谁"
    assert worksheet["B3"].value == "张三"
