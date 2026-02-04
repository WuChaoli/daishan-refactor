"""
DifyClientFactory 使用示例

演示如何使用 DifyClientFactory 管理多个 Dify client。
"""

import os
from src.services.dify_client_factory import DifyClientFactory


def example_basic_usage():
    """基本使用示例"""
    # 1. 设置环境变量（通常在 .env 文件中配置）
    os.environ["DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING"] = "app-xxx"
    os.environ["DIFY_CHAT_APIKEY_EMERGENCY_RESPONSE"] = "app-yyy"
    os.environ["DIFY_CHAT_APIKEY_PARK_INFO"] = "app-zzz"
    os.environ["DIFY_BASE_RUL"] = "http://172.16.11.60/v1"

    # 2. 创建工厂实例（自动加载所有 DIFY_CHAT_APIKEY_ 前缀的环境变量）
    factory = DifyClientFactory()

    # 3. 列出所有可用的 client
    print("可用的 clients:", factory.list_clients())
    # 输出: ['PERSONNEL_DISPATCHING', 'EMERGENCY_RESPONSE', 'PARK_INFO']

    # 4. 获取指定的 client
    personnel_client = factory.get_client("PERSONNEL_DISPATCHING")
    emergency_client = factory.get_client("EMERGENCY_RESPONSE")

    # 5. 使用 client 调用 Dify API
    # personnel_client.run_chat_streaming(...)
    # emergency_client.run_chat_streaming(...)


def example_check_client_exists():
    """检查 client 是否存在"""
    factory = DifyClientFactory()

    # 检查 client 是否存在
    if factory.has_client("PERSONNEL_DISPATCHING"):
        client = factory.get_client("PERSONNEL_DISPATCHING")
        print("找到 PERSONNEL_DISPATCHING client")
    else:
        print("PERSONNEL_DISPATCHING client 不存在")


def example_custom_base_url():
    """使用自定义 base_url"""
    # 创建工厂时指定自定义 base_url
    factory = DifyClientFactory(base_url="http://custom.example.com/v1")

    # 所有 client 都会使用这个 base_url
    client = factory.get_client("PERSONNEL_DISPATCHING")


def example_error_handling():
    """错误处理示例"""
    factory = DifyClientFactory()

    try:
        # 尝试获取不存在的 client
        client = factory.get_client("NON_EXISTENT")
    except ValueError as e:
        print(f"错误: {e}")
        # 输出: 错误: Client 'NON_EXISTENT' 不存在。可用的 client: ...


if __name__ == "__main__":
    example_basic_usage()
