from rag_stream.utils.prompts import GuessQuestionsPrompts


def test_type2_fallback_prompt_should_emphasize_guess_not_answer():
    prompt = GuessQuestionsPrompts.get_type2_fallback_prompt("我碰到了氢氟酸怎么办？")

    assert "不是回答器" in prompt
    assert "用户下一步可能还会问的3个问题" in prompt
    assert "严格禁止" in prompt
    assert "输出格式（必须完全一致为JSON数组）" in prompt
    assert "我碰到了氢氟酸怎么办？" in prompt
