from rag_stream.services.fixed_question_flow_service import (
    normalize_fixed_question_candidates,
)


def test_normalize_fixed_question_candidates_should_support_plain_question_chunks():
    candidates = normalize_fixed_question_candidates(
        [
            {
                "question": "园区地址在哪\r",
                "similarity": 0.88,
            },
            {
                "question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
                "similarity": 0.77,
            },
        ]
    )

    assert candidates == [
        {
            "question": "园区地址在哪",
            "raw_question": "园区地址在哪",
            "similarity": 0.88,
        },
        {
            "question": "园区负责人是谁",
            "raw_question": "Question: 园区负责人是谁\tAnswer: 园区负责人信息",
            "similarity": 0.77,
        },
    ]
