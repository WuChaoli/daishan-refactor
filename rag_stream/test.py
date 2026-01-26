import requests
import time
import json

# 配置测试参数
API_URL = "http://172.16.11.60:11027/api/general"  # 对应FastAPI服务地址和端口
TEST_MESSAGES = [
    "介绍下浙江世倍尔新材料有限公司"  # 测试空输入的情况
]

def test_stream_chat(question: str, user_id: str = "test_user_001"):
    """测试流式聊天接口"""
    print(f"\n{'#'*50}")
    print(f"测试消息: {question!r}")
    print(f"用户ID: {user_id}")
    print(f"发送请求到: {API_URL}")
    print(f"{'#'*50}\n")

    # 构建请求数据
    payload = {
        "question": question,
        "user_id": user_id
    }

    try:
        # 发送POST请求，接收流式响应
        with requests.post(
            API_URL,
            json=payload,
            stream=True,
            timeout=60
        ) as response:
            # 检查响应状态码
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return

            print("开始接收流式响应...\n")
            
            # 逐行处理流式响应
            for line in response.iter_lines(decode_unicode=True):
                if line:  # 过滤空行
                    print(line, end='', flush=True)
            
            print("\n\n流式响应接收完成")
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生异常: {str(e)}")
    except Exception as e:
        print(f"处理响应时发生异常: {str(e)}")

if __name__ == "__main__":
    print("=== 开始测试流式聊天接口 ===")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 逐个测试消息
    for i, message in enumerate(TEST_MESSAGES, 1):
        print(f"\n\n=== 测试用例 {i}/{len(TEST_MESSAGES)} ===")
        test_stream_chat(message, f"test_user_{i:03d}")
        time.sleep(2)  # 等待2秒再进行下一个测试，避免请求过于密集
    
    print("\n\n=== 所有测试用例执行完毕 ===")
