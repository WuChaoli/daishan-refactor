from rag_stream.config.settings import RAGFlowConfig


def test_get_intent_type_should_parse_string_number_mapping():
    config = RAGFlowConfig(
        api_key="mock",
        base_url="http://mock",
        database_mapping={"db_type2": "2"},
    )

    assert config.get_intent_type("db_type2") == 2


def test_get_intent_type_should_return_minus_one_for_invalid_string_mapping():
    config = RAGFlowConfig(
        api_key="mock",
        base_url="http://mock",
        database_mapping={"db_type2": "type2"},
    )

    assert config.get_intent_type("db_type2") == -1
