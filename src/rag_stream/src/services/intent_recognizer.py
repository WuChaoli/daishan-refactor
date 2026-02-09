"""
intent_recognizer - 通用意图识别模块
基于 RAG 检索结果进行排序、映射和目标结果提取
"""

from dataclasses import dataclass
import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

from src.config.settings import Settings, settings

if TYPE_CHECKING:
    from src.services.ragflow_client import RagflowClient


@dataclass
class IntentRecognitionResult:
    """通用意图识别结果"""

    query: str
    intent_type: int
    database: str
    similarity: float
    database_results: List[Any]


@dataclass
class IntentRecognizerSettings:
    """意图识别参数配置"""

    database_mapping: Mapping[str, Any]
    similarity_threshold: float
    top_k: int
    default_type: int


DatabaseResultsDict = Dict[str, List[Any]]
JudgeFunction = Callable[[DatabaseResultsDict, IntentRecognizerSettings], Optional[Any]]


_runtime_settings: Optional[IntentRecognizerSettings] = None
_runtime_client: Optional["RagflowClient"] = None
_runtime_judge_function: Optional[JudgeFunction] = None


def _default_yaml_path() -> Path:
    """获取 rag_stream/config.yaml 默认路径"""
    return Path(__file__).resolve().parents[2] / "config.yaml"


def _default_mapping_file_path() -> Path:
    """获取 services 下默认映射文件路径"""
    return Path(__file__).resolve().parent / "intent_mapping.example.json"


def load_database_mapping_from_json(
    mapping_file: Optional[Union[str, Path]] = None,
) -> Mapping[str, Any]:
    """从 services 下 JSON 文件加载数据库映射"""
    mapping_path = Path(mapping_file) if mapping_file else _default_mapping_file_path()

    with open(mapping_path, "r", encoding="utf-8") as fp:
        payload = json.load(fp) or {}

    if not isinstance(payload, dict):
        raise ValueError("mapping json 根节点必须是对象")

    database_mapping = payload.get("database_mapping", payload)
    if not isinstance(database_mapping, dict):
        raise ValueError("database_mapping 必须是对象")

    return database_mapping


def load_intent_recognizer_settings_from_json(
    config_file: Optional[Union[str, Path]] = None,
) -> IntentRecognizerSettings:
    """从 JSON 文件加载意图识别设置"""
    config_path = Path(config_file) if config_file else _default_mapping_file_path()

    with open(config_path, "r", encoding="utf-8") as fp:
        payload = json.load(fp) or {}

    if not isinstance(payload, dict):
        raise ValueError("intent recognizer json 根节点必须是对象")

    database_mapping = payload.get("database_mapping", payload)
    if not isinstance(database_mapping, dict):
        raise ValueError("database_mapping 必须是对象")

    similarity_threshold = payload.get(
        "similarity_threshold",
        settings.intent.similarity_threshold,
    )
    top_k = payload.get(
        "top_k",
        payload.get("top_k_per_database", settings.intent.top_k_per_database),
    )
    default_type = payload.get("default_type", settings.intent.default_type)

    return IntentRecognizerSettings(
        database_mapping=database_mapping,
        similarity_threshold=float(similarity_threshold),
        top_k=int(top_k),
        default_type=int(default_type),
    )


def default_judge_function(
    table_results: DatabaseResultsDict,
    recognizer_settings: IntentRecognizerSettings,
) -> Optional[Any]:
    """默认判断逻辑：将各表结果展开后按相似度排序，取最高且>=阈值的候选"""
    flattened_results: List[Any] = []
    for table_name in recognizer_settings.database_mapping.keys():
        flattened_results.extend(table_results.get(table_name, []))

    for table_name, table_items in table_results.items():
        if table_name not in recognizer_settings.database_mapping:
            flattened_results.extend(table_items)

    if not flattened_results:
        return None

    flattened_results.sort(key=_safe_similarity, reverse=True)
    candidate = flattened_results[0]
    if _safe_similarity(candidate) >= recognizer_settings.similarity_threshold:
        return candidate
    return None


def load_intent_recognizer_settings_from_yaml(
    yaml_path: Optional[Union[str, Path]] = None,
    mapping_file: Optional[Union[str, Path]] = None,
) -> tuple[IntentRecognizerSettings, Settings]:
    """从 config.yaml 加载意图识别设置"""
    config_path = Path(yaml_path) if yaml_path else _default_yaml_path()
    loaded_settings = Settings.load_from_yaml_with_env_override(config_path)
    database_mapping = load_database_mapping_from_json(mapping_file=mapping_file)

    recognizer_settings = IntentRecognizerSettings(
        database_mapping=database_mapping,
        similarity_threshold=loaded_settings.intent.similarity_threshold,
        top_k=loaded_settings.intent.top_k_per_database,
        default_type=loaded_settings.intent.default_type,
    )
    return recognizer_settings, loaded_settings


def configure_intent_recognizer(
    yaml_path: Optional[Union[str, Path]] = None,
    client: Optional["RagflowClient"] = None,
    mapping_file: Optional[Union[str, Path]] = None,
    judge_function: Optional[JudgeFunction] = None,
) -> IntentRecognizerSettings:
    """
    设置运行时意图识别配置（从 config.yaml 加载）

    - 映射、阈值、top_k、默认类型均由配置文件提供
    - client 需要由调用方传入，不在此处自动创建
    """
    global _runtime_settings, _runtime_client, _runtime_judge_function

    recognizer_settings, _ = load_intent_recognizer_settings_from_yaml(
        yaml_path=yaml_path,
        mapping_file=mapping_file,
    )
    _runtime_settings = recognizer_settings
    _runtime_judge_function = judge_function or default_judge_function
    _runtime_client = client

    return recognizer_settings


def _flatten_table_results(
    table_results: DatabaseResultsDict,
    recognizer_settings: IntentRecognizerSettings,
) -> List[Any]:
    """按映射配置顺序展开各表结果，并按相似度降序"""
    flattened_results: List[Any] = []

    for table_name in recognizer_settings.database_mapping.keys():
        flattened_results.extend(table_results.get(table_name, []))

    for table_name, table_items in table_results.items():
        if table_name not in recognizer_settings.database_mapping:
            flattened_results.extend(table_items)

    flattened_results.sort(key=_safe_similarity, reverse=True)
    return flattened_results


def _build_intent_result_from_table_results(
    query: str,
    table_results: DatabaseResultsDict,
    recognizer_settings: IntentRecognizerSettings,
    judge_function: Optional[JudgeFunction] = None,
) -> IntentRecognitionResult:
    """基于按表分组的结果，构建最终意图识别结果"""
    flattened_results = _flatten_table_results(table_results, recognizer_settings)
    if not flattened_results:
        return IntentRecognitionResult(
            query=query,
            intent_type=recognizer_settings.default_type,
            database="",
            similarity=0.0,
            database_results=[],
        )

    decide = judge_function or default_judge_function
    judged_result = decide(table_results, recognizer_settings)
    best_result = judged_result or flattened_results[0]

    best_database = getattr(best_result, "database", "") or ""
    best_similarity = _safe_similarity(best_result)
    database_results = table_results.get(best_database, [])[: recognizer_settings.top_k]

    intent_type = _normalize_intent_type(
        recognizer_settings.database_mapping.get(
            best_database,
            recognizer_settings.default_type,
        ),
        recognizer_settings.default_type,
    )
    # 默认逻辑下保留阈值兜底；自定义 judge_function 时由调用方自行控制
    if judge_function is None and best_similarity < recognizer_settings.similarity_threshold:
        intent_type = recognizer_settings.default_type

    return IntentRecognitionResult(
        query=query,
        intent_type=intent_type,
        database=best_database,
        similarity=best_similarity,
        database_results=database_results,
    )


def _safe_similarity(result: Any) -> float:
    """安全获取相似度分数"""
    value = getattr(result, "total_similarity", 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_intent_type(value: Any, default_type: int) -> int:
    """兼容意图映射值：支持 int 或 str（可转 int）"""
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return default_type
        try:
            return int(text)
        except ValueError:
            return default_type

    return default_type


def recognize_intent_from_results(
    query: str,
    all_results: Sequence[Any],
    database_mapping: Mapping[str, Any],
    default_type: int,
    similarity_threshold: float,
    top_k: int,
    judge_function: Optional[JudgeFunction] = None,
) -> IntentRecognitionResult:
    """
    通用意图识别入口：
    1. 对所有结果按相似度降序排序
    2. 选择最高相似度结果对应的查询表（database）
    3. 返回该查询表映射出的意图类型和该表的查询结果
    """
    recognizer_settings = IntentRecognizerSettings(
        database_mapping=database_mapping,
        similarity_threshold=similarity_threshold,
        top_k=top_k,
        default_type=default_type,
    )
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")

    table_results: DatabaseResultsDict = {}
    for item in all_results:
        table_name = getattr(item, "database", "") or ""
        table_results.setdefault(table_name, []).append(item)

    return _build_intent_result_from_table_results(
        query=query,
        table_results=table_results,
        recognizer_settings=recognizer_settings,
        judge_function=judge_function,
    )


async def recognize_intent(
    query: str,
    client: Optional["RagflowClient"] = None,
    recognizer_settings: Optional[IntentRecognizerSettings] = None,
    judge_function: Optional[JudgeFunction] = None,
) -> IntentRecognitionResult:
    """
    通用意图识别入口（包含 RAGFlow 查询步骤）

    对外仅需传入 query；其他参数可通过 configure_intent_recognizer 预先配置。
    """
    global _runtime_settings, _runtime_client, _runtime_judge_function

    if recognizer_settings is None:
        if _runtime_settings is None:
            configure_intent_recognizer(client=client)
        recognizer_settings = _runtime_settings

    if recognizer_settings is None:
        raise ValueError("IntentRecognizerSettings not initialized")

    active_client = client or _runtime_client
    if active_client is None:
        raise ValueError("RagflowClient not initialized, please pass client")

    if not hasattr(active_client, "query_single_database"):
        raise ValueError("RagflowClient missing query_single_database method")

    table_names = list(recognizer_settings.database_mapping.keys())
    tasks = [active_client.query_single_database(query, table_name) for table_name in table_names]
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    table_results: DatabaseResultsDict = {}
    for table_name, task_result in zip(table_names, task_results):
        if isinstance(task_result, Exception):
            table_results[table_name] = []
            continue
        if isinstance(task_result, list):
            table_results[table_name] = task_result
        else:
            table_results[table_name] = []

    return _build_intent_result_from_table_results(
        query=query,
        table_results=table_results,
        recognizer_settings=recognizer_settings,
        judge_function=judge_function or _runtime_judge_function,
    )
