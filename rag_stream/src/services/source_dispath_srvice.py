"""
SourceDispatchService - 资源调度服务
负责处理资源调度相关的业务逻辑
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.models.schemas import SourceDispatchRequest, AccidentEventData
from src.models.emergency_entities import (
    EmergencySupply,
    RescueTeam,
    EmergencyExpert,
    FireFightingFacility,
    Shelter,
    MedicalInstitution,
    RescueOrganization,
    ProtectionTarget
)
from src.services.log_manager import LogManager
from src.services.prompts import SourceDispatchPrompts
from src.config.settings import settings
from src.utils.function_tracer import trace_function
from DaiShanSQL import Server

# 加载sourceType映射配置
MAPPING_FILE = Path(__file__).parent / "source_type_mapping.json"
with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    SOURCE_TYPE_MAPPING = json.load(f)


@trace_function
async def handle_source_dispatch(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> List[Dict[str, str]]:
    """
    处理资源调度请求

    Args:
        request: 资源调度请求对象，包含事故ID、资源类型和语音文本
        log_manager: 日志管理器实例

    Returns:
        List[Dict[str, str]]: 资源列表，每个资源包含id等字段
    """
    logger = log_manager.get_function_logger("source_dispatch")

    try:
        accident_id = _validate_and_extract_accident_id(request)
        logger.info(f"处理资源调度请求，事故ID: {accident_id}, 资源类型: {request.sourceType}")

        sql = _build_accident_query_sql(accident_id)
        logger.debug(f"执行 SQL 查询: {sql}")

        query_result = _query_accident_from_database(sql, logger)
        accident_data = _parse_accident_query_result(query_result, accident_id)
        logger.info(f"成功获取事故数据: {accident_data.accident_name}")

        general_client, solid_client = _get_dify_clients(logger)

        intent_query, accident_type_query, entity_query = _build_parallel_dify_queries(request, accident_data)
        logger.debug("准备并行调用 Dify: 意图分类 + 事故类型识别 + 实体提取")

        intent_response, accident_type_response, entity_response = await _call_dify_parallel_analysis(
            general_client, intent_query, accident_type_query, entity_query
        )
        logger.info("成功并行调用 Dify: 意图分类 + 事故类型识别 + 实体提取")

        intent, business_area, entities = _extract_analysis_results(
            intent_response, accident_type_response, entity_response, logger
        )

        result = await _dispatch_by_intent(
            intent, request, log_manager, solid_client, entities,
            accident_data, business_area, general_client, logger
        )

        return result

    except ValueError as e:
        logger.error(f"业务逻辑错误: {e}")
        return []
    except KeyError as e:
        logger.error(f"数据字段缺失: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"处理资源调度请求时发生错误: {e}", exc_info=True)
        return []


def _parse_ai_response_to_list(answer: str, logger) -> List[Dict[str, Any]]:
    """
    解析 AI 响应为列表格式

    Args:
        answer: AI 返回的响应字符串
        logger: 日志记录器

    Returns:
        List[Dict[str, Any]]: 解析后的列表

    Raises:
        ValueError: 如果响应不是有效的 JSON 列表格式
    """
    answer = answer.strip()
    logger.debug(f"AI响应原始内容: {repr(answer[:200])}")

    if not answer:
        logger.warning("AI响应为空，返回空列表")
        return []

    # 从文本中提取JSON
    json_str = _extract_json_from_text(answer, logger)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}, 提取的JSON: {repr(json_str[:200])}")
        raise ValueError(f"AI响应不是有效的JSON格式: {answer[:100]}")

    if not isinstance(result, list):
        raise ValueError(f"AI 返回的不是列表格式: {answer[:100]}")

    logger.info(f"成功解析 JSON，返回 {len(result)} 个项目")
    return result


def _extract_json_from_text(text: str, logger) -> str:
    """
    从文本中提取JSON格式内容，并确保格式正确

    Args:
        text: 可能包含JSON的文本字符串
        logger: 日志记录器

    Returns:
        str: 提取并标准化的JSON字符串

    Raises:
        ValueError: 如果无法提取有效的JSON
    """
    text = text.strip()

    # 处理markdown代码块
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            logger.debug(f"从markdown代码块中提取JSON: {json_str[:100]}")
            return _normalize_json_string(json_str, logger)

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            logger.debug(f"从代码块中提取JSON: {json_str[:100]}")
            return _normalize_json_string(json_str, logger)

    # 尝试找到JSON数组 [...]
    if "[" in text and "]" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        json_str = text[start:end].strip()
        logger.debug(f"提取JSON数组: {json_str[:100]}")
        return _normalize_json_string(json_str, logger)

    # 尝试找到JSON对象 {...}
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end].strip()
        logger.debug(f"提取JSON对象: {json_str[:100]}")
        return _normalize_json_string(json_str, logger)

    # 如果没有找到JSON标记，返回原始文本
    logger.debug("未找到JSON标记，返回原始文本")
    return _normalize_json_string(text, logger)


def _normalize_json_string(json_str: str, logger) -> str:
    """
    标准化JSON字符串，将Python格式转换为JSON格式

    Args:
        json_str: 可能是Python格式或JSON格式的字符串
        logger: 日志记录器

    Returns:
        str: 标准化的JSON字符串

    Raises:
        ValueError: 如果无法解析为有效格式
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


def _parse_entity_list(answer: str, logger) -> List[str]:
    """
    解析实体提取响应为字符串列表

    Args:
        answer: AI 返回的响应字符串，预期格式为 ["实体1", "实体2", ...]
        logger: 日志记录器

    Returns:
        List[str]: 解析后的实体列表

    Raises:
        ValueError: 如果响应不是有效的 JSON 列表格式
    """
    # 去除首尾空格
    answer = answer.strip()
    logger.debug(f"实体提取原始响应: {repr(answer[:200])}")

    # 处理空响应
    if not answer:
        logger.warning("实体提取响应为空，返回空列表")
        return []

    # 从文本中提取JSON
    json_str = _extract_json_from_text(answer, logger)

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


def _validate_and_extract_accident_id(request: SourceDispatchRequest) -> int:
    """验证并提取事故ID"""
    if not request.accidentId:
        raise ValueError("事故ID不能为空")

    try:
        return int(request.accidentId)
    except ValueError:
        raise ValueError(f"事故ID格式错误: {request.accidentId}")


def _build_accident_query_sql(accident_id: int) -> str:
    """构建事故查询SQL语句"""
    return f"""
    SELECT ACCIDENT_NAME, TO_CHAR(COORDINATE) AS COORDINATE, HAZARDOUS_CHEMICALS, ACCIDENT_OVERVIEW
    FROM IPARK_AE_ACCIDENT_EVENT
    WHERE ID = {accident_id}
    """


def _query_accident_from_database(sql: str, logger) -> Any:
    """查询事故数据"""
    server = Server()
    query_result = server.QueryBySQL(sql)
    logger.debug(f"数据库查询结果: {query_result}")
    logger.debug(f"查询结果类型: {type(query_result)}")
    return query_result


def _parse_accident_query_result(query_result: Any, accident_id: int) -> AccidentEventData:
    """解析查询结果并创建事故实体"""
    if isinstance(query_result, dict):
        if 'data' in query_result:
            data_list = query_result['data']
        elif 'result' in query_result:
            data_list = query_result['result']
        else:
            data_list = [query_result]
    elif isinstance(query_result, list):
        data_list = query_result
    else:
        data_list = []

    if not data_list or len(data_list) == 0:
        raise ValueError(f"未找到事故ID为 {accident_id} 的数据")

    row = data_list[0]
    return AccidentEventData.from_db_row(
        accident_name=row.get("ACCIDENT_NAME"),
        coordinate=row.get("COORDINATE"),
        hazardous_chemicals=row.get("HAZARDOUS_CHEMICALS"),
        accident_overview=row.get("ACCIDENT_OVERVIEW")
    )


def _get_dify_clients(logger) -> tuple:
    """获取Dify客户端实例"""
    from src.services.dify_client_factory import get_client

    general_client = get_client("GENRAL_CHAT")
    if general_client is None:
        raise ValueError("Dify general_chat client 未配置。请在环境变量中设置 DIFY_CHAT_APIKEY_GENRAL_CHAT")

    try:
        solid_client = get_client("SOLID_RESOURCE_INSTRUCTION")
    except ValueError as e:
        logger.warning(f"获取 Dify solid_resource_instruction client 失败: {e}")
        solid_client = None

    return general_client, solid_client


def _build_parallel_dify_queries(request: SourceDispatchRequest, accident_data: AccidentEventData) -> tuple:
    """构建三个并行Dify查询文本"""
    intent_query = SourceDispatchPrompts.get_intent_classification_prompt(request.voiceText)
    accident_type_query = SourceDispatchPrompts.get_accident_type_classification_prompt(accident_data)
    entity_query = SourceDispatchPrompts.get_entity_extraction_prompt(request.voiceText)
    return intent_query, accident_type_query, entity_query


async def _call_dify_parallel_analysis(
    general_client,
    intent_query: str,
    accident_type_query: str,
    entity_query: str
) -> tuple:
    """并行调用Dify进行意图分类、事故类型识别和实体提取"""
    return await asyncio.gather(
        asyncio.to_thread(
            general_client.run_chat,
            query=intent_query,
            user="system",
            inputs={},
            conversation_id=""
        ),
        asyncio.to_thread(
            general_client.run_chat,
            query=accident_type_query,
            user="system",
            inputs={},
            conversation_id=""
        ),
        asyncio.to_thread(
            general_client.run_chat,
            query=entity_query,
            user="system",
            inputs={},
            conversation_id=""
        )
    )


def _extract_analysis_results(
    intent_response,
    accident_type_response,
    entity_response,
    logger
) -> tuple:
    """提取意图、事故类型和实体列表"""
    intent_answer = intent_response.answer if hasattr(intent_response, 'answer') else str(intent_response)
    if not intent_answer:
        raise ValueError("意图分类响应为空")
    logger.debug(f"意图分类响应: {intent_answer}")

    business_area = accident_type_response.answer if hasattr(accident_type_response, 'answer') else str(accident_type_response)
    business_area = business_area.strip()
    logger.info(f"获取到事故类型: {business_area}")

    entity_answer = entity_response.answer if hasattr(entity_response, 'answer') else str(entity_response)
    entities = _parse_entity_list(entity_answer, logger)
    logger.info(f"提取到 {len(entities)} 个实体: {entities}")

    return intent_answer, business_area, entities


async def _dispatch_by_intent(
    intent: str,
    request: SourceDispatchRequest,
    log_manager: LogManager,
    solid_client,
    entities: List[str],
    accident_data: AccidentEventData,
    business_area: str,
    general_client,
    logger
) -> Dict[str, Any]:
    """根据意图分类结果分发处理"""
    if intent.strip().lower() == "resource":
        logger.info("意图分类为 'resource'，调用 get_solid_resource_instruction")
        return await _get_solid_resource_instruction(
            request,
            log_manager,
            solid_client,
            entities
        )
    else:
        logger.info(f"意图分类为 '{intent}'，调用 _query_resource_by_type")
        return await _query_resource_by_type(
            request,
            log_manager,
            f"source_dispatch_{request.sourceType}",
            accident_data=accident_data,
            business_area=business_area,
            general_client=general_client
        )


@trace_function
async def _get_solid_resource_instruction(
    request: SourceDispatchRequest,
    log_manager: LogManager,
    client,
    entities: List[str]
) -> list:
    """
    调用 Dify 获取固体资源指令

    Args:
        request: 资源调度请求对象，包含资源类型
        log_manager: 日志管理器实例
        client: Dify client 实例（SOLID_RESOURCE_INSTRUCTION）
        entities: 实体名称字符串列表

    Returns:
        list: 包含资源ID列表的结果，格式如 [{"id":"1111"},{"id":"2222"}]

    Raises:
        ValueError: 如果 client 未配置
    """
    logger = log_manager.get_function_logger("solid_resource_instruction")
    logger.info(f"获取固体资源指令，资源类型: {request.sourceType}, 实体数量: {len(entities)}")

    # 验证 client 是否可用
    if client is None:
        raise ValueError("Dify solid_resource_instruction client 未配置。请在环境变量中设置 DIFY_CHAT_APIKEY_SOLID_RESOURCE_INSTRUCTION")

    # 存储所有返回的 ID
    result_ids = []

    # 循环遍历 entities，对每个实体名称调用 dify client
    for entity_name in entities:
        logger.debug(f"调用 Dify，实体名称: {entity_name}, 资源类型: {request.sourceType}")

        # 调用 Dify run_chat
        dify_response = await asyncio.to_thread(
            client.run_chat,
            query=entity_name,
            user="system",
            inputs={"resource_type": request.sourceType},
            conversation_id=""
        )

        # 提取 answer 字段（默认是全部由数字组成的 str 串，也就是 ID）
        answer = dify_response.answer if hasattr(dify_response, 'answer') else str(dify_response)
        answer = answer.strip()

        if answer:
            # 将 ID 包装成 {"id": "xxx"} 格式
            result_ids.append({"id": answer})
            logger.debug(f"实体 {entity_name} 返回 ID: {answer}")
        else:
            logger.warning(f"实体 {entity_name} 返回空 ID")

    logger.info(f"成功调用 Dify solid_resource_instruction，返回 {len(result_ids)} 个 ID")
    return result_ids


@trace_function
async def _query_resource_by_type(
    request: SourceDispatchRequest,
    log_manager: LogManager,
    function_name: str,
    accident_data: AccidentEventData,
    business_area: Optional[str] = None,
    number: int = 5,
    general_client = None
) -> List[Any]:
    """
    通用的资源查询函数，根据资源类型执行SQL查询并映射到实体类

    Args:
        request: 资源调度请求对象
        log_manager: 日志管理器实例
        function_name: 功能名称，用于日志记录
        accident_data: 事故事件数据，用于 AI 筛选
        business_area: 业务领域（可选，用于救援队伍和应急专家）
        number: 查询数量限制（默认5）
        general_client: Dify general_chat client 实例（用于 AI 筛选）

    Returns:
        List[Any]: 实体类实例列表
    """
    logger = log_manager.get_function_logger(function_name)
    logger.info(f"处理资源调度: {request.sourceType}")

    # 实体类映射
    entity_mapping = {
        "emergencySupplies": EmergencySupply,
        "rescueTeam": RescueTeam,
        "emergencyExpert": EmergencyExpert,
        "fireFightingFacilities": FireFightingFacility,
        "shelter": Shelter,
        "medicalInstitution": MedicalInstitution,
        "rescueOrganization": RescueOrganization,
        "protectionTarget": ProtectionTarget
    }

    # 实体类工厂方法映射（用于有位置字段的实体）
    entity_factory_mapping = {
        "fireFightingFacilities": ("from_db_row", ["id", "name", "latitude_longitude"]),
        "shelter": ("from_db_row", ["id", "shelter_name", "lon_and_lat"]),
        "medicalInstitution": ("from_db_row", ["id", "institution_name", "local_pos"]),
        "rescueOrganization": ("from_db_row", ["id", "institution_name", "local_pos"]),
        "protectionTarget": ("from_db_row", ["id", "target_name", "local_pos"])
    }

    # 获取映射配置
    mapping = SOURCE_TYPE_MAPPING.get(request.sourceType)
    if not mapping:
        raise ValueError(f"未找到资源类型 {request.sourceType} 的映射配置")

    # 构建SQL语句
    table_name = mapping["table_name"]
    sql_template = mapping["sql_template"]

    # 替换SQL模板参数
    sql = sql_template.format(
        table_name=table_name,
        business_area=business_area or "",
        number=number
    )
    logger.debug(f"执行SQL查询: {sql}")

    # 执行查询
    server = Server()
    query_result = server.QueryBySQL(sql)
    logger.debug(f"查询结果类型: {type(query_result)}")

    # 处理查询结果，提取数据列表
    data_list = []
    if isinstance(query_result, dict):
        if 'data' in query_result:
            data_list = query_result['data']
        elif 'result' in query_result:
            data_list = query_result['result']
        else:
            data_list = [query_result]
    elif isinstance(query_result, list):
        data_list = query_result

    logger.info(f"查询到 {len(data_list)} 条记录")

    # 获取实体类
    entity_class = entity_mapping.get(request.sourceType)
    if not entity_class:
        raise ValueError(f"未找到实体类: {request.sourceType}")

    # 将数据库行映射到实体类
    entities = []
    for row in data_list:
        try:
            # 检查是否需要使用工厂方法
            if request.sourceType in entity_factory_mapping:
                factory_method, field_names = entity_factory_mapping[request.sourceType]
                # 提取字段值（大小写不敏感）
                values = []
                for field_name in field_names:
                    # 尝试不同的大小写组合
                    value = row.get(field_name) or row.get(field_name.upper()) or row.get(field_name.lower())
                    # ID字段转换为字符串
                    if field_name.lower() == 'id' and value is not None:
                        value = str(value)
                    values.append(value)
                # 调用工厂方法
                entity = getattr(entity_class, factory_method)(*values)
                entities.append(entity)
            else:
                # 直接实例化（处理字段名大小写和类型转换）
                normalized_row = {}
                for key, value in row.items():
                    key_lower = key.lower()
                    # ID字段转换为字符串
                    if key_lower == 'id' and value is not None:
                        value = str(value)
                    normalized_row[key_lower] = value
                entity = entity_class(**normalized_row)
                entities.append(entity)
        except Exception as e:
            logger.warning(f"加载实体失败: {e}, 数据: {row}")
            continue

    logger.info(f"成功加载 {len(entities)} 个实体实例")

    # 对有坐标的实体（除医疗机构外）按距离排序
    entities_with_coords = [
        "fireFightingFacilities",
        "shelter",
        "rescueOrganization",
        "protectionTarget"
    ]

    if request.sourceType in entities_with_coords:
        from src.utils.geo_utils import sort_entities_by_distance
        entities = sort_entities_by_distance(accident_data, entities)
        logger.info(f"已按距离排序 {request.sourceType} 实体")

    # 验证 general_client 是否可用
    if general_client is None:
        raise ValueError("Dify general_chat client 未配置")

    # 使用 AI 筛选实体 ID
    # 将实体列表序列化为 JSON（作为数据库信息）
    entities_json = json.dumps(
        [{"id": entity.id, "name": getattr(entity, 'name', getattr(entity, 'shelter_name', getattr(entity, 'institution_name', getattr(entity, 'target_name', ''))))} for entity in entities],
        ensure_ascii=False
    )

    # 获取提示词
    prompt = SourceDispatchPrompts.get_database_id_extraction_prompt(
        voice_text=request.voiceText,
        accent_result=accident_data.to_json_str()
    )

    # 将数据库信息插入到提示词中
    prompt = prompt.replace("<数据库信息>\n\n</数据库信息>", f"<数据库信息>\n{entities_json}\n</数据库信息>")

    logger.debug(f"AI 筛选提示词: {prompt}")

    # 调用 Dify
    dify_response = await asyncio.to_thread(
        general_client.run_chat,
        query=prompt,
        user="system",
        inputs={},
        conversation_id=""
    )

    # 提取 answer 并解析为列表
    answer = dify_response.answer if hasattr(dify_response, 'answer') else str(dify_response)
    logger.debug(f"AI 筛选响应: {answer}")

    # 使用辅助函数解析 AI 响应
    return _parse_ai_response_to_list(answer, logger)


@trace_function
async def handle_emergency_supplies(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理应急物资资源调度"""
    logger = log_manager.get_function_logger("emergency_supplies")
    logger.info(f"处理应急物资资源调度: {request.sourceType}")

    # 获取映射配置
    mapping = SOURCE_TYPE_MAPPING.get(request.sourceType)
    if not mapping:
        raise ValueError(f"未找到资源类型 {request.sourceType} 的映射配置")

    # 构建SQL语句
    table_name = mapping["table_name"]
    sql = mapping["sql_template"].format(table_name=table_name)
    logger.debug(f"执行SQL查询: {sql}")

    # 执行查询
    server = Server()
    query_result = server.QueryBySQL(sql)
    logger.debug(f"查询结果: {query_result}")

    # 处理查询结果
    if isinstance(query_result, dict):
        if 'data' in query_result:
            return query_result['data']
        elif 'result' in query_result:
            return query_result['result']
        else:
            return [query_result]
    elif isinstance(query_result, list):
        return query_result
    else:
        return []


@trace_function
async def handle_rescue_team(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理救援队伍资源调度"""
    logger = log_manager.get_function_logger("rescue_team")
    logger.info(f"处理救援队伍资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_emergency_expert(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理应急专家资源调度"""
    logger = log_manager.get_function_logger("emergency_expert")
    logger.info(f"处理应急专家资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_fire_fighting_facilities(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理消防设施资源调度"""
    logger = log_manager.get_function_logger("fire_fighting_facilities")
    logger.info(f"处理消防设施资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_shelter(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理避难场所资源调度"""
    logger = log_manager.get_function_logger("shelter")
    logger.info(f"处理避难场所资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_medical_institution(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理医疗机构资源调度"""
    logger = log_manager.get_function_logger("medical_institution")
    logger.info(f"处理医疗机构资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_rescue_organization(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理救援机构资源调度"""
    logger = log_manager.get_function_logger("rescue_organization")
    logger.info(f"处理救援机构资源调度: {request.sourceType}")
    return []


@trace_function
async def handle_protection_target(
    request: SourceDispatchRequest,
    log_manager: LogManager
) -> list:
    """处理防护目标资源调度"""
    logger = log_manager.get_function_logger("protection_target")
    logger.info(f"处理防护目标资源调度: {request.sourceType}")
    return []