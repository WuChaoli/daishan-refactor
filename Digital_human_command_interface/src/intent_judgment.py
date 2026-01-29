"""
intent_judgment - 意图判断核心逻辑
负责协调整体意图判断流程,包括相似度排序、阈值判断和意图类型映射
"""

from dataclasses import dataclass
from typing import List, Optional

from src.config import Config
from src.log_manager import LogManager
from src.ragflow_client import RagflowClient


@dataclass
class QueryResult:
    """查询结果"""

    question: str  # 匹配的问题原文
    similarity: float  # 相似度分数


@dataclass
class IntentResult:
    """意图识别结果"""

    type: int  # 意图类型 (0/1/2)
    query: str  # 用户原始查询
    results: List[QueryResult]  # Top 5 查询结果
    similarity: float  # 最高相似度
    database: str  # 匹配的知识库名称


async def intent_judgment(
    query: str,
    client: Optional[RagflowClient],
    config: Optional[Config],
    log_manager: Optional[LogManager],
    databases: list = []
) -> IntentResult:
    """
    意图判断核心函数

    Args:
        query: 用户查询文本
        client: RAGFlow 客户端
        config: 应用配置
        log_manager: 日志管理器

    Returns:
        意图识别结果,包含 type、query 和. Top 5 查询结果
    """
    # 空值检查
    if log_manager is None:
        raise ValueError("LogManager not initialized")
    if client is None:
        raise ValueError("RagflowClient not initialized")
    if config is None:
        raise ValueError("Config not initialized")

    logger = log_manager.get_function_logger("intent_judgment")

    logger.info(f"开始意图判断，query='{query[:50]}...'")
    log_manager.log_function(
        "intent_judgment",
        "INFO",
        f"开始意图判断",
        query=query[:50],
    )

    try:
        # 调用 RAGFlow 客户端查询所有知识库
        all_results = []
        if databases:
            for database in databases:
                query_result = await client.query_single_database(query, database)
                all_results.extend(query_result)
        else:
            all_results = await client.query_all_databases(query)

        if not all_results:
            # RAGFlow 返回空结果，触发降级策略
            logger.warning("RAGFlow 返回空结果，降级到 type=0")
            log_manager.log_function(
                "intent_judgment",
                "WARNING",
                f"降级到 type=0",
                reason="RAGFlow 返回空结果",
            )
            return IntentResult(
                type=config.default_type,
                query=query,
                results=[],
                similarity=0.0,
                database="",
            )

        # 获取最高相似度结果
        best_result = all_results[0]
        logger.info(
            f"最高相似度={best_result.total_similarity:.4f}, "
            f"知识库={best_result.database}"
        )

        # 确定意图类型
        intent_type = config.default_type

        # 判断相似度是否达到阈值
        if best_result.total_similarity >= config.similarity_threshold:
            try:
                intent_type = config.get_type_mapping(best_result.database)
                logger.info(
                    f"知识库映射成功: {best_result.database} -> type={intent_type}"
                )
            except KeyError as e:
                # 知识库不在映射表中，降级到 type=0
                logger.error(f"知识库映射错误: {str(e)}，降级到 type=0")
                log_manager.log_function(
                    "intent_judgment",
                    "ERROR",
                    f"知识库映射错误",
                    database=best_result.database,
                    error=str(e),
                )
        else:
            logger.warning(
                f"相似度 {best_result.total_similarity:.4f} < 阈值 {config.similarity_threshold}，"
                f"降级到 type=0"
            )
            log_manager.log_function(
                "intent_judgment",
                "WARNING",
                f"降级到 type=0",
                reason="相似度不足",
                similarity=best_result.total_similarity,
                threshold=config.similarity_threshold,
            )

        # 获取相似度最高的知识库名称
        best_database = best_result.database

        # 从该知识库的结果中提取 Top 5
        database_results = [r for r in all_results if r.database == best_database][
            :5
        ]  # 取前5个结果

        # 转换为 QueryResult 列表
        top_results = [
            QueryResult(question=r.question, similarity=r.total_similarity)
            for r in database_results
        ]

        logger.info(
            f"意图判断完成: type={intent_type}, "
            f"知识库={best_database}, "
            f"相似度={best_result.total_similarity:.4f}, "
            f"返回结果数={len(top_results)}"
        )
        log_manager.log_function(
            "intent_judgment",
            "INFO",
            f"意图判断完成",
            type=intent_type,
            database=best_database,
            similarity=best_result.total_similarity,
            results_count=len(top_results),
        )

        return IntentResult(
            type=intent_type,
            query=query,
            results=top_results,  # 总是返回 Top 5 结果
            similarity=best_result.total_similarity,
            database=best_database,
        )

    except Exception as e:
        # 未预期异常，降级到 type=0
        logger.error(f"意图判断异常: {str(e)}", exc_info=True)
        log_manager.log_function(
            "intent_judgment", "ERROR", f"意图判断异常", error=str(e)
        )
        return IntentResult(
            type=config.default_type,
            query=query,
            results=[],
            similarity=0.0,
            database="",
        )

async def instrcut_judgement(
    query: str,
    client: Optional[RagflowClient],
    config: Optional[Config],
    log_manager: Optional[LogManager],
) -> IntentResult:
    """
    判断指令内容

    Args:
        query: 用户查询文本
        client: RAGFlow 客户端
        config: 应用配置
        log_manager: 日志管理器

    Returns:
        返回指令内容
    """
    # 空值检查
    if log_manager is None:
        raise ValueError("LogManager not initialized")
    if client is None:
        raise ValueError("RagflowClient not initialized")
    if config is None:
        raise ValueError("Config not initialized")

    logger = log_manager.get_function_logger("instrcut_judgement")

    logger.info(f"开始意图判断，query='{query[:50]}...'")
    log_manager.log_function(
        "instrcut_judgement",
        "INFO",
        f"开始意图判断",
        query=query[:50],
    )

    try:
        # 调用 RAGFlow 客户端查询所有知识库
        all_results = await client.query_single_database(query, "岱山-指令集")

        if not all_results:
            # RAGFlow 返回空结果，触发降级策略
            logger.warning("RAGFlow 返回空结果，降级到 type=0")
            log_manager.log_function(
                "intent_judgment",
                "WARNING",
                f"降级到 type=0",
                reason="RAGFlow 返回空结果",
            )
            return IntentResult(
                type=config.default_type,
                query=query,
                results=[],
                similarity=0.0,
                database="",
            )

        # 获取最高相似度结果
        best_result = all_results[0]
        logger.info(
            f"最高相似度={best_result.total_similarity:.4f}, "
            f"知识库={best_result.database}"
        )

        # 确定意图类型
        intent_type = config.default_type
        target_database = ""

        # 判断相似度是否达到阈值
        if best_result.total_similarity >= config.similarity_threshold:
            try:
                intent_type = config.get_type_mapping(best_result.database)
                target_database = best_result.database
                logger.info(
                    f"知识库映射成功: {best_result.database} -> type={intent_type}"
                )
            except KeyError as e:
                # 知识库不在映射表中，降级到 type=0
                logger.error(f"知识库映射错误: {str(e)}，降级到 type=0")
                log_manager.log_function(
                    "intent_judgment",
                    "ERROR",
                    f"知识库映射错误",
                    database=best_result.database,
                    error=str(e),
                )
        else:
            logger.warning(
                f"相似度 {best_result.total_similarity:.4f} < 阈值 {config.similarity_threshold}，"
                f"降级到 type=0"
            )
            log_manager.log_function(
                "intent_judgment",
                "WARNING",
                f"降级到 type=0",
                reason="相似度不足",
                similarity=best_result.total_similarity,
                threshold=config.similarity_threshold,
            )

        # 获取相似度最高的知识库名称
        best_database = best_result.database

        # 从该知识库的结果中提取 Top 5
        database_results = [r for r in all_results if r.database == best_database][
            :5
        ]  # 取前5个结果

        # 转换为 QueryResult 列表
        top_results = [
            QueryResult(question=r.question, similarity=r.total_similarity)
            for r in database_results
        ]

        logger.info(
            f"意图判断完成: type={intent_type}, "
            f"知识库={best_database}, "
            f"相似度={best_result.total_similarity:.4f}, "
            f"返回结果数={len(top_results)}"
        )
        log_manager.log_function(
            "intent_judgment",
            "INFO",
            f"意图判断完成",
            type=intent_type,
            database=best_database,
            similarity=best_result.total_similarity,
            results_count=len(top_results),
        )

        # 无论 type 是什么(0/1/2),都返回统一的响应结构
        return IntentResult(
            type=intent_type,
            query=query,
            results=top_results,  # 总是返回 Top 5 结果
            similarity=best_result.total_similarity,
            database=best_database,
        )

    except Exception as e:
        # 未预期异常，降级到 type=0
        logger.error(f"意图判断异常: {str(e)}", exc_info=True)
        log_manager.log_function(
            "intent_judgment", "ERROR", f"意图判断异常", error=str(e)
        )
        return IntentResult(
            type=config.default_type,
            query=query,
            results=[],
            similarity=0.0,
            database="",
        )
