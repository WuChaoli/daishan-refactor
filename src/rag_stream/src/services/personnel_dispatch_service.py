"""
PersonnelDispatchService - 人员调度服务
负责处理人员调度相关的业务逻辑
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

from log_decorator import log, logger, logging


@log()
async def handle_personnel_dispatch(
    voice_text: str,
    user_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    处理人员调度请求

    Args:
        voice_text: 语音文本
        user_id: 用户ID

    Returns:
        List[Dict[str, str]]: 人员ID列表，格式如 [{"id":"1111"},{"id":"2222"}]
    """

    try:
        logger.info(f"处理人员调度请求，语音文本: {voice_text}")
        logging.INFO(
            f"人员调度请求接入: voice_len={len(voice_text)}, has_user_id={bool(user_id)}"
        )

        # 获取 Dify clients
        general_client, personnel_client = _get_dify_clients()
        logging.DEBUF("Dify 客户端已就绪: general + personnel")

        # 步骤1: 实体提取
        entities = await _extract_entities(voice_text, general_client)
        logger.info(f"提取到 {len(entities)} 个实体: {entities}")
        logging.INFO(f"实体提取完成: entity_count={len(entities)}")

        if not entities:
            logger.warning("未提取到任何实体，返回空列表")
            return []

        # 步骤2: 循环调用人员调度 client，异步执行
        result_ids = await _call_personnel_dispatch_for_entities(
            entities, personnel_client, user_id
        )

        logger.info(f"成功调用人员调度，返回 {len(result_ids)} 个 ID")
        logging.INFO(f"人员调度完成: resolved_count={len(result_ids)}")
        return result_ids

    except ValueError as e:
        logger.error(f"业务逻辑错误: {e}")
        return []
    except KeyError as e:
        logger.error(f"数据字段缺失: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"处理人员调度请求时发生错误: {e}", exc_info=True)
        return []


def _get_dify_clients() -> tuple:
    """获取Dify客户端实例"""
    from src.utils.dify_client_factory import get_client

    general_client = get_client("GENRAL_CHAT")
    if general_client is None:
        raise ValueError("Dify general_chat client 未配置。请在环境变量中设置 DIFY_CHAT_APIKEY_GENRAL_CHAT")

    try:
        personnel_client = get_client("PERSONNEL_DISPATCHING")
    except ValueError as e:
        raise ValueError(
            "人员调度 client 未配置。"
            "请在环境变量中设置 DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING"
        ) from e

    return general_client, personnel_client


async def _extract_entities(
    voice_text: str,
    general_client
) -> List[str]:
    """
    调用 Dify 进行实体提取

    Args:
        voice_text: 语音文本
        general_client: Dify general_chat client 实例

    Returns:
        List[str]: 提取的实体列表
    """
    from src.utils.prompts import SourceDispatchPrompts

    # 构建实体提取 prompt
    entity_query = SourceDispatchPrompts.get_entity_extraction_prompt(voice_text)
    logger.debug(f"实体提取 prompt: {entity_query}")
    logging.DEBUF(f"实体提取 prompt 构建完成: prompt_len={len(entity_query)}")

    # 调用 Dify 进行实体提取
    entity_response = await asyncio.to_thread(
        general_client.run_chat,
        query=entity_query,
        user="system",
        inputs={},
        conversation_id=""
    )

    # 提取 answer 字段
    entity_answer = entity_response.answer if hasattr(entity_response, 'answer') else str(entity_response)
    logger.debug(f"实体提取响应: {entity_answer}")
    logging.DEBUF(f"实体提取响应长度: answer_len={len(entity_answer)}")

    # 解析实体列表
    entities = _parse_entity_list(entity_answer)
    return entities


def _parse_entity_list(answer: str) -> List[str]:
    """
    解析实体提取响应为字符串列表

    Args:
        answer: AI 返回的响应字符串，预期格式为 ["实体1", "实体2", ...]

    Returns:
        List[str]: 解析后的实体列表
    """
    answer = answer.strip()
    logger.debug(f"实体提取原始响应: {repr(answer[:200])}")

    if not answer:
        logger.warning("实体提取响应为空，返回空列表")
        return []

    # 从文本中提取JSON
    json_str = _extract_json_from_text(answer)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}, 提取的JSON: {repr(json_str[:200])}")
        raise ValueError(f"实体提取响应不是有效的JSON格式: {answer[:100]}")

    if not isinstance(result, list):
        raise ValueError(f"AI 返回的不是列表格式: {answer[:100]}")

    # 确保所有元素都是字符串
    str_list = [str(item) for item in result]
    logger.info(f"成功解析实体列表，返回 {len(str_list)} 个实体")
    return str_list


def _extract_json_from_text(text: str) -> str:
    """
    从文本中提取JSON格式内容

    Args:
        text: 可能包含JSON的文本字符串

    Returns:
        str: 提取并标准化的JSON字符串
    """
    text = text.strip()

    # 处理markdown代码块
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            logger.debug(f"从markdown代码块中提取JSON: {json_str[:100]}")
            return _normalize_json_string(json_str)

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            logger.debug(f"从代码块中提取JSON: {json_str[:100]}")
            return _normalize_json_string(json_str)

    # 尝试找到JSON数组 [...]
    if "[" in text and "]" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        json_str = text[start:end].strip()
        logger.debug(f"提取JSON数组: {json_str[:100]}")
        return _normalize_json_string(json_str)

    # 如果没有找到JSON标记，返回原始文本
    logger.debug("未找到JSON标记，返回原始文本")
    return _normalize_json_string(text)


def _normalize_json_string(json_str: str) -> str:
    """
    标准化JSON字符串，将Python格式转换为JSON格式

    Args:
        json_str: 可能是Python格式或JSON格式的字符串

    Returns:
        str: 标准化的JSON字符串
    """
    import ast

    json_str = json_str.strip()

    # 首先尝试直接解析为JSON
    try:
        parsed = json.loads(json_str)
        logger.debug("字符串已是有效的JSON格式")
        return json_str
    except json.JSONDecodeError:
        logger.debug("不是有效的JSON格式，尝试作为Python格式解析")

    # 尝试作为Python字面量解析（支持单引号）
    try:
        parsed = ast.literal_eval(json_str)
        # 转换为标准JSON格式
        normalized = json.dumps(parsed, ensure_ascii=False)
        logger.debug(f"成功将Python格式转换为JSON格式: {normalized[:100]}")
        return normalized
    except (ValueError, SyntaxError) as e:
        logger.warning(f"无法解析为Python格式: {e}")
        # 返回原始字符串，让调用方处理错误
        return json_str


async def _call_personnel_dispatch_for_entities(
    entities: List[str],
    personnel_client,
    user_id: Optional[str]
) -> List[Dict[str, str]]:
    """
    循环调用人员调度 client，异步执行

    Args:
        entities: 实体名称列表
        personnel_client: Dify personnel_dispatching client 实例
        user_id: 用户ID

    Returns:
        List[Dict[str, str]]: 人员ID列表，格式如 [{"id":"1111"},{"id":"2222"}]
    """
    result_ids = []

    # 创建所有异步任务
    tasks = []
    for entity_name in entities:
        logger.debug(f"准备调用 Dify，实体名称: {entity_name}")
        task = asyncio.to_thread(
            personnel_client.run_chat,
            query=entity_name,
            user=user_id or "anonymous",
            inputs={},
            conversation_id=""
        )
        tasks.append((entity_name, task))

    logging.INFO(f"人员调度并行调用开始: entity_count={len(tasks)}")

    # 并行执行所有任务
    for entity_name, task in tasks:
        try:
            dify_response = await task

            # 提取 answer 字段（默认是全部由数字组成的 str 串，也就是 ID）
            answer = dify_response.answer if hasattr(dify_response, 'answer') else str(dify_response)
            answer = answer.strip()

            if answer:
                # 将 ID 包装成 {"id": "xxx"} 格式
                result_ids.append({"id": answer})
                logger.debug(f"实体 {entity_name} 返回 ID: {answer}")
            else:
                logger.warning(f"实体 {entity_name} 返回空 ID")

        except Exception as e:
            logger.error(f"调用人员调度 client 失败，实体: {entity_name}, 错误: {e}", exc_info=True)
            continue

    logging.INFO(f"人员调度并行调用完成: resolved_count={len(result_ids)}")
    return result_ids
