import os
import json
import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# 加载环境变量
_ = load_dotenv(find_dotenv())


class OpenAIUtils:
    def __init__(self):
        self.Aliclient = OpenAI(
            base_url=os.getenv("openai_base_url"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.Alimodel = os.getenv("OPENAI_MODEL")

        self.client = OpenAI(
            base_url=os.getenv("TextToSQL_base_url"),
            api_key=os.getenv("TextToSQL_api_key")
        )
        self.sqlmodel =os.getenv("TextToSQL_model")

    def request(self, conversation=None, tools=[], tool_choice="auto",thinking=False,model=""):
        if conversation is None:
            conversation = []

        api_params={}
        api_params["messages"]=conversation
        api_params["temperature"]=0.1
        if tools != []:
            api_params['tools']=tools
            api_params["tool_choice"]=tool_choice
        if model!="":
            api_params['model'] = model
            api_params["extra_body"]={"enable_thinking": False}
            response = self.Aliclient.chat.completions.create(
                **api_params
            )
        else:
            api_params['model'] = self.sqlmodel
            response = self.client.chat.completions.create(
               **api_params
            )
        return response.choices[0].message

    def request_stream(self, conversation=None, tools=[], tool_use="auto", thinking=False):
        """
        一个健壮的流式请求生成器，能正确处理文本和工具调用。
        """
        if conversation is None:
            conversation = []

        response = self.client.chat.completions.create(
            messages=conversation,
            model=self.model,
            extra_body={"enable_thinking": thinking},
            tool_choice=tool_use,
            tools=tools,
            stream=True
        )

        tool_calls_buffer = {}  # 用于组装工具调用的缓冲区
        content = ""
        reasoning_content = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # 1. 处理文本内容 (优化了检查方式)
            if delta.content:
                content += delta.content
                yield ('content', delta.content)

            # 2. 处理推理内容 (修正了检查顺序)
            # 注意：reasoning_content 不是 OpenAI 官方标准，可能是特定提供商的扩展
            # 如果你的提供商不支持，这部分代码永远不会执行
            elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning_content += delta.reasoning_content
                yield ('reasoning_content', delta.reasoning_content)

            # 3. 处理工具调用 (优化了检查方式)
            elif delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    index = tool_call_delta.index
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {"id": "", "function": {"name": "", "arguments": ""}}

                    if tool_call_delta.id:
                        tool_calls_buffer[index]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_calls_buffer[index]["function"]["name"] += tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            tool_calls_buffer[index]["function"]["arguments"] += tool_call_delta.function.arguments

            # 4. 检查是否完成，如果完成，则yield完整的工具调用
            if finish_reason == 'tool_calls':
                complete_tool_calls = []
                for tc in tool_calls_buffer.values():
                    complete_tool_calls.append({
                        "id": tc["id"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        },
                        "type": "function"  # 添加 type 字段以符合标准格式
                    })

                # 按照流式输出格式，逐个输出工具调用
                for tool_call in complete_tool_calls:
                    yield ('tool_call', tool_call)

                tool_calls_buffer.clear()

        # yield ('done', {"reasoning_content": reasoning_content, "content": content, "tool_calls_complete": []})

    def add_user_messages(self, prompt, conversation=None):
        if conversation is None:
            conversation = []
        conversation.append({"role": "user", "content": prompt})
        return conversation

    def add_ai_messages(self, conversation, message):
        # message 应该是一个完整的消息对象，比如从 request() 返回的
        conversation.append(message)
        return conversation

    def print_stream_response(self, stream_generator):
        full_response = ""
        reasoning_content = ""
        tools=""
        for event_type, data in stream_generator:
            if event_type == 'content':
                print(data, end='', flush=True)
                full_response += data
            elif event_type == 'reasoning_content':
                reasoning_content+=data
                print(f"{data}", end='', flush=True)
            elif event_type == 'tool_calls_complete':
                print("\n\n--- 检测到工具调用 ---")
                tools+=data
                print("完整的工具调用对象:", json.dumps(data, indent=2, ensure_ascii=False))
        return {
            "content": full_response,
            "reasoning_content": reasoning_content,
            "tools": tools,
        }

    def send_message(self, stream_generator):
        for event_type, data in stream_generator:
            yield (event_type, data)

    def add_stream_response(self, stream_generator,conversation=None):
        for event_type, data in stream_generator:
            if event_type == 'done':
                reasoning_content = data["reasoning_content"]
                content = data["content"]
                self.add_assistant_message(reasoning_content,content,conversation)

    def add_assistant_message(self, reasoning_content, content,conversation):
        data={
            "role": "assistant",
            "content": f"<thinking>{reasoning_content}</thinking>{content}"
        }
        conversation.append(data)

if __name__ == "__main__":
    utils = OpenAIUtils()
    prompt = "我想查询北京2024年11月的天气"

    # 假设我们有这样一个工具
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"},
                },
                "required": ["location"],
            },
        }
    }]

    print("--- 开始流式请求 ---")

    # 使用 for 循环来消费生成器
    stream_generator = utils.request_stream(conversation=[{"role": "user", "content": prompt}], tools=tools, tool_use="auto",thinking=True)
    full_response = ""
    utils.print_stream_response(stream_generator)