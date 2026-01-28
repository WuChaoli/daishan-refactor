"""
IntentService - 意图识别服务
负责处理三种意图类型(Type 0/1/2)的业务逻辑
"""

import asyncio
import re

from rag_stream.src.services.intent_judgment import IntentResult, intent_judgment
from rag_stream.src.services.log_manager import LogManager
from rag_stream.src.services.ragflow_client import RagflowClient
from DaiShanSQL.DaiShanSQL.api_server import server, Server


class IntentService:
    """意图识别服务"""

    def __init__(
        self,
        log_manager: LogManager,
        ragflow_client: RagflowClient,
    ):
        """
        初始化意图识别服务

        Args:
            log_manager: 日志管理器
            ragflow_client: RAGFlow 客户端
        """
        self.log_manager = log_manager
        self.ragflow_client = ragflow_client
        self.logger = log_manager.get_function_logger("intent_service")

        # 初始化 Dify Chat 客户端 (延迟加载)
        # self.dify_chat_client = None
        self.park_kb_client = None
        self.enterprise_kb_client = None
        self.safety_kb_client = None
        self.type0_semantic_client = None

        # DaiShanSQL 现在使用动态导入，不需要预先初始化
        self.daishan_server = None

    async def process_query(self, text_input: str, user_id: str) -> dict:
        """
        处理用户查询,返回直接响应（非流式）

        Args:
            text_input: 用户输入文本
            user_id: 用户 ID

        Returns:
            字典格式响应 {"type": int, "data":": dict}
        """
        self.logger.info(f"处理用户查询, user_id={user_id}, query='{text_input[:50]}...'")

        try:
            # 步骤 1: 意图判断
            intent_result = await intent_judgment(
                query=text_input,
                client=self.ragflow_client,
                log_manager=self.log_manager,
            )

            self.logger.info(
                f"意图判断完成: type={intent_result.type}, "
                f"database={intent_result.database}, "
                f"similarity={intent_result.similarity:.4f}"
            )

            # 步骤 2: 根据意图类型路由到对应处理器
            if intent_result.type == 1:
                return await self._handle_type1(text_input, user_id, intent_result)
            else:
                return await self._handle_type2(text_input, user_id, intent_result)

        except Exception as e:
            self.logger.error(f"处理查询异常: {str(e)}", exc_info=True)
            return {"type": 0, "data": {"error": str(e)}}

    async def _handle_type1(
        self, text_input: str, user_id: str, intent_result: IntentResult
    ) -> dict:
        """
        Type 1 处理器: 明确指令类
        支持知识库查询 ([knowledgebase:xxx] 标记)

        Args:
            text_input: 用户输入
            user_id: 用户 ID
            intent_result: 意图识别结果

        Returns:
            {"type": 1, "data": {"kb_name": []}}
        """
        self.logger.info(f"Type 1 处理器: 明确指令类查询")

        try:
            # 检查是否包含 [knowledgebase:xxx] 标记
            # 从 intent_result.results[0].question 中提取知识库标记
            first_question = intent_result.results[0].question
            kb_match = re.search(r'\[knowledgebase:(\w+)\]', first_question)

            if kb_match:
                kb_name = kb_match.group(1)
                self.logger.info(f"检测到知识库标记: {kb_name}")
                result = ""
                if kb_name == "园区知识库":
                    result = "1"
                elif kb_name == "企业知识库":
                    result = server.sqlFixed.sql_ChemicalCompanyInfo()
                elif kb_name == "安全信息知识库":
                    result = server.sqlFixed.sql_SecuritySituation()
                
                self.logger.debug("sql_result: %s", result)
                
                return {"type": 1, "data": {"kb_name": kb_name, "sql_result": str(result)}}
            else:
                # 无知识库标记,返回空列表
                self.logger.info(f"无知识库标记")
                return {"type": 1, "data": {"kb_name": "园区知识库","sql_result": "1"}}

        except Exception as e:
            self.logger.error(f"Type 1 处理器异常: {str(e)}", exc_info=True)
            return {"type": 1, "data": {"error": f"Type 1 处理器异常: {str(e)}"}}

    async def _handle_type2(
        self, text_input: str, user_id: str, intent_result: IntentResult
    ) -> dict:
        """
        Type 2 处理器 - 数据库查询类意图

        集成 DaiShanSQL 模块,执行 SQL 查询

        Args:
            text_input: 用户输入
            user_id: 用户标识符
            intent_result: 意图识别结果

        Returns:
            {"type": 2, "data": {"sql_result": ...}}
        """
        self.logger.info(f"Type 2 处理器: 数据库查询, query='{text_input[:50]}...', user_id={user_id}")

        try:
            # 直接使用已导入的 server 实例
            server_instance = server

            # 从 intent_result 中提取 question 列表
            questions = []
            for res in intent_result.results:
                question_text = res.question
                # 解析 "Question: xxx\tAnswer: yyy" 格式，提取 Question 部分
                if question_text.startswith("Question: "):
                    # 分割并提取 Question 部分
                    parts = question_text.split("\tAnswer: ", 1)
                    if parts[0].startswith("Question: "):
                        extracted_question = parts[0][10:]  # 去掉 "Question: " 前缀
                        questions.append(extracted_question.strip())

            # 如果没有提取到问题，使用原始 query
            if not questions:
                questions = [text_input]

            self.logger.info(
                f"调用 DaiShanSQL, questions: {questions[:3]}... (共{len(questions)}个)"
            )

            # 调用 DaiShanSQL
            sql_result = await asyncio.to_thread(
                server_instance.get_sql_result,
                query=text_input,
                history=[],  # 使用空列表
                questions=questions,
            )

            self.logger.info(f"DaiShanSQL 查询完成")

            # DEBUG: 打印完整的 SQL 结果
            self.logger.info(f"========== SQL Result Debug ==========")
            self.logger.info(f"SQL Result 类型: {type(sql_result)}")
            self.logger.info(f"SQL Result 内容: {sql_result}")
            if isinstance(sql_result, dict):
                self.logger.info(f"SQL Result 键: {list(sql_result.keys())}")
            self.logger.info(f"======================================")

            # 直接返回 SQL 结果，不做任何处理
            return {"type": 2, "data": {"sql_result": sql_result}}

        except ImportError as ie:
            self.logger.error(f"导入 DaiShanSQL 模块失败: {str(ie)}", exc_info=True)
            return {"type": 2, "data": {"error": f"DaiShanSQL 模块未找到: {str(ie)}"}}
        except Exception as e:
            self.logger.error(f"Type 2 处理失败: {str(e)}", exc_info=True)
            return {"type": 2, "data": {"error": f"数据库查询异常: {str(e)}"}}

    def _get_kb_client(self, kb_name: str):
        """根据知识库名称获取对应的 Dify Chat 客户端"""
        if kb_name == "park" and self.park_kb_client:
            return self.park_kb_client
        elif kb_name == "enterprise" and self.enterprise_kb_client:
            return self.enterprise_kb_client
        elif kb_name == "safety" and self.safety_kb_client:
            return self.safety_kb_client
        else:
            return None

    # async def _query_dify_chat_blocking(
    #     self, client, query: str, user_id: str
    # ) -> str:
    #     """
    #     调用 Dify Chat 查询并返回同步结果

    #     Args:
    #         client: Dify Chat 客户端
    #         query: 查询文本
    #         user_id: 用户 ID

    #     Returns:
    #         查询结果字符串
    #     """
    #     try:
    #         # 调用 Dify Chat API
    #         response = client.create_chat_message(
    #             query=query,
    #             user=user_id,
    #             response_mode="blocking",
    #         )

    #         # 解析响应
    #         if hasattr(response, "answer"):
    #             return response.answer
    #         else:
    #             return str(response)

    #     except Exception as e:
    #         self.logger.error(f"Dify Chat 查询异常: {str(e)}", exc_info=True)
    #         return f"Dify Chat 查询异常: {str(e)}"
