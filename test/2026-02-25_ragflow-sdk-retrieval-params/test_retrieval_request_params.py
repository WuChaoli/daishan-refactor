import pytest

from src.ragflow_sdk.core.client import RAGFlowClient
from src.ragflow_sdk.models.chunks import RetrievalRequest


def test_retrieval_request_should_include_new_api_fields_in_payload():
    request = RetrievalRequest(
        question="what is ragflow",
        dataset_ids=["ds_1"],
        document_ids=["doc_1"],
        page=2,
        page_size=20,
        similarity_threshold=0.45,
        vector_similarity_weight=0.8,
        top_k=256,
        rerank_id="rerank_model_1",
        keyword=True,
        highlight=True,
        cross_languages=["zh", "en"],
        metadata_condition={
            "logic": "and",
            "conditions": [
                {"name": "author", "comparison_operator": "=", "value": "Toby"}
            ],
        },
        use_kg=True,
        toc_enhance=True,
    )

    payload = request.model_dump()

    assert payload["vector_similarity_weight"] == 0.8
    assert payload["document_ids"] == ["doc_1"]
    assert payload["rerank_id"] == "rerank_model_1"
    assert payload["keyword"] is True
    assert payload["highlight"] is True
    assert payload["cross_languages"] == ["zh", "en"]
    assert payload["metadata_condition"]["logic"] == "and"
    assert payload["use_kg"] is True
    assert payload["toc_enhance"] is True


def test_retrieval_request_should_allow_document_ids_without_dataset_ids():
    request = RetrievalRequest(question="what is ragflow", document_ids=["doc_1"])
    payload = request.model_dump()
    assert payload["document_ids"] == ["doc_1"]
    assert payload["dataset_ids"] is None


def test_retrieval_request_should_require_dataset_ids_or_document_ids():
    with pytest.raises(ValueError, match="dataset_ids 和 document_ids 至少需要提供一个"):
        RetrievalRequest(question="what is ragflow")


def test_retrieve_should_not_send_none_fields():
    client = RAGFlowClient(api_url="http://localhost:80/v1", api_key="test-key")

    client.http.post = lambda endpoint, json: {"endpoint": endpoint, "json": json}
    client.parser.parse_list = lambda response, _: response

    response = client.retrieve(
        RetrievalRequest(question="what is ragflow", document_ids=["doc_1"])
    )

    assert response["endpoint"] == "/retrieval"
    assert "dataset_ids" not in response["json"]
    assert "document_ids" in response["json"]
    assert "rerank_id" not in response["json"]
