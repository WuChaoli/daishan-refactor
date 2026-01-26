import json
import requests
import logging
from typing import Generator, Dict, Any, Optional
from requests.exceptions import RequestException
from config import settings

logger = logging.getLogger(__name__)

class RAGClient:
    """RAG服务客户端"""
    
    def __init__(self):
        self.base_url = settings.RAG_BASE_URL
        self.api_key = settings.RAG_API_KEY
        self.timeout = settings.REQUEST_TIMEOUT
        self.stream_timeout = settings.STREAM_TIMEOUT
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_session(self, chat_id: str, name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """创建会话"""
        url = f"{self.base_url}/api/v1/chats/{chat_id}/sessions"
        
        payload = {"name": name}
        if user_id:
            payload["user_id"] = user_id
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"创建会话失败: {str(e)}")
            raise
    
    def chat_stream(self, chat_id: str, question: str, session_id: Optional[str] = None, 
                   user_id: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """流式聊天"""
        url = f"{self.base_url}/api/v1/chats/{chat_id}/completions"
        
        payload = {
            "question": question,
            "stream": True
        }
        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        
        try:
            with requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                stream=True,
                timeout=(self.timeout, self.stream_timeout)
            ) as response:
                response.raise_for_status()
                
                old_answer = ""
                word_id = 0
                
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    # 处理数据行
                    if line.startswith("data:"):
                        line = line.replace("data:", "", 1).strip()
                        
                        try:
                            json_data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        # 检查是否是结束标志
                        if json_data.get("data") is True:
                            break
                        
                        # 获取回答内容
                        answer = json_data.get("answer")
                        if not answer:
                            continue
                        
                        # 计算增量回答
                        incremental_answer = answer.replace(old_answer, "", 1)
                        old_answer = answer
                        
                        # 构建流式响应块
                        chunk = {
                            "session_id": session_id or "new_session",
                            "answer": incremental_answer,
                            "flag": 1,
                            "word_id": word_id,
                            "full_answer": answer,  # 完整回答用于调试
                            "references": json_data.get("data", {}).get("reference", {})
                        }
                        word_id += 1
                        
                        yield chunk
                        
        except RequestException as e:
            logger.error(f"流式聊天请求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"处理流式响应时发生错误: {str(e)}")
            raise
    
    def chat_sync(self, chat_id: str, question: str, session_id: Optional[str] = None,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """同步聊天（非流式）"""
        url = f"{self.base_url}/api/v1/chats/{chat_id}/completions"
        
        payload = {
            "question": question,
            "stream": False
        }
        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"同步聊天请求失败: {str(e)}")
            raise

# 创建全局RAG客户端实例
rag_client = RAGClient()
