"""
猜你想问服务模块

根据意图识别结果，返回推荐问题列表
"""
import json
import re
from typing import Dict, List, Any
from rag_stream.utils.log_manager_import import entry_trace, trace, marker

from rag_stream.utils.dify_client_factory import get_client
from rag_stream.utils.prompts import GuessQuestionsPrompts


# 类别1的固定问题模板
TYPE1_FIXED_QUESTIONS = [
    "介绍一下园区",
    "介绍一下园区总体企业情况",
    "介绍一下企业安全态势"
]


@entry_trace("guess-questions")
async def handle_guess_questions(question: str, intent_service) -> List[Dict[str, str]]:
    """
    处理猜你想问请求的主函数

    Args:
        question: 用户问题
        intent_service: 意图识别服务实例

    Returns:
        推荐问题列表
    """
    try:
        # 输入验证
        question = question.strip()
        if not question:
            return []

        if len(question) > 1000:
            return []

        # 调用意图识别服务
        intent_result = await intent_service.process_query(question, user_id=None)

        # 将IntentResult转换为字典
        intent_dict = _convert_to_dict(intent_result)

        # 根据意图类型选择处理函数
        questions = await _process_by_type(intent_dict, question)

        return questions

    except Exception as e:
        marker("猜你想问服务异常", {"error": str(e)}, level="ERROR")
        return []


def _convert_to_dict(intent_result: Any) -> Dict[str, Any]:
    """
    将IntentResult转换为字典

    Args:
        intent_result: 意图识别结果

    Returns:
        字典格式的意图结果
    """
    if hasattr(intent_result, 'model_dump'):
        return intent_result.model_dump()
    elif hasattr(intent_result, 'dict'):
        return intent_result.dict()
    else:
        return intent_result


async def _process_by_type(intent_dict: Dict[str, Any], original_question: str) -> List[Dict[str, str]]:
    """
    根据意图类型选择处理函数

    Args:
        intent_dict: 字典格式的意图结果

    Returns:
        推荐问题列表
    """
    intent_type = intent_dict.get("type", 0)

    if intent_type == 1:
        return process_type1(intent_dict)
    elif intent_type in [2,3]:
        questions = process_type2(intent_dict)
        if questions:
            return questions
        return await _generate_type2_fallback_questions(original_question)
    else:
        return process_other_types(intent_dict)


def _parse_question_field(question_text: str) -> str:
    """
    解析question字段，提取纯文本问题

    支持格式：
    - "Question: xxx\tAnswer: xxx" -> "xxx"
    - "纯文本问题" -> "纯文本问题"

    Args:
        question_text: 原始question字段

    Returns:
        解析后的纯文本问题
    """
    if not question_text:
        return ""

    # 检查是否包含 "Question:" 和 "\tAnswer:" 格式
    if "Question:" in question_text and "\tAnswer:" in question_text:
        # 提取 "Question:" 和 "\tAnswer:" 之间的文本
        start = question_text.find("Question:") + len("Question:")
        end = question_text.find("\tAnswer:")
        return question_text[start:end].strip()

    # 如果不是特殊格式，直接返回原文本
    return question_text.strip()


def process_type1(intent_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    处理类别1（type=1）的意图结果

    返回固定的3个问题

    Args:
        intent_result: 意图识别结果

    Returns:
        包含3个固定问题的列表
    """
    return [
        {"question": question}
        for question in TYPE1_FIXED_QUESTIONS
    ]


def process_type2(intent_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    处理类别2（type=2）的意图结果

    提取results[1:4]的question字段（第2-4个结果）

    Args:
        intent_result: 意图识别结果

    Returns:
        提取的问题列表（最多3个）
    """
    results = intent_result.get("results", [])
    if not isinstance(results, list):
        return []

    # 提取第2-4个结果（索引1-3）
    extracted_results = results[1:4]

    # 提取并解析question字段
    return [
        {"question": _parse_question_field(item.get("question", ""))}
        for item in extracted_results
        if isinstance(item, dict) and "question" in item
    ]


def _parse_llm_generated_questions(answer_text: str) -> List[str]:
    text = (answer_text or "").strip()
    if not text:
        return []

    candidates: List[str] = []

    # 优先尝试 JSON 数组
    json_text = text
    if "[" in text and "]" in text:
        json_text = text[text.find("[") : text.rfind("]") + 1]

    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str):
                    value = item.strip()
                elif isinstance(item, dict):
                    value = str(item.get("question") or item.get("guess_your_question") or "").strip()
                else:
                    value = str(item).strip()

                if value:
                    candidates.append(value)
    except json.JSONDecodeError:
        # 兼容普通文本：按行拆分并去除编号
        for line in text.splitlines():
            normalized = re.sub(r"^\s*(?:[-*]|\d+[\.\)\、\:]?)\s*", "", line).strip()
            if normalized:
                candidates.append(normalized)

    deduplicated: List[str] = []
    seen = set()
    for item in candidates:
        if item not in seen:
            seen.add(item)
            deduplicated.append(item)

    return deduplicated[:3]


async def _generate_type2_fallback_questions(original_question: str) -> List[Dict[str, str]]:
    try:
        general_client = get_client("GENRAL_CHAT")
    except Exception as error:
        marker("获取GENRAL_CHAT client失败", {"error": str(error)}, level="ERROR")
        return []

    prompt = GuessQuestionsPrompts.get_type2_fallback_prompt(original_question)

    try:
        response = general_client.run_chat(
            query=prompt,
            user="system",
            inputs={},
            conversation_id="",
        )
    except Exception as error:
        marker("调用GENRAL_CHAT生成猜你想问失败", {"error": str(error)}, level="ERROR")
        return []

    answer_text = response.answer if hasattr(response, "answer") else str(response)
    generated = _parse_llm_generated_questions(answer_text)

    return [{"question": item} for item in generated]


def process_other_types(intent_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    处理其他类别（type=0或其他）的意图结果

    返回空列表

    Args:
        intent_result: 意图识别结果

    Returns:
        空列表
    """
    return []
