import requests
import json
import time

# 配置
BASE_URL = "http://localhost:11027"
API_KEY = "ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm"

def test_create_session():
    """测试创建会话"""
    url = f"{BASE_URL}/api/sessions/法律法规"
    data = {
        "name": "测试会话",
        "user_id": "test_user_001"
    }
    
    response = requests.post(url, json=data)
    print(f"创建会话响应: {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    
    if response.status_code == 200:
        return response.json()["data"]["session_id"]
    return None

def test_stream_chat(user_id, question, category="laws"):
    """测试流式聊天 - 使用用户ID进行会话绑定"""
    url = f"{BASE_URL}/api/{category}"
    data = {
        "question": question,
        "user_id": user_id  # 只传user_id，不传session_id，系统会自动绑定会话
    }
    
    print(f"\n开始流式聊天 - 问题: {question}")
    print(f"用户ID: {user_id}")
    print("=" * 50)
    
    try:
        with requests.post(url, json=data, stream=True, timeout=60) as response:
            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data_content = line.replace("data:", "", 1).strip()
                        try:
                            json_data = json.loads(data_content)
                            if json_data.get("code") == 0:
                                data_field = json_data.get("data", {})
                                if data_field.get("flag") == 1:  # 正常数据
                                    answer = data_field.get("answer", "")
                                    word_id = data_field.get("wordId", 0)
                                    print(f"[{word_id}] {answer}", end="", flush=True)
                                elif data_field.get("flag") == 0:  # 结束标志
                                    print("\n[流式回复结束]")
                                    break
                            else:
                                print(f"\n错误: {json_data.get('message')}")
                        except json.JSONDecodeError:
                            continue
            else:
                print(f"请求失败: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"流式聊天异常: {str(e)}")

def test_user_session_binding():
    """测试用户会话绑定功能"""
    user_id = "test_user_001"
    
    print(f"\n🧪 测试用户会话绑定功能")
    print(f"用户ID: {user_id}")
    print("=" * 60)
    
    # 第一次提问 - 会自动创建会话
    print("\n📝 第一次提问（自动创建会话）:")
    test_stream_chat(user_id, "有哪些危险预警源？", "warn")
    
    # 等待一下
    time.sleep(2)
    
    # 第二次提问 - 应该使用同一个会话
    print("\n📝 第二次提问（使用同一会话）:")
    test_stream_chat(user_id, "这些法规有哪些具体要求？", "laws")
    
    # 等待一下
    time.sleep(2)
    
    # 第三次提问 - 继续使用同一会话
    print("\n📝 第三次提问（继续同一会话）:")
    test_stream_chat(user_id, "违反这些法规会有什么后果？", "laws")

def test_multi_category_sessions():
    """测试同一用户在不同类别的会话管理"""
    user_id = "test_user_002"
    
    print(f"\n🧪 测试多类别会话管理")
    print(f"用户ID: {user_id}")
    print("=" * 60)
    
    # 在法律法规类别提问
    # print("\n📚 重大危险源预警:")
    # test_stream_chat(user_id, "有哪些法律法规？", "laws")
    # time.sleep(2)
    # print("\n📚 通用:")
    # test_stream_chat(user_id, "介绍岱山经开区当前安全状况", "general")
    # time.sleep(2)
    
    print("\n📚 重大危险源预警:")
    test_stream_chat(user_id, "有哪些危险预警源？", "warn")
    time.sleep(2)
    
    # 在标准规范类别提问
    print("\n📚 当日安全态势:")
    test_stream_chat(user_id, "当日安全态势是什么？", "safesituation")
    time.sleep(2)
    
    # 在应急知识类别提问
    print("\n📚 双重预防机制效果:")
    test_stream_chat(user_id, "双重预防机制是什么？", "prevent")
    time.sleep(2)

    # # 在应急知识类别提问
    # print("\n📚 园区开停车:")
    # test_stream_chat(user_id, "双重预防机制是什么？", "park")
    # time.sleep(2)

    # 在应急知识类别提问
    print("\n📚 园区特殊作业态势:")
    test_stream_chat(user_id, "园区特殊作业态势有哪些？", "special")
    time.sleep(2)

    # 在应急知识类别提问
    print("\n📚 园区企业态势:")
    test_stream_chat(user_id, "园区企业态势？", "firmsituation")
    time.sleep(2)
    
    # # 再次在法律法规类别提问 - 应该使用之前的会话
    # print("\n📚 法律法规类别（继续之前会话）:")
    # test_stream_chat(user_id, "刚才说的法规还有哪些细节？", "laws")

def test_get_user_sessions(user_id):
    """测试获取用户会话信息"""
    url = f"{BASE_URL}/api/user/{user_id}/sessions"
    response = requests.get(url)
    print(f"\n📊 获取用户 {user_id} 的会话信息:")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    else:
        print(f"错误: {response.text}")

def test_categories():
    """测试获取支持的类别"""
    url = f"{BASE_URL}/api/categories"
    response = requests.get(url)
    print(f"\n支持的类别: {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

def test_health():
    """测试健康检查"""
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    print(f"\n健康检查: {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

def main():
    """主测试函数"""
    # print("开始测试RAG流式回复API - 用户会话绑定功能")
    # print("=" * 80)
    
    # # 测试健康检查
    # test_health()
    
    # # 测试获取类别
    # test_categories()
    
    # # 测试用户会话绑定功能
    # test_user_session_binding()
    
    # 测试多类别会话管理
    test_multi_category_sessions()
    
    # 获取用户会话信息
    # test_get_user_sessions("test_user_001")
    # test_get_user_sessions("test_user_002")
    
    # print("\n" + "=" * 80)
    # print("✅ 测试完成！")
    # print("\n💡 关键特性演示:")
    # print("1. 同一用户在同一类别中连续提问会使用相同的session_id")
    # print("2. 不同类别会创建独立的会话")
    # print("3. 会话会自动过期和清理")
    # print("4. 支持查看用户的所有会话信息")

if __name__ == "__main__":
    main()
