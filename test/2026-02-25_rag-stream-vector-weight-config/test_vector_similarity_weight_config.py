from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_STREAM_ROOT = PROJECT_ROOT / "src" / "rag_stream"
SRC_ROOT = PROJECT_ROOT / "src"
for _path in (RAG_STREAM_ROOT, SRC_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.config.settings import IntentConfig, RAGFlowConfig
from src.utils import ragflow_client as ragflow_client_module


class _FakeSDKClient:
    def __init__(self, *args, **kwargs):
        self.last_retrieval = None

    def list_datasets(self, page=1, page_size=100):
        return {
            "items": [SimpleNamespace(id="dataset_1", name="db_main")],
            "total": 1,
        }

    def retrieve(self, retrieval):
        self.last_retrieval = retrieval
        return []


@pytest.mark.parametrize(
    ("intent_weight", "expected_weight"),
    [
        (None, 0.7),  # 继承 ragflow 基础配置
        (0.4, 0.4),  # intent 覆盖
    ],
)
def test_ragflow_client_should_apply_effective_vector_weight(
    monkeypatch, intent_weight, expected_weight
):
    monkeypatch.setattr(ragflow_client_module, "RAGFlowClient", _FakeSDKClient)
    monkeypatch.setattr(ragflow_client_module, "marker", lambda *args, **kwargs: None)

    ragflow_cfg = RAGFlowConfig(
        api_key="test",
        base_url="http://localhost:8081/api/v1",
        timeout=30,
        max_retries=1,
        vector_similarity_weight=0.7,
        database_mapping={"db_main": 1},
    )
    intent_cfg = IntentConfig(
        similarity_threshold=0.5,
        top_k_per_database=5,
        vector_similarity_weight=intent_weight,
        default_type=0,
    )

    client = ragflow_client_module.RagflowClient(ragflow_cfg, intent_cfg)
    request = client._build_retrieval_request("园区开停车", "dataset_1")
    assert request.vector_similarity_weight == expected_weight


def test_vector_similarity_weight_should_validate_range():
    with pytest.raises(ValueError, match="vector_similarity_weight 必须在 0-1 之间"):
        RAGFlowConfig(vector_similarity_weight=1.2)

    with pytest.raises(
        ValueError, match="intent.vector_similarity_weight 必须在 0-1 之间"
    ):
        IntentConfig(vector_similarity_weight=-0.1)
