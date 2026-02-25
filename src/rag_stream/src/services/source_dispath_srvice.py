"""
SourceDispatchService - 资源调度服务
负责处理资源调度相关的业务逻辑
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Type
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
from src.utils.prompts import SourceDispatchPrompts
from src.config.settings import settings
from src.utils.log_manager_import import trace, marker
from src.utils.daishan_sql_logging import format_daishan_log_text
from DaiShanSQL import Server

# 加载sourceType映射配置
MAPPING_FILE = Path(__file__).resolve().parents[1] / "utils" / "source_type_mapping.json"
with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    SOURCE_TYPE_MAPPING = json.load(f)


@trace
async def handle_source_dispatch(
    request: SourceDispatchRequest
) -> List[Dict[str, str]]:
    """
    处理资源调度请求

    Args:
        request: 资源调度请求对象，包含事故ID、资源类型和语音文本

    Returns:
        List[Dict[str, str]]: 资源列表，每个资源包含id等字段
    """

    try:
        accident_id = _validate_and_extract_accident_id(request)
        marker("source_dispatch.start", {"accident_id": accident_id, "source_type": request.sourceType})

        sql = _build_accident_query_sql(accident_id)

        query_result = _query_accident_from_database(sql)
        accident_data = _parse_accident_query_result(query_result, accident_id)
        marker("accident.loaded", {"name": accident_data.accident_name, "overview_len": len(accident_data.accident_overview or '')})

        general_client, solid_client = _get_dify_clients()

        intent_query, accident_type_query, entity_query = _build_parallel_dify_queries(request, accident_data)
        marker("dify.parallel.start")

        intent_response, accident_type_response, entity_response = await _call_dify_parallel_analysis(
            general_client, intent_query, accident_type_query, entity_query
        )
        marker("dify.parallel.complete")

        intent, business_area, entities = _extract_analysis_results(
            intent_response, accident_type_response, entity_response
        )
        marker("analysis.complete", {"intent": intent.strip().lower(), "business_area": business_area, "entity_count": len(entities)})

        result = await _dispatch_by_intent(
            intent, request, solid_client, entities,
            accident_data, business_area, general_client
        )

        marker("source_dispatch.complete", {"source_type": request.sourceType, "result_count": len(result)})

        return result

    except ValueError as e:
        marker("source_dispatch.value_error", {"error": str(e)}, level="ERROR")
        return []
    except KeyError as e:
        marker("source_dispatch.key_error", {"error": str(e)}, level="ERROR")
        return []
    except Exception as e:
        marker("source_dispatch.exception", {"error": str(e)}, level="ERROR")
        return []


@trace
def _parse_ai_response_to_list(answer: str) -> List[Dict[str, Any]]:
    """
    解析 AI 响应为列表格式

    Args:
        answer: AI 返回的响应字符串

    Returns:
        List[Dict[str, Any]]: 解析后的列表

    Raises:
        ValueError: 如果响应不是有效的 JSON 列表格式
    """
    answer = answer.strip()
    marker("parse_ai_response.start", {"preview": repr(answer[:200])})

    if not answer:
        marker("parse_ai_response.empty", {}, level="WARNING")
        return []

    # 从文本中提取JSON
    json_str = _extract_json_from_text(answer)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        marker("parse_ai_response.json_error", {"error": str(e), "json_preview": repr(json_str[:200])}, level="ERROR")
        raise ValueError(f"AI响应不是有效的JSON格式: {answer[:100]}")

    if not isinstance(result, list):
        raise ValueError(f"AI 返回的不是列表格式: {answer[:100]}")

    marker("parse_ai_response.success", {"item_count": len(result)})
    return result


@trace
def _extract_json_from_text(text: str) -> str:
    """
    从文本中提取JSON格式内容，并确保格式正确

    Args:
        text: 可能包含JSON的文本字符串

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
            marker("extract_json.markdown_json", {"preview": json_str[:100]})
            return _normalize_json_string(json_str)

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            json_str = text[start:end].strip()
            marker("extract_json.markdown_code", {"preview": json_str[:100]})
            return _normalize_json_string(json_str)

    # 尝试找到JSON数组 [...]
    if "[" in text and "]" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        json_str = text[start:end].strip()
        marker("extract_json.array", {"preview": json_str[:100]})
        return _normalize_json_string(json_str)

    # 尝试找到JSON对象 {...}
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end].strip()
        marker("extract_json.object", {"preview": json_str[:100]})
        return _normalize_json_string(json_str)

    # 如果没有找到JSON标记，返回原始文本
    marker("extract_json.fallback")
    return _normalize_json_string(text)


@trace
def _normalize_json_string(json_str: str) -> str:
    """
    标准化JSON字符串，将Python格式转换为JSON格式

    Args:
        json_str: 可能是Python格式或JSON格式的字符串

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
        marker("normalize_json.already_valid")
        return json_str
    except json.JSONDecodeError:
        marker("normalize_json.try_python")

    # 尝试作为Python字面量解析（支持单引号）
    try:
        parsed = ast.literal_eval(json_str)
        # 转换为标准JSON格式
        normalized = json.dumps(parsed, ensure_ascii=False)
        marker("normalize_json.converted", {"preview": normalized[:100]})
        return normalized
    except (ValueError, SyntaxError) as e:
        marker("normalize_json.failed", {"error": str(e)}, level="WARNING")
        # 返回原始字符串，让调用方处理错误
        return json_str


@trace
def _parse_entity_list(answer: str) -> List[str]:
    """
    解析实体提取响应为字符串列表

    Args:
        answer: AI 返回的响应字符串，预期格式为 ["实体1", "实体2", ...]

    Returns:
        List[str]: 解析后的实体列表

    Raises:
        ValueError: 如果响应不是有效的 JSON 列表格式
    """
    # 去除首尾空格
    answer = answer.strip()
    marker("parse_entity.start", {"preview": repr(answer[:200])})

    # 处理空响应
    if not answer:
        marker("parse_entity.empty", {}, level="WARNING")
        return []

    # 从文本中提取JSON
    json_str = _extract_json_from_text(answer)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        marker("parse_entity.json_error", {"error": str(e), "json_preview": repr(json_str[:200])}, level="ERROR")
        raise ValueError(f"实体提取响应不是有效的JSON格式: {answer[:100]}")

    if not isinstance(result, list):
        raise ValueError(f"AI 返回的不是列表格式: {answer[:100]}")

    # 确保所有元素都是字符串
    str_list = [str(item) for item in result]
    marker("parse_entity.success", {"entity_count": len(str_list)})
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


def _query_accident_from_database(sql: str) -> Any:
    """查询事故数据"""
    server = Server()
    marker("DaiShanSQL入参", {"入参": format_daishan_log_text(sql)})
    try:
        query_result = server.QueryBySQL(sql)
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(query_result)})
        return query_result
    except Exception as error:
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(f"ERROR: {error}")}, level="ERROR")
        raise


@trace
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


def _get_dify_clients() -> tuple:
    """获取Dify客户端实例"""
    from src.utils.dify_client_factory import get_client

    general_client = get_client("GENRAL_CHAT")
    if general_client is None:
        raise ValueError("Dify general_chat client 未配置。请在环境变量中设置 DIFY_CHAT_APIKEY_GENRAL_CHAT")

    try:
        solid_client = get_client("SOLID_RESOURCE_INSTRUCTION")
    except ValueError as e:
        marker("get_dify_clients.solid_missing", {"error": str(e)}, level="WARNING")
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
    entity_response
) -> tuple:
    """提取意图、事故类型和实体列表"""
    intent_answer = intent_response.answer if hasattr(intent_response, 'answer') else str(intent_response)
    if not intent_answer:
        raise ValueError("意图分类响应为空")

    business_area = accident_type_response.answer if hasattr(accident_type_response, 'answer') else str(accident_type_response)
    business_area = business_area.strip()

    entity_answer = entity_response.answer if hasattr(entity_response, 'answer') else str(entity_response)
    entities = _parse_entity_list(entity_answer)

    return intent_answer, business_area, entities


async def _dispatch_by_intent(
    intent: str,
    request: SourceDispatchRequest,
    solid_client,
    entities: List[str],
    accident_data: AccidentEventData,
    business_area: str,
    general_client
) -> Dict[str, Any]:
    """根据意图分类结果分发处理"""
    if intent.strip().lower() == "resource":
        marker("dispatch.resource_intent", {"entity_count": len(entities)})
        return await _get_solid_resource_instruction(
            request,
            solid_client,
            entities
        )
    else:
        marker("dispatch.filter_intent", {"source_type": request.sourceType, "business_area": business_area})

        # 资源类型到处理函数的映射
        handler_mapping = {
            "emergencySupplies": handle_emergency_supplies,
            "rescueTeam": handle_rescue_team,
            "emergencyExpert": handle_emergency_expert,
            "fireFightingFacilities": handle_fire_fighting_facilities,
            "shelter": handle_shelter,
            "medicalInstitution": handle_medical_institution,
            "rescueOrganization": handle_rescue_organization,
            "protectionTarget": handle_protection_target
        }

        handler = handler_mapping.get(request.sourceType)
        if not handler:
            raise ValueError(f"未找到资源类型 {request.sourceType} 的处理函数")

        # 根据资源类型调用相应的处理函数
        # 救援队伍和应急专家需要 business_area 参数
        if request.sourceType in ["rescueTeam", "emergencyExpert"]:
            return await handler(
                request=request,
                accident_data=accident_data,
                business_area=business_area,
                general_client=general_client
            )
        else:
            return await handler(
                request=request,
                accident_data=accident_data,
                general_client=general_client
            )


async def _get_solid_resource_instruction(
    request: SourceDispatchRequest,
    client,
    entities: List[str]
) -> list:
    """
    调用 Dify 获取固体资源指令

    Args:
        request: 资源调度请求对象，包含资源类型
        client: Dify client 实例（SOLID_RESOURCE_INSTRUCTION）
        entities: 实体名称字符串列表

    Returns:
        list: 包含资源ID列表的结果，格式如 [{"id":"1111"},{"id":"2222"}]

    Raises:
        ValueError: 如果 client 未配置
    """
    marker("solid_resource.start", {"source_type": request.sourceType, "entity_count": len(entities)})

    # 验证 client 是否可用
    if client is None:
        raise ValueError("Dify solid_resource_instruction client 未配置。请在环境变量中设置 DIFY_CHAT_APIKEY_SOLID_RESOURCE_INSTRUCTION")

    # 存储所有返回的 ID
    result_ids = []

    # 循环遍历 entities，对每个实体名称调用 dify client
    for entity_name in entities:
        marker("solid_resource.call_dify", {"entity": entity_name, "resource_type": request.sourceType})

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
        else:
            marker("solid_resource.empty_id", {"entity": entity_name}, level="WARNING")

    marker("solid_resource.complete", {"result_count": len(result_ids)})
    return result_ids


def _get_sql_from_mapping(
    source_type: str,
    business_area: Optional[str],
    number: int
) -> str:
    """从映射配置获取SQL语句"""
    mapping = SOURCE_TYPE_MAPPING.get(source_type)
    if not mapping:
        raise ValueError(f"未找到资源类型 {source_type} 的映射配置")
    
    return mapping["sql_template"].format(
        table_name=mapping["table_name"],
        business_area=business_area or "",
        number=number
    )


async def _execute_resource_query(
    source_type: str,
    business_area: Optional[str] = None,
    number: int = 5
) -> List[Dict[str, Any]]:
    """执行资源查询并返回原始数据行"""
    sql = _get_sql_from_mapping(source_type, business_area, number)
    marker("resource_query.execute", {"source_type": source_type, "has_business_area": bool(business_area), "limit": number})
    server = Server()
    marker("DaiShanSQL入参", {"入参": format_daishan_log_text(sql)})
    try:
        query_result = server.QueryBySQL(sql)
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(query_result)})
    except Exception as error:
        marker("DaiShanSQL出参", {"出参": format_daishan_log_text(f"ERROR: {error}")}, level="ERROR")
        raise
    data_list = _extract_data_list_from_query_result(query_result)
    marker("resource_query.complete", {"source_type": source_type, "row_count": len(data_list)})
    return data_list


def _map_to_entities(
    rows: List[Dict[str, Any]],
    entity_class: Type,
    entity_factory_config: Optional[tuple] = None
) -> List[Any]:
    """将数据库行映射为实体对象"""
    return _map_rows_to_entities(rows, entity_class, entity_factory_config)


def _sort_by_distance(
    entities: List[Any],
    accident_data: AccidentEventData
) -> List[Any]:
    """按距离排序实体列表"""
    from src.utils.geo_utils import sort_entities_by_distance
    return sort_entities_by_distance(accident_data, entities)


def _build_ai_prompt(
    entities: List[Any],
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    prompt_generator: Callable
) -> str:
    """构建AI筛选提示词"""
    entities_json = _serialize_entities_to_json(entities)
    prompt = prompt_generator(
        voice_text=request.voiceText,
        accent_result=accident_data.to_json_str()
    )
    return prompt.replace(
        "<数据库信息>\n\n</数据库信息>",
        f"<数据库信息>\n{entities_json}\n</数据库信息>"
    )


async def _filter_with_ai(
    entities: List[Any],
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    prompt_generator: Callable,
    general_client
) -> List[Dict[str, Any]]:
    """使用AI进行智能筛选"""
    if general_client is None:
        raise ValueError("Dify general_chat client 未配置")

    prompt = _build_ai_prompt(entities, request, accident_data, prompt_generator)
    marker("ai_filter.start", {"source_type": request.sourceType, "candidate_count": len(entities)})
    
    dify_response = await asyncio.to_thread(
        general_client.run_chat,
        query=prompt,
        user="system",
        inputs={},
        conversation_id=""
    )

    answer = dify_response.answer if hasattr(dify_response, 'answer') else str(dify_response)
    filtered = _parse_ai_response_to_list(answer)
    marker("ai_filter.complete", {"source_type": request.sourceType, "selected_count": len(filtered)})
    return filtered


def _extract_data_list_from_query_result(query_result: Any) -> list:
    """从查询结果中提取数据列表"""
    if isinstance(query_result, dict):
        if 'data' in query_result:
            return query_result['data']
        elif 'result' in query_result:
            return query_result['result']
        else:
            return [query_result]
    elif isinstance(query_result, list):
        return query_result
    return []


def _map_rows_to_entities(
    data_list: list,
    entity_class,
    entity_factory_config: Optional[tuple]
) -> list:
    """将数据库行映射到实体类实例"""
    entities = []
    for row in data_list:
        try:
            if entity_factory_config:
                # 使用工厂方法
                factory_method, field_names = entity_factory_config
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
            marker("map_entities.failed", {"error": str(e)}, level="WARNING")
            continue
    return entities


def _serialize_entities_to_json(entities: list) -> str:
    """将实体列表序列化为JSON字符串"""
    entity_list = []
    for entity in entities:
        # 尝试不同的名称字段
        name = getattr(entity, 'name', None) or \
               getattr(entity, 'shelter_name', None) or \
               getattr(entity, 'institution_name', None) or \
               getattr(entity, 'target_name', '')
        entity_list.append({"id": entity.id, "name": name})
    return json.dumps(entity_list, ensure_ascii=False)


async def handle_emergency_supplies(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理应急物资资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(rows, EmergencySupply, None)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_emergency_supplies_prompt,
        general_client
    )


async def handle_rescue_team(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    business_area: str,
    general_client
) -> list:
    """处理救援队伍资源调度"""
    rows = await _execute_resource_query(request.sourceType, business_area, 5)
    entities = _map_to_entities(rows, RescueTeam, None)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_rescue_team_prompt,
        general_client
    )


async def handle_emergency_expert(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    business_area: str,
    general_client
) -> list:
    """处理应急专家资源调度"""
    rows = await _execute_resource_query(request.sourceType, business_area, 5)
    entities = _map_to_entities(rows, EmergencyExpert, None)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_emergency_expert_prompt,
        general_client
    )


async def handle_fire_fighting_facilities(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理消防设施资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(
        rows, FireFightingFacility,
        ("from_db_row", ["id", "name", "latitude_longitude"])
    )
    entities = _sort_by_distance(entities, accident_data)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_fire_fighting_facilities_prompt,
        general_client
    )


async def handle_shelter(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理避难场所资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(
        rows, Shelter,
        ("from_db_row", ["id", "shelter_name", "lon_and_lat"])
    )
    entities = _sort_by_distance(entities, accident_data)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_shelter_prompt,
        general_client
    )


async def handle_medical_institution(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理医疗机构资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(
        rows, MedicalInstitution,
        ("from_db_row", ["id", "institution_name", "local_pos"])
    )
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_medical_institution_prompt,
        general_client
    )


async def handle_rescue_organization(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理救援机构资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(
        rows, RescueOrganization,
        ("from_db_row", ["id", "institution_name", "local_pos"])
    )
    entities = _sort_by_distance(entities, accident_data)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_rescue_organization_prompt,
        general_client
    )


async def handle_protection_target(
    request: SourceDispatchRequest,
    accident_data: AccidentEventData,
    general_client
) -> list:
    """处理防护目标资源调度"""
    rows = await _execute_resource_query(request.sourceType, number=5)
    entities = _map_to_entities(
        rows, ProtectionTarget,
        ("from_db_row", ["id", "target_name", "local_pos"])
    )
    entities = _sort_by_distance(entities, accident_data)
    return await _filter_with_ai(
        entities, request, accident_data,
        SourceDispatchPrompts.get_protection_target_prompt,
        general_client
    )
