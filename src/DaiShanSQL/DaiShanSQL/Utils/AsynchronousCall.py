from dotenv import load_dotenv, find_dotenv
import asyncio
import sys
from openai import AsyncOpenAI
import os
import time
import traceback
from tqdm import tqdm
from .Prompt_Templete import Prompt_Templete

# ========== 核心修复：Windows 异步事件循环适配 ==========
# 修复 Windows 下 asyncio 事件循环关闭报错问题
if sys.platform == 'win32':
    # 切换到更稳定的 Selector 事件循环策略
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 可选：重写析构函数，彻底屏蔽报错（双重保障）
    from asyncio.proactor_events import _ProactorBasePipeTransport
    original_del = _ProactorBasePipeTransport.__del__
    def new_del(self):
        try:
            original_del(self)
        except (RuntimeError, AttributeError):
            pass
    _ProactorBasePipeTransport.__del__ = new_del

# 加载环境变量
_ = load_dotenv(find_dotenv())

class AsynchronousCall:
    def __init__(self):
        self.chat_client = AsyncOpenAI(
            base_url=os.getenv("Qwen2.5_7B_base_url"),
            api_key=os.getenv("Qwen2.5_7B_api_key"),
        )
        self.sql_client = AsyncOpenAI(
            base_url=os.getenv("TextToSQL_base_url"),
            api_key=os.getenv("TextToSQL_api_key"),
        )
        self.prompt_utils = Prompt_Templete()

    async def process_query_detiled_item(self, query_dict):
        try:
            prompt = query_dict['user_query']
            query_conversation = [{"role": "user", "content": prompt}]
            # start_time = time.time()
            
            # 异步调用 OpenAI API
            new_prompt_response = await self.chat_client.chat.completions.create(
                model=os.getenv("Qwen2.5_7B_model"),
                messages=query_conversation,
                max_tokens=100,
                temperature=0.1,
                extra_body={"enable_thinking": False}
            )
            result_content = new_prompt_response.choices[0].message.content
            # print(f"\033[34m当前提问时间消耗：{time.time() - start_time}\033[0m")
            return True, {**query_dict, "result": result_content}

        except Exception as e:
            print(f"处理单个查询失败: {traceback.format_exc()}")
            return False, {}

    async def process_response_sql_item(self, query_dict):
        try:
            prompt = query_dict['user_query']
            query_conversation = [{"role": "user", "content": prompt}]
            
            # 异步调用 SQL 生成 API
            new_prompt_response = await self.sql_client.chat.completions.create(
                model=os.getenv("TextToSQL_model"),
                temperature=0.1,
                messages=query_conversation
            )
            result_content = new_prompt_response.choices[0].message.content
            return True, {**query_dict, "result": result_content}

        except Exception as e:
            print(f"生成 SQL 失败: {traceback.format_exc()}")
            return False, {}

    async def process_batch(self, data_batch, semaphore, mode):
        """处理一个数据批次，通过信号量控制并发"""
        async with semaphore:
            tasks = []
            for dd in data_batch:
                if mode == "change_query":
                    task = self.process_query_detiled_item(dd)
                elif mode == "response_sql":
                    task = self.process_response_sql_item(dd)
                tasks.append(task)

            # 异步执行所有任务并收集结果
            results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 统计成功数量
            successful_count = sum(1 for success, _ in results if success)
            return successful_count, results

    async def async_agent_eval(self, data, mode, batch_size=5, max_concurrent=3):
        """异步代理评估主函数，分批次处理数据"""
        total_count = len(data)
        if total_count == 0:
            return 0, 0, []
            
        # 创建信号量限制并发批次数量
        semaphore = asyncio.Semaphore(max_concurrent)
        now_count = 0
        total_successful = 0
        final_results = []
        
        while now_count < total_count:
            end_idx = min(now_count + batch_size, total_count)
            batch = data[now_count:end_idx]
            start_time = time.time()
            try:
                # 处理当前批次
                successful_count, results = await self.process_batch(
                    batch, semaphore, mode
                )
                
                # 更新结果和统计
                final_results.extend(results)
                total_successful += successful_count
                batch_processed = len(batch)
                now_count += batch_processed
                
                # 打印当前进度
                progress = now_count / total_count * 100
                # 轻微延迟，避免高频请求触发 API 限流
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"批次处理错误 (位置 {now_count}-{end_idx}): {traceback.format_exc()}")
                # 失败批次也标记为已处理，避免死循环
                now_count += len(batch)
                # 打印错误批次的进度
                progress = now_count / total_count * 100
                print(f"进度: {now_count}/{total_count} ({progress:.1f}%) - 批次 {now_count}-{end_idx} 处理失败")
                continue
        
        # print(f"\033[32m处理完成 ({mode})！总计成功: {total_successful}/{total_count} 条，总耗时: {time.time() - start_time:.2f} 秒\033[0m")
        return total_successful, total_count, final_results

    async def Agent_eval_async(self, query_data, mode):
        """异步版本的Agent评估函数，封装参数并执行"""
        batch_size = 5
        max_concurrent = 5
        successful, total, final_results = await self.async_agent_eval(
            query_data, mode, batch_size=batch_size, max_concurrent=max_concurrent
        )
        # 过滤出成功的结果
        return [data for success, data in final_results if success]

    # ========== 修复同步调用异步函数的逻辑 ==========
    def _run_async_safely(self, coro):
        """安全执行异步函数的封装方法，适配 Windows 事件循环"""
        try:
            # 获取当前线程的事件循环，如果没有则创建新的
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # 没有现有循环，创建新循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # 运行协程并获取结果
            return loop.run_until_complete(coro)
        finally:
            # 安全关闭事件循环（先清理任务）
            try:
                # 取消所有未完成的任务
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                    try:
                        loop.run_until_complete(task)
                    except asyncio.CancelledError:
                        pass
            finally:
                loop.close()

    def ProcessQuerys(self, query, table_info):
        """处理查询提示词生成，同步接口"""
        query_prompt_list = []
        for tt in table_info:
            new_prompt = self.prompt_utils.fixQuerys(query, tt)
            query_prompt_list.append({"user_query": new_prompt, "table": tt})
        
        # 使用安全的异步执行方法替代直接的 asyncio.run()
        new_prompt_result = self._run_async_safely(
            self.Agent_eval_async(query_prompt_list, mode="change_query")
        )
        return new_prompt_result

    def replace_sql_asterisk(self, sql_list):
        processed_list = []
        for item in sql_list:
            new_item = item.copy()
            sql_content = new_item['result']
            if 'count' not in sql_content.lower():
                tableInfo = item["table"]['列名信息']
                field = ",".join(str(i) for i in tableInfo)
                new_item['result'] = sql_content.replace('*', field)
            
            processed_list.append(new_item)
        return processed_list
    
    def ProcessSQL(self, query, prompts):
        """处理 SQL 生成，同步接口"""
        new_sql_prompt = []
        for new_prompt in prompts:
            new_user_query = new_prompt["result"]
            # 刚用户初始问题与修正后问题一致，则表明chat模型无法对其进行补充，因此判定该问题无效，需要跳过
            if str(new_user_query)==str(query):
                continue
            table = new_prompt["table"]
            sql_query = self.prompt_utils.gengerate_sql(new_user_query, table)
            new_sql_prompt.append({
                "user_query": sql_query, 
                "table": table,
                "origin_user_query": new_user_query
            })
        
        # 使用安全的异步执行方法
        new_sql_result = self._run_async_safely(
            self.Agent_eval_async(new_sql_prompt, mode="response_sql")
        )
        result_list = self.replace_sql_asterisk(new_sql_result)
        return result_list


# ========== 测试示例（可选） ==========
if __name__ == "__main__":
    # 示例用法
    async_call = AsynchronousCall()
    
    # 测试 ProcessQuerys
    # test_query = "查询用户订单数据"
    # test_tables = ["order_table", "user_table"]
    # query_results = async_call.ProcessQuerys(test_query, test_tables)
    # print(f"查询处理结果: {query_results}")
    
    # 测试 ProcessSQL
    # test_prompts = [{"result": "查询2024年订单", "table": "order_table"}]
    # sql_results = async_call.ProcessSQL("查询用户订单数据", test_prompts)
    # print(f"SQL 生成结果: {sql_results}")