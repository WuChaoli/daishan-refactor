import json
import requests
import logging
from requests.exceptions import RequestException

# 配置日志
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def send_stream_request():
    # 构建请求体
    request_body = {
        "question": "什么是安全生产法规",
        "stream": True,
        "session_id": "95375ce8826a11f088630242ac140003"
    }
    
    url = "http://192.168.188.3:8081/api/v1/chats/1b0abaca824a11f0bc900242ac140003/completions"
    
    # 设置请求头
    headers = {
        "Accept": "text/event-stream",
        "Authorization": "Bearer ragflow-U5NzEwM2MyNzhmMTExZjA5NDRhNjI0YW",
        "Content-Type": "application/json"
    }
    
    try:
        # 发送POST请求，stream=True表示流式响应
        with requests.post(
            url,
            headers=headers,
            json=request_body,
            stream=True,
            timeout=(10, None)  # 连接超时10秒，读取超时None（无限制）
        ) as response:
            
            response.raise_for_status()  # 检查HTTP错误状态码
            
            old_answer = ""
            word_id = 0
            
            print("📡 开始接收流式数据...")
            print("-" * 50)
            
            # 迭代处理流式响应
            for line in response.iter_lines(decode_unicode=True):
                if line:  # 跳过空行
                    # 处理数据行
                    if line.startswith("data:"):
                        line = line.replace("data:", "", 1).strip()
                        
                        try:
                            json_object = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        # 解析JSON数据
                        data = json_object.get("data")
                        if not data:
                            continue
                        
                        # 检查是否是结束标志
                        if data is True:
                            print("-" * 50)
                            print(f"[end=1] 流式传输结束")
                            print(f"📊 传输统计: 总块数 {word_id}, 最终长度 {len(old_answer)} 字符")
                            
                            # 创建结束标志的数据对象
                            end_body = {
                                "sessionId": request_body["session_id"],
                                "answer": "",  # 结束时不包含新内容
                                "flag": 1,
                                "wordId": word_id,
                                "end": 1  # 1表示传输结束
                            }
                            
                            # 这里可以添加推送逻辑
                            # sse_data_service.push_data(end_body)
                            print(f"📤 发送结束标志: {end_body}")
                            
                            break
                            
                        answer = json_object.get("answer")
                        if not answer:
                            continue
                            
                        # 计算增量回答
                        if old_answer and answer.startswith(old_answer):
                            incremental = answer[len(old_answer):]
                        else:
                            incremental = answer
                        
                        old_answer = answer
                        
                        # 显示增量内容，end=0表示还在传输中
                        if incremental:
                            print(f"[end=0] 增量内容: {incremental}")
                        
                        # 构建返回数据对象，包含end字段
                        push_body = {
                            "sessionId": request_body["session_id"],
                            "answer": incremental if incremental else answer,
                            "flag": 1,
                            "wordId": word_id,
                            "end": 0  # 0表示还在传输中
                        }
                        word_id += 1
                        
                        # 显示进度信息
                        print(f"    📊 块 {word_id}: 当前总长度 {len(answer)} 字符")
                        
                        # 这里可以添加推送逻辑
                        # sse_data_service.push_data(push_body)
                        
    except RequestException as e:
        logger.error(f"请求发生错误: {str(e)}")
    except Exception as e:
        logger.error(f"处理响应时发生错误: {str(e)}")

if __name__ == "__main__":
    send_stream_request()
