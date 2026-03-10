#!/usr/bin/env python3
"""
RAGFlow 网络连接测试脚本
测试 GET/POST 请求 datasets 接口，以及网络延迟
"""

import time
import requests
import subprocess
import sys

# RAGFlow 配置
BASE_URL = "http://172.16.11.60:8081/api/v1"
API_KEY = "ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm"
TIMEOUT = 30

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def test_ping():
    """测试网络延迟"""
    print("=" * 60)
    print("测试1: 网络延迟 (ping)")
    print("=" * 60)

    try:
        # ping 5 次
        result = subprocess.run(
            ["ping", "-c", "5", "172.16.11.60"],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"[WARNING] ping 返回非零状态: {result.returncode}")
            print(f"stderr: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] ping 失败: {e}")
    print()


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试2: 健康检查接口 (GET /api/health)")
    print("=" * 60)

    url = f"{BASE_URL}/api/health"
    start_time = time.time()

    try:
        response = requests.get(url, timeout=TIMEOUT)
        elapsed = time.time() - start_time
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.3f}s")
        print(f"响应内容: {response.text[:200]}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {e}")
    print()


def test_datasets_get():
    """测试 GET 请求 datasets"""
    print("=" * 60)
    print("测试3: GET /datasets")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": 100}

    start_time = time.time()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"响应数据结构类型: {type(data).__name__}")

            # 处理不同的数据结构
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("data", {}).get("items", []) if isinstance(data.get("data"), dict) else data.get("items", [])
            else:
                items = []

            print(f"数据集数量: {len(items)}")
            if items:
                print("数据集列表:")
                for item in items[:5]:  # 只显示前5个
                    if isinstance(item, dict):
                        print(f"  - {item.get('name')} (ID: {item.get('id')})")
                    else:
                        print(f"  - {item}")
                if len(items) > 5:
                    print(f"  ... 还有 {len(items) - 5} 个")
        else:
            print(f"响应内容: {response.text[:500]}")
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] 请求超时 ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {type(e).__name__}: {e}")
    print()


def test_datasets_post():
    """测试 POST 请求 datasets"""
    print("=" * 60)
    print("测试4: POST /datasets (尝试)")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    payload = {"page": 1, "page_size": 100}

    start_time = time.time()
    try:
        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.3f}s")
        print(f"响应内容: {response.text[:500]}")

        if response.status_code == 200:
            data = response.json()
            items = data.get("data", {}).get("items", [])
            print(f"数据集数量: {len(items)}")

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] 请求超时 ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {type(e).__name__}: {e}")
    print()


def test_bandwidth():
    """粗略测试带宽（通过下载响应内容）"""
    print("=" * 60)
    print("测试5: 粗略带宽测试")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": 100}

    start_time = time.time()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT,
            stream=True  # 使用流式读取以准确计算
        )

        # 读取所有内容
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk

        elapsed = time.time() - start_time
        size_bytes = len(content)
        size_kb = size_bytes / 1024
        bandwidth_kbps = size_kb / elapsed if elapsed > 0 else 0

        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应大小: {size_kb:.2f} KB ({size_bytes} bytes)")
        print(f"总耗时: {elapsed:.3f}s")
        print(f"粗略带宽: {bandwidth_kbps:.2f} KB/s")

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] 请求超时 ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {type(e).__name__}: {e}")
    print()


def test_with_longer_timeout():
    """使用更长超时测试 GET datasets"""
    print("=" * 60)
    print("测试6: GET /datasets (超时 120s)")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": 100}
    long_timeout = 120

    start_time = time.time()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=long_timeout
        )
        elapsed = time.time() - start_time
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"响应数据结构类型: {type(data).__name__}")

            # 处理不同的数据结构
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("data", {}).get("items", []) if isinstance(data.get("data"), dict) else data.get("items", [])
            else:
                items = []

            print(f"数据集数量: {len(items)}")
        else:
            print(f"响应内容: {response.text[:500]}")
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] 请求超时 ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {type(e).__name__}: {e}")
    print()


def test_multiple_requests():
    """多次请求测试成功率"""
    print("=" * 60)
    print("测试7: 多次请求成功率测试 (10次 GET /datasets)")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": 100}

    success_count = 0
    timeout_count = 0
    error_count = 0
    times = []

    for i in range(10):
        start_time = time.time()
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30
            )
            elapsed = time.time() - start_time
            times.append(elapsed)

            if response.status_code == 200:
                success_count += 1
                print(f"  请求 {i+1}: OK ({elapsed:.3f}s)")
            else:
                error_count += 1
                print(f"  请求 {i+1}: 错误 {response.status_code} ({elapsed:.3f}s)")
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            timeout_count += 1
            print(f"  请求 {i+1}: 超时 ({elapsed:.3f}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            error_count += 1
            print(f"  请求 {i+1}: 异常 {type(e).__name__} ({elapsed:.3f}s)")

        time.sleep(0.5)  # 短暂间隔

    print(f"\n统计结果:")
    print(f"  成功: {success_count}/10")
    print(f"  超时: {timeout_count}/10")
    print(f"  错误: {error_count}/10")
    if times:
        print(f"  平均响应时间: {sum(times)/len(times):.3f}s")
        print(f"  最快: {min(times):.3f}s, 最慢: {max(times):.3f}s")
    print()


def test_with_small_page_size():
    """测试小数据量请求"""
    print("=" * 60)
    print("测试8: GET /datasets (page_size=1, 小数据量)")
    print("=" * 60)

    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": 1}

    start_time = time.time()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30
        )
        elapsed = time.time() - start_time
        print(f"URL: {url}?page=1&page_size=1")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        data = response.json()
        print(f"响应数据结构类型: {type(data).__name__}")
        print(f"响应大小: {len(response.text)} bytes")
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] 请求超时 ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 请求失败 ({elapsed:.3f}s): {type(e).__name__}: {e}")
    print()


def main():
    print("\n" + "=" * 60)
    print("RAGFlow 网络连接测试")
    print(f"目标: {BASE_URL}")
    print("=" * 60 + "\n")

    test_ping()
    test_health()
    test_datasets_get()
    test_datasets_post()
    test_bandwidth()
    test_with_longer_timeout()
    test_multiple_requests()
    test_with_small_page_size()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
