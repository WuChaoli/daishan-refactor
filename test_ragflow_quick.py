#!/usr/bin/env python3
"""
RAGFlow 快速网络测试 - 精简版
"""

import time
import requests

BASE_URL = "http://172.16.11.60:8081/api/v1"
API_KEY = "ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def test(method, page_size=100, timeout=30):
    """测试 datasets 接口"""
    url = f"{BASE_URL}/datasets"
    params = {"page": 1, "page_size": page_size}

    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        else:
            resp = requests.post(url, headers=HEADERS, json=params, timeout=timeout)

        elapsed = time.time() - start
        print(f"{method:4} | timeout={timeout:3}s | {resp.status_code} | {elapsed:.2f}s | {len(resp.text)} bytes")
        return True
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"{method:4} | timeout={timeout:3}s | TIMEOUT | {elapsed:.2f}s | -")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"{method:4} | timeout={timeout:3}s | ERROR | {elapsed:.2f}s | {type(e).__name__}")
        return False

print("=" * 70)
print("RAGFlow 快速网络测试")
print(f"目标: {BASE_URL}")
print("=" * 70)
print(f"{'Method':6} | {'Timeout':9} | {'Status':7} | {'Time':6} | {'Size':10}")
print("-" * 70)

# 测试不同组合
results = []
results.append(("GET/30s", test("GET", page_size=100, timeout=30)))
results.append(("GET/10s", test("GET", page_size=100, timeout=10)))
results.append(("POST/30s", test("POST", page_size=100, timeout=30)))

# 测试小数据量
results.append(("GET/10s/small", test("GET", page_size=1, timeout=10)))

print("-" * 70)
print(f"结果: {sum(1 for _, r in results if r)}/{len(results)} 成功")
