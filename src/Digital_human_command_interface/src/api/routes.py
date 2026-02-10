"""
FastAPI 路由定义
"""

import asyncio
import json
import re
import time
import httpx
from typing import AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from src.intent_judgment import IntentResult, intent_judgment, instrcut_judgement
from src.models import ErrorResponse, IntentRequest
from dify_sdk import DaishanStreamingParser
from log_decorator import log, logger

# 创建路由器
router = APIRouter()


@log()
async def create_dify_payload(text_input: str, user_id: str, instrction:str=None) -> Dict:
    """创建 Dify API 请求体"""
    if instrction:
        return {
            "query": text_input,
            "inputs": {
                "instrction": instrction
            },
            "response_mode": "streaming",
            "user": user_id,
            "conversation_id": "",
            "auto_generate_name": True,
            "files": []
        }
    return {
        "query": text_input,
        "inputs": {},
        "response_mode": "streaming",
        "user": user_id,
        "conversation_id": "",
        "auto_generate_name": True,
        "files": []
    }


@log()
async def get_dify_headers(api_key: str) -> Dict:
    """获取 Dify API 请求头"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

# ============================================================
# 处理函数
# ============================================================

@log()
async def convert_json_to_stream(json_response: dict) -> AsyncGenerator[str, None]:
    """
    将 JSON 响应转换为 SSE 流式格式的异步生成器

    参考 dify_async_stream_generator 的实现,提供统一的 SSE 事件流格式:
    - event: start - 开始流式输出
    - event: message - 文本块输出
    - event: complete - 输出完成
    - event: end - 流结束
    - event: error - 错误信息

    Args:
        json_response: JSON 响应字典,支持以下格式:
            - {"return": "text content"} - Type 0 返回格式
            - {"result": "text content"} - Type 1 正常返回格式
            - {"error": "error message"} - 错误返回格式

    Yields:
        str: SSE 格式的事件字符串
    """
    try:
        # 检查是否为错误响应
        if "error" in json_response:
            error_msg = json_response.get("error", "未知错误")
            yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
            return

        # 提取文本内容 (支持 "return" 或 "result" 字段)
        text_content = None
        if "return" in json_response:
            text_content = json_response["return"]
        elif "result" in json_response:
            text_content = json_response["result"]

        if not text_content:
            # 空内容处理
            yield f"event: start\ndata: {json.dumps({'message': '开始流式输出'}, ensure_ascii=False)}\n\n"
            yield f"event: complete\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\n\n"
            yield f"event: end\ndata: [DONE]\n\n"
            return

        # 发送开始事件
        yield f"event: start\ndata: {json.dumps({'message': '开始流式输出'}, ensure_ascii=False)}\n\n"

        # 分块输出文本 (每块 3 字符,间隔 0.02 秒)
        chunk_size = 3
        message_id = 0
        for i in range(0, len(text_content), chunk_size):
            chunk = text_content[i : i + chunk_size]
            message_id += 1
            # 发送消息片段事件
            yield f"id: {message_id}\nevent: message\ndata: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)  # 模拟打字机效果

        # 发送完成事件
        yield f"event: complete\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\n\n"

        # 发送结束事件
        yield f"event: end\ndata: [DONE]\n\n"

    except Exception as e:
        # 异常处理
        error_msg = f"流式转换异常: {str(e)}"
        yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"


@log()
def get_enterprise_statistics() -> str:
    """
    调用 sql_introduction 获取企业统计数据，格式化为上下文字符串

    用于园区知识库查询时，先获取企业统计信息作为上下文，
    与用户问题拼接后一起发送给 Dify Chat。

    Returns:
        格式化后的企业统计信息字符串，失败时返回空字符串
    """
    try:
        import sys
        from pathlib import Path

        # 获取 DaiShanSQL 目录路径
        db_search_dir = Path(__file__).resolve().parents[3] / "DaiShanSQL"
        db_search_dir_str = str(db_search_dir)

        # 临时添加到 sys.path
        path_added = False
        if db_search_dir_str not in sys.path:
            sys.path.insert(0, db_search_dir_str)
            path_added = True

        # 导入并调用
        import importlib

        api_server_module = importlib.import_module("DaiShanSQL")
        server_instance = api_server_module.Server()

        result = server_instance.sql_introduction()

        # 清理 sys.path
        if path_added and db_search_dir_str in sys.path:
            sys.path.remove(db_search_dir_str)

        # 检查结果状态
        if result.get("数据库查询状态") != "success":
            return ""

        # 格式化结果为自然语言
        stats_parts = []
        for item in result.get("数据库查询结果", []):
            for key, value in item.items():
                if isinstance(value, list) and len(value) > 0:
                    # 提取第一个结果的值
                    first_row = value[0]
                    for field_name, field_value in first_row.items():
                        stats_parts.append(str(field_value))

        return "\n".join(stats_parts)

    except Exception as e:
        return ""

# 处理意图未识别的逻辑
@log(is_entry=True, enable_mermaid=True)
async def intent_handler_0(data: dict, user_id: str, http_request: Request):
    """
    Type 0 处理器 - 语义类意图

    处理逻辑:
    1. 提取用户 query
    2. 返回固定错误消息 "无效指令#@#@#"
    3. 使用 StreamingResponse 返回流式输出

    Args:
        data: 响应数据字典
        user_id: 用户标识符
        http_request: FastAPI Request 对象

    注意: 不再调用 Dify Chat API
    """
    query = data.get("query", "")

    # 返回固定错误消息
    error_message = "无效指令#@#@#"

    # 使用 StreamingResponse 返回流式输出
    return StreamingResponse(
        content=convert_json_to_stream({"return": error_message}),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

# 从 answer 字符串中提取 instruction (知识库标记之前的内容)
@log()
def extract_instruction(answer: str) -> str:
    """
    从 answer 字符串中提取 instruction (知识库标记之前的内容)

    提取逻辑:
    1. 使用正则表达式匹配 'instruction内容 [knowledgebase:xxx]' 格式
    2. 返回标记之前的内容作为 instruction
    3. 清理末尾的空格和特殊字符

    Args:
        answer: 完整的 answer 字符串,可能包含 [knowledgebase:xxx] 标记

    Returns:
        str: 提取的 instruction 字符串,如果没有标记则返回空字符串

    Example:
        >>> extract_instruction("【global+parkSafetySituation #@#@# [knowledgebase:园区知识库】")
        "【global+parkSafetySituation #@#@# "
        >>> extract_instruction("无标记的普通文本")
        ""
    """
    # 匹配模式: instruction内容 [knowledgebase:xxx]
    # 使用非贪婪匹配 (.+?) 确保只提取到第一个标记之前的内容
    pattern = r"^(.+?)(\[[Kk]nowledgebase:[^\]]+\])"
    match = re.search(pattern, answer)

    if match:
        instruction = match.group(1)
        # 清理末尾的空格
        return instruction.rstrip()
    else:
        # 没有找到知识库标记
        return ""

# 处理意图为【指令集】的逻辑
@log(is_entry=True, enable_mermaid=True)
async def intent_handler_1(data: dict, user_id: str, http_request: Request):
    """
    Type 1 处理器 - 明确指令类

    处理逻辑:
    1. 读取 results[0] 中的 answer 字段
    2. 检查是否包含 [knowledgebase:表名] 标记
    3. 如果包含,提取标记之前的部分作为 instruction
    4. 调用 Dify Chat 的 run_chat_streaming,直接转发 SSE 流式输出

    Args:
        data: 响应数据字典
        user_id: 用户标识符
        http_request: FastAPI Request 对象

    支持的知识库表名:
    - 园区知识库 → park_kb_client
    - 企业知识库 → enterprise_kb_client
    - 安全信息知识库 → safety_kb_client

    流式输出策略:
    - 使用 Dify Chat 的原生 SSE 流式输出,不再使用 convert_json_to_stream
    - 通过 inputs={"instruction": instruction} 传递指令内容
    - 直接转发 Dify Chat 的 SSE 事件,确保零延迟的流式体验

    降级策略:
    - Dify Chat 客户端未初始化或调用失败 → 记与其他 error 日志,返回错误流
    """
    # 从 app.state 获取资源
    park_kb_client = getattr(http_request.app.state, 'park_kb_client', None)
    enterprise_kb_client = getattr(http_request.app.state, 'enterprise_kb_client', None)
    safety_kb_client = getattr(http_request.app.state, 'safety_kb_client', None)

    try:
        # 检查 results 数组
        results = data.get("results", [])
        if not results:
            return StreamingResponse(
                content=convert_json_to_stream({"error": "No results found"}),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                },
            )

        # 获取第一个结果
        first_result = results[0]

        # 提取 answer 字段
        question = first_result.get("question", "")

        # 解析 answer (格式: "Question: xxx\tAnswer: yyy")
        answer = None
        if "\tAnswer: " in question:
            parts = question.split("\tAnswer: ", 1)
            if len(parts) == 2:
                answer = parts[1]

        if not answer:
            answer = "无效指令#@#@#"

        # 检查是否包含 [knowledgebase:表名] 标记
        kb_pattern = r"\[knowledgebase:([^\]]+)\]"
        kb_matches = re.findall(kb_pattern, answer)

        if not kb_matches:
            # 不包含知识库标记,直接返回 answer
            return StreamingResponse(
                content=convert_json_to_stream({"result": answer}),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                },
            )

        # 包含知识库标记,使用 Dify Chat 查询

        # 知识库名称到 Dify Chat 客户端的映射
        KB_TO_CLIENT = {
            "园区知识库": ("park_kb_chat", park_kb_client),
            "企业知识库": ("enterprise_kb_chat", enterprise_kb_client),
            "安全信息知识库": ("safety_kb_chat", safety_kb_client),
        }

        # 提取 instruction (知识库标记之前的内容)
        instruction = extract_instruction(answer)

        # 使用第一个知识库对应的 Dify Chat 客户端进行流式输出
        # 注意: 只使用第一个知识库的客户端,因为 Dify 会处理完整输入
        first_kb_name = kb_matches[0] if kb_matches else None
        if first_kb_name:
            client_info = KB_TO_CLIENT.get(first_kb_name)
            if client_info and client_info[1]:
                client_name, client = client_info

                # 获取用户查询
                user_query = data.get("query", "")

                # 创建流式输出生成器,直接转发 Dify Chat 的 SSE 事件
                async def event_generator():
                    """生成 SSE 事件流,使用 DaishanStreamingParser 转换为统一格式"""
                    try:
                        # 确定最终发送给 Dify 的 query
                        final_query = user_query

                        # 如果是企业知识库，先获取企业统计数据并拼接
                        if first_kb_name == "企业知识库":
                            enterprise_stats = get_enterprise_statistics()
                            if enterprise_stats:
                                final_query = f"""用户问题：{user_query}

以下是园区企业的统计信息供参考：
{enterprise_stats}"""
                            else:
                                pass

                        # 调用 Dify Chat 流式接口

                        # 创建 DaishanStreamingParser，自动转换为统一格式
                        parser = DaishanStreamingParser(chunk_size=3, chunk_delay=0.02)

                        # 空值检查
                        if client is None:
                            yield f"event: error\ndata: {json.dumps({'error': 'Client not initialized'}, ensure_ascii=False)}\n\n"
                            return

                        for event in client.run_chat_streaming(
                            query=final_query,
                            user=user_id,  # 使用传入的 user_id
                            inputs=(
                                {"instruction": instruction} if instruction else None
                            ),
                            parser=parser,  # 传递新解析器
                        ):
                            # 直接透传（已经是统一格式）
                            yield event

                    except Exception as e:
                        # 发送错误事件
                        yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

                # 返回流式响应
                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                        "Access-Control-Allow-Origin": "*",
                    },
                )
            else:
                # 客户端未初始化,使用降级方案
                return StreamingResponse(
                    content=convert_json_to_stream({"error": "知识库客户端未初始化"}),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                        "Access-Control-Allow-Origin": "*",
                    },
                )
        else:
            # 没有知识库标记(理论不应走到这里),使用原有逻辑
            return StreamingResponse(
                content=convert_json_to_stream({"result": answer}),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                },
            )

    except Exception as e:
        return StreamingResponse(
            content=convert_json_to_stream({"error": f"处理失败: {str(e)}"}),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )

# 将 SQL 查询结果格式化为 Dify Chat 的 query 参数
@log()
def format_sql_result_as_query(original_query: str, sql_result: dict) -> str:
    """
    将 SQL 查询结果格式化为 Dify Chat 的 query 参数

    设计思路:
    1. 提取用户原始问题
    2. 格式化 SQL 查询结果(JSON 美化)
    3. 构建 prompt 模板,引导 LLM 总结数据

    Args:
        original_query: 用户原始查询 (如 "岱山园区有多少企业?")
        sql_result: DaiShanSQL 返回的结果
            可能的格式:
            格式1 (DaiShanSQL 实际返回):
                {"数据库查询": "SELECT ...", "数据库查询结果": [[{...}]]}
            格式2 (旧格式兼容):
                {"数据库查询结果": [[{...}]], "query": "用户问题"}
            格式3:
                {"sql": "...", "result": [...], "message": "..."}
            格式4:
                {"code": 200, "msg": "...", "data": [...], "sql": "..."}

    Returns:
        str: 格式化后的 prompt
    """
    import json

    # 1. 提取查询结果数据 - 兼容多种格式
    result_data = []
    sql_query = ""
    message = ""

    # 尝试多种可能的键名（按优先级）
    if "数据库查询结果" in sql_result:
        # DaiShanSQL 实际返回的格式
        result_data = sql_result["数据库查询结果"]
        # 新格式使用 '数据库查询' 键存储 SQL，旧格式使用 'query'
        sql_query = sql_result.get("数据库查询", "")
        message = sql_result.get("query", "")
    elif "result" in sql_result:
        # 格式1: 直接包含 'result' 字段
        result_data = sql_result["result"]
        sql_query = sql_result.get("sql", "")
        message = sql_result.get("message", "")
    elif "data" in sql_result:
        # 格式2: 包含 'data' 字段
        result_data = sql_result["data"]
        sql_query = sql_result.get("sql", "")
        message = sql_result.get("msg", "")

    # 如果是嵌套的列表结构（如 [[{...}]]），展平它
    if isinstance(result_data, list) and len(result_data) > 0:
        if isinstance(result_data[0], list):
            # [[{...}, {...}]] -> [{...}, {...}]
            result_data = result_data[0]

    # 2. 格式化 JSON(美化输出,确保中文可读)
    formatted_result = json.dumps(
        result_data, ensure_ascii=False, indent=2  # 保留中文  # 缩进美化
    )

    # 3. 构建 prompt 模板
    # 如果有 SQL 查询语句，显示这部分（DaiShanSQL 返回的 '数据库查询' 字段）
    sql_section = f"\n执行的 SQL 查询:\n{sql_query}\n\n" if sql_query else ""

    prompt = f"""用户问题: {original_query}
{sql_section}查询结果:
{formatted_result}

请基于以上查询结果,用简洁自然的语言回答用户问题。要求:
1. 如果结果是列表,总结关键信息(数量、主要内容等)
2. 如果是统计数据,重点说明数字含义
3. 如果结果为空,礼貌地告知用户
4. 回答简洁明了,不要重复问题
5. 直接给出答案,不需要过度解释
"""

    return prompt

# 处理意图为【数据视图】的逻辑
@log(is_entry=True, enable_mermaid=True)
async def intent_handler_2(data: dict, user_id: str, http_request: Request):
    """
    Type 2 处理器 - 数据库查询类意图

    集成 DaiShanSQL 模块,执行 SQL 查询

    Args:
        data: 响应数据字典
        user_id: 用户标识符
        http_request: FastAPI Request 对象

    新流程:
    1. 调用 DaiShanSQL 获取 SQL 查询结果
    2. 使用 Dify Chat 将结果格式化为自然语言
    3. 返回友好的自然语言回答

    降级策略:
    - Dify Chat 客户端未初始化 → 返回原始结果
    - Dify Chat 调用失败 → 返回原始结果
    """
    # 从 app.state 获取资源
    dify_chat_client = getattr(http_request.app.state, 'dify_chat_client', None)

    try:
        # 导入 DaiShanSQL 模块
        # 注意: api_server.py 使用相对导入,需要临时调整 sys.path
        try:
            import sys
            from pathlib import Path

            # 获取 DaiShanSQL 目录的绝对路径
            # routes.py 位于 src/api/,需要向上两级到 src/,然后进入 DaiShanSQL/
            # 注意: 包内使用 from DaiShanSQL.xxx 导入，所以需要添加父目录
            db_search_dir = Path(__file__).resolve().parents[3] / "DaiShanSQL"
            db_search_dir_str = str(db_search_dir)

            # 临时添加到 sys.path
            path_added = False
            if db_search_dir_str not in sys.path:
                sys.path.insert(0, db_search_dir_str)
                path_added = True

            # 导入 api_server 模块
            # 由于 DaiShanSQL 父目录在 sys.path 中,使用包名导入
            import importlib

            api_server_module = importlib.import_module("DaiShanSQL")
            # 创建 Server 实例
            server_instance = api_server_module.Server()

            # 提取查询信息
            query = data.get("query", "")
            # history 已从 API 中移除,使用空列表
            history_list = []

            # 从 results 中提取 question 列表
            # 注意：results 包含意图识别返回的相似问题列表
            results = data.get("results", [])

            # 提取 Question 部分（格式: "Question: xxx\tAnswer: yyy"）
            questions = []
            for res in results:
                question_text = res.get("question", "")  # 注意是小写 'question'
                # 解析 "Question: xxx\tAnswer: yyy" 格式，提取 Question 部分
                if question_text.startswith("Question: "):
                    # 分割并提取 Question 部分
                    parts = question_text.split("\tAnswer: ", 1)
                    if parts[0].startswith("Question: "):
                        extracted_question = parts[0][10:]  # 去掉 "Question: " 前缀
                        questions.append(extracted_question.strip())

            # 如果没有提取到问题，使用原始 query
            if not questions:
                questions = [query]

            # ======== Step 1: 调用 DaiShanSQL (保持原有逻辑) ========
            loop = asyncio.get_event_loop()
            sql_result = await loop.run_in_executor(
                None,
                lambda: server_instance.get_sql_result(
                    query=query,
                    history=history_list,  # 参数名是 history，但传递 conversation 格式
                    questions=questions,
                ),
            )


            # ======== DEBUG: 打印完整的 SQL 结果 ========

            # 清理: 如果是我们添加的路径,从 sys.path 中移除
            if path_added and db_search_dir_str in sys.path:
                sys.path.remove(db_search_dir_str)

            # ======== Step 2: 尝试使用 Dify Chat 包装结果 ========
            if dify_chat_client:
                try:

                    # 格式化 SQL 结果为 prompt
                    formatted_query = format_sql_result_as_query(
                        original_query=query, sql_result=sql_result
                    )

                    # 流式输出生成器
                    async def event_generator():
                        """生成 SSE 事件流,使用 DaishanStreamingParser 转换为统一格式"""
                        try:
                            # 创建 DaishanStreamingParser，自动转换为统一格式
                            parser = DaishanStreamingParser(chunk_size=3, chunk_delay=0.02)

                            # 空值检查
                            if dify_chat_client is None:
                                yield f"event: error\ndata: {json.dumps({'error': 'Dify Chat client not initialized'}, ensure_ascii=False)}\n\n"
                                return

                            for event in dify_chat_client.run_chat_streaming(
                                query=formatted_query,
                                user=user_id,  # 使用传入的 user_id
                                parser=parser,  # 传递新解析器
                            ):
                                # 直接透传（已经是统一格式）
                                yield event
                        except Exception as e:
                            # 发送错误事件
                            error_data = {"event": "error", "message": str(e)}
                            yield f"data: {json.dumps(error_data)}\n\n"

                    # 返回流式响应
                    return StreamingResponse(
                        event_generator(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                        },
                    )

                except Exception as e:
                    pass
            else:
                pass

            # ======== Step 3: 降级 - 返回原始 SQL 结果 ========
            # 将 SQL 结果转换为字符串并用流式返回
            result_str = json.dumps(sql_result, ensure_ascii=False)
            return StreamingResponse(
                content=convert_json_to_stream({"result": result_str}),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                },
            )

        except ImportError as ie:
            return StreamingResponse(
                content=convert_json_to_stream(
                    {"error": f"DaiShanSQL 模块未找到: {str(ie)}"}
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                },
            )

    except Exception as e:
        return StreamingResponse(
            content=convert_json_to_stream({"error": f"处理失败: {str(e)}"}),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )


# 流式聊天生成器函数
@log()
async def dify_async_stream_generator(
    text_input: str,
    user_id: str,
    http_client: httpx.AsyncClient,
    config,
    api_key:str=None,
    instruction_type:str=None
) -> AsyncGenerator[str, None]:
    """异步生成器：处理 Dify API 流式响应并生成标准SSE格式输出"""
    try:
        # 从配置读取参数
        if not api_key:
            api_key = config.stream_chat_api_key
        base_url = config.stream_chat_base_url
        endpoint = config.stream_chat_endpoint
        max_retry = config.stream_chat_max_retry
        retry_delay = config.stream_chat_retry_delay

        # 构建请求参数
        headers = await get_dify_headers(api_key)
        payload = await create_dify_payload(text_input, user_id, instruction_type)
        url = f"{base_url}{endpoint}"

        start_time = time.time()
        first_output_sent = False
        retry_count = 0

        while retry_count <= max_retry:
            try:
                async with http_client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        error_detail = await response.text()
                        error_msg = f"Dify API请求失败，状态码: {response.status_code}, 响应: {error_detail[:200]}"
                        yield f"event: error\\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\\n\\n"
                        break
                    yield f"event: start\\ndata: {json.dumps({'message': '开始流式输出'}, ensure_ascii=False)}\\n\\n"
                    print(f"response: {response}")

                    message_id = 0
                    async for line in response.aiter_lines():
                        # print(f"line: {line}")
                        if not first_output_sent and (time.time() - start_time > 15):
                            timeout_data = {
                                "code": 1,
                                "message": "当前网络异常，请稍后再试。",
                                "data": {
                                    "answer": "当前网络异常，请稍后再试。",
                                    "flag": 1,
                                    "wordId": message_id,
                                    "end": 0
                                }
                            }
                            yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\\n\\n"
                            timeout_data1 = {
                                "code": 1,
                                "data": {
                                    "answer": "",
                                    "flag": 0,
                                    "wordId": message_id+1,
                                    "end": 1
                                }
                            }
                            yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\\n\\n"
                            return

                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line.lstrip("data: ").strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError as e:
                            warn_msg = f"解析流式数据失败: {str(e)}, 原始数据: {data_str[:100]}"
                            yield f"event: warning\\ndata: {json.dumps({'warning': warn_msg}, ensure_ascii=False)}\\n\\n"
                            continue
                        
                        # print(f"data: {data}")
                        event_type = data.get("event")

                        # 处理流式模式：从 message 事件中提取答案片段
                        if event_type == "message":
                            answer_chunk = data.get("answer", "")
                            if answer_chunk:
                                # 优化打字机效果：批量处理字符，减少yield次数
                                if not first_output_sent:
                                    first_output_sent = True

                                if not first_output_sent and time.time() - start_time > 15:
                                    timeout_data = {
                                        "code": 1,
                                        "message": "当前网络异常，请稍后再试。",
                                        "data": {
                                                "answer": "当前网络异常，请稍后再试。",
                                                "flag": 1,
                                                "wordId": message_id,
                                                "end": 0
                                            }
                                    }
                                    yield f"data: {json.dumps(timeout_data, ensure_ascii=False)}\n\n"
                                    timeout_data1 = {
                                        "code": 1,
                                        "data": {
                                                "answer": "",
                                                "flag": 0,
                                                "wordId": message_id+1,
                                                "end": 1
                                            }
                                    }
                                    yield f"data: {json.dumps(timeout_data1, ensure_ascii=False)}\n\n"
                                    return
                                chunk_size = 3  # 每次输出3个字符
                                for i in range(0, len(answer_chunk), chunk_size):
                                    chunk = answer_chunk[i:i+chunk_size]
                                    message_id += 1
                                    # 发送消息片段事件
                                    yield f"id: {message_id}\nevent: message\ndata: {json.dumps({'content': chunk, 'type': 'chunk'}, ensure_ascii=False)}\n\n"
                                    await asyncio.sleep(0.02)  # 调整延迟时间

                        elif event_type == "message_end":
                            yield f"event: complete\\ndata: {json.dumps({'message': '流式输出已完成'}, ensure_ascii=False)}\\n\\n"
                            break

                        elif event_type == "error":
                            print(f"6.3")
                            error_msg = f"Dify API流式处理错误: {data.get('message', '未知错误')}"
                            yield f"event: error\\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\\n\\n"
                            break
                        
                    yield f"event: end\\ndata: [DONE]\\n\\n"
                    break

            except httpx.TimeoutException:
                retry_count += 1
                if retry_count > max_retry:
                    error_msg = f"请求超时，已重试{max_retry}次仍失败"
                    yield f"event: error\\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\\n\\n"
                    break
                await asyncio.sleep(retry_delay * retry_count)

            except httpx.RequestError as e:
                error_msg = f"请求发生错误: {str(e)[:150]}"
                yield f"event: error\\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\\n\\n"
                break

    except Exception as e:
        error_msg = f"处理请求时发生异常: {str(e)[:150]}"
        yield f"event: error\\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\\n\\n"

# 处理指令判断函数
@log(is_entry=True, enable_mermaid=True)
async def instruct_process(query:str, http_request: Request):
    # 从 app.state 获取资源
    ragflow_client = getattr(http_request.app.state, 'ragflow_client', None)
    config_manager = getattr(http_request.app.state, 'config_manager', None)

    # 空值检查
    if ragflow_client is None or config_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "服务未完全初始化",
                "suggestion": "请联系管理员",
            },
        )

    try:
        # 执行意图判断
        result: IntentResult = await instrcut_judgement(
            query=query,
            client=ragflow_client,
            config=config_manager.get_config(),
        )

        # 构建 QueryResult 列表
        from src.models import QueryResult

        results_list = [
            QueryResult(question=r.question, similarity=r.similarity)
            for r in result.results
        ]

        # 根据路由到对应的处理器
        intent_type = result.type

        # 构建完整的响应数据结构
        response_data = {
            "type": intent_type,
            "query": result.query,
            "results": [
                {"question": r.question, "similarity": r.similarity}
                for r in results_list
            ],
        }

        # 路由到对应的处理器
        if intent_type == 1:
            # 检查 results 数组
            results = response_data.get("results", [])
            # 获取第一个结果
            first_result = results[0]
            # 提取 answer 字段
            question = first_result.get("question", "")
            # 解析 answer (格式: "Question: xxx\tAnswer: yyy")
            answer = None
            if "\tAnswer: " in question:
                parts = question.split("\tAnswer: ", 1)
                if len(parts) == 2:
                    answer = parts[1]
            if not answer:
                return {
                    "answer": "无效指令#@#@#",
                    "chat_type": "normal_instruct"
                }

            # 检查是否包含 [knowledgebase:表名] 标记
            kb_pattern = r"\[knowledgebase:([^\]]+)\]"
            kb_matches = re.findall(kb_pattern, answer)

            if not kb_matches:
                # 不包含知识库标记,直接返回 answer
                return {
                    "answer": answer,
                    "chat_type": "normal_instruct"
                }

            # 包含知识库标记,使用 Dify Chat 查询
            first_kb_name = kb_matches[0] if kb_matches else None

            # 提取 instruction (知识库标记之前的内容)
            instruction = extract_instruction(answer)
        else:
            return {
                "answer": instruction,
                "chat_type": first_kb_name,
            }

    except HTTPException:
        return {
            "answer": "无效指令#@#@#",
            "chat_type": "normal_instruct"
        }
    

# ============================================================
# 路由定义
# ============================================================

@router.get("/", tags=["根路径"])
@log(is_entry=True, enable_mermaid=True)
async def root(request: Request):
    """根路径"""
    app_start_time = getattr(request.app.state, 'start_time', time.time())
    return {
        "service": "岱山意图识别服务",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": time.time() - app_start_time,
    }


@router.get("/health", tags=["健康检查"])
@log(is_entry=True, enable_mermaid=True)
async def health_check(request: Request):
    """健康检查接口"""
    ragflow_client = getattr(request.app.state, 'ragflow_client', None)

    # 空值检查
    if ragflow_client is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "checks": {
                    "ragflow": {
                        "status": "pass" if ragflow_client is not None else "fail",
                        "description": "RAGFlow client"
                    }
                }
            }
        )

    health_status = {"status": "healthy", "timestamp": time.time(), "checks": {}}

    # 检查 RAGFlow 连接
    try:
        ragflow_ok = ragflow_client.test_connection()
        health_status["checks"]["ragflow"] = {
            "status": "pass" if ragflow_ok else "fail",
            "description": "RAGFlow service connection",
        }
        if not ragflow_ok:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["ragflow"] = {
            "status": "fail",
            "description": f"RAGFlow connection error: {str(e)}",
        }
        health_status["status"] = "unhealthy"

    # 返回适当的 HTTP 状态码
    status_code = 200
    if health_status["status"] == "degraded":
        status_code = 200
    elif health_status["status"] == "unhealthy":
        status_code = 503

    return JSONResponse(content=health_status, status_code=status_code)


# 意图识别
@router.post(
    "/intent",
    responses={400: {"model": ErrorResponse}, 200: {"model": ErrorResponse}},
    tags=["意图识别"],
)
@log(is_entry=True, enable_mermaid=True)
async def intent_recognition(request: IntentRequest, http_request: Request):
    """
    意图识别接口 - 路由分发器

    接收用户查询和用户标识,根据 type 值路由到对应的子接口。

    - **text_input**: 用户查询文本 (1-1000 字符)
    - **user_id**: 用户标识符 (1-100 字符)

    返回:
    - 所有类型都返回 StreamingResponse (SSE 流式格式)
    - 根据 type 值转发到对应处理器:
      - type=0: intent_handler_0 (语义类)
      - type=1: intent_handler_1 (明确指令类)
      - type=2: intent_handler_2 (数据库查询类)
    """
    # 从 app.state 获取资源
    ragflow_client = getattr(http_request.app.state, 'ragflow_client', None)
    config_manager = getattr(http_request.app.state, 'config_manager', None)

    # 空值检查
    if ragflow_client is None or config_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "服务未完全初始化",
                "suggestion": "请联系管理员",
            },
        )

    try:
        # 执行意图判断
        result: IntentResult = await intent_judgment(
            query=request.text_input,
            client=ragflow_client,
            config=config_manager.get_config(),
        )

        # 构建 QueryResult 列表
        from src.models import QueryResult

        results_list = [
            QueryResult(question=r.question, similarity=r.similarity)
            for r in result.results
        ]

        # 根据路由到对应的处理器
        intent_type = result.type

        # 构建完整的响应数据结构
        response_data = {
            "type": intent_type,
            "query": result.query,
            "results": [
                {"question": r.question, "similarity": r.similarity}
                for r in results_list
            ],
        }

        # 路由到对应的处理器
        # 确保 user_id 不为 None（使用 "anonymous" 作为默认值）
        user_id = request.user_id or "anonymous"
        if intent_type == 0:
            response = await intent_handler_0(response_data, user_id, http_request)
        elif intent_type == 1:
            response = await intent_handler_1(response_data, user_id, http_request)
        elif intent_type == 2:
            response = await intent_handler_2(response_data, user_id, http_request)
        else:
            # 未知的 type,直接返回原始数据
            response = JSONResponse(content=response_data)

        return response

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "服务内部错误",
                "suggestion": "请稍后重试或联系管理员",
            },
        )

# 流式聊天
@router.post(
    "/api/stream-chat",
    summary="流式聊天接口（标准SSE格式）",
    description="接收text_input，返回标准SSE格式的流式输出",
    response_class=StreamingResponse
)
@log(is_entry=True, enable_mermaid=True)
async def instrcution_command(input_data: IntentRequest, request: Request):
    """
    示例请求体：
    {
        "text_input": "请介绍贵公司",
        "user_id": "user_001"  // 可选，默认 fastapi_client_user
    }
    
    SSE事件格式：
    - event: start - 开始流式输出
    - event: message - 消息内容片段 (data: {"content": "文本片段", "type": "chunk"})
    - event: complete - 流式输出完成
    - event: error - 错误信息
    - event: warning - 警告信息
    - event: end - 流结束 (data: [DONE])
    """
    # 校验输入
    if not input_data.text_input.strip():
        raise HTTPException(status_code=400, detail="text_input 字段不能为空")
    
    # 从应用状态获取HTTP客户端
    http_client = request.app.state.http_client

    ragflow_client = getattr(request.app.state, 'ragflow_client', None)
    config_manager = getattr(request.app.state, 'config_manager', None)
    config=config_manager.get_config()

    # 空值检查
    if ragflow_client is None or config_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "服务未完全初始化",
                "suggestion": "请联系管理员",
            },
        )

    # 执行意图判断
    result: IntentResult = await intent_judgment(
        query=input_data.text_input,
        client=ragflow_client,
        config=config_manager.get_config(),
        databases=["岱山-指令集-260129"]
    )

    answer = "无效指令#@#@#"
    if len(result.results) > 0:
        best_result = result.results[0]
        print(f"指令最大相似度为：{result.similarity}\n指令为：{best_result.question}")
        if result.similarity >= config.similarity_threshold:
            # 提取 answer 字段
            question = best_result.question
            # 解析 answer (格式: "Question: xxx\tAnswer: yyy")
            if "\tAnswer: " in question:
                parts = question.split("\tAnswer: ", 1)
                if len(parts) == 2:
                    answer = parts[1]

    
    # 返回流式响应
    return StreamingResponse(
        content=dify_async_stream_generator(
            text_input=input_data.text_input.strip(),
            user_id=input_data.user_id.strip(),
            http_client=http_client,
            config=config,
            instruction_type=answer
        ),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
