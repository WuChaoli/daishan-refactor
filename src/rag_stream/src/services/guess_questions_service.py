"""
猜你想问服务模块

根据意图识别结果，返回推荐问题列表
"""
from typing import Dict, List, Any
from log_decorator import logger


# 类别1的固定问题模板
TYPE1_FIXED_QUESTIONS = [
    "介绍一下园区",
    "介绍一下园区总体企业情况",
    "介绍一下企业安全态势"
]


async def handle_guess_questions(question: str, intent_service) -> Dict[str, Any]:
    """
    处理猜你想问请求的主函数

    Args:
        question: 用户问题
        intent_service: 意图识别服务实例

    Returns:
        包含推荐问题列表的响应字典
    """
    try:
        # 输入验证
        question = question.strip()
        if not question:
            return {
                "code": 1,
                "message": "问题不能为空",
                "data": []
            }

        if len(question) > 1000:
            return {
                "code": 1,
                "message": "问题长度不能超过1000字符",
                "data": []
            }

        # 调用意图识别服务
        intent_result = await intent_service.process_query(question, user_id=None)

        # 将IntentResult转换为字典
        intent_dict = _convert_to_dict(intent_result)

        # 根据意图类型选择处理函数
        questions = _process_by_type(intent_dict)

        return {
            "code": 0,
            "message": "成功",
            "data": questions
        }

    except Exception as e:
        logger.error(f"猜你想问服务异常: {str(e)}", exc_info=True)
        return {
            "code": 1,
            "message": "意图识别服务暂时不可用",
            "data": []
        }


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


def _process_by_type(intent_dict: Dict[str, Any]) -> List[Dict[str, str]]:
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
    elif intent_type == 2:
        return process_type2(intent_dict)
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
        {"guess_your_question": question}
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

    # 提取第2-4个结果（索引1-3）
    extracted_results = results[1:4]

    # 提取并解析question字段
    return [
        {"guess_your_question": _parse_question_field(item.get("question", ""))}
        for item in extracted_results
        if isinstance(item, dict) and "question" in item
    ]


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
