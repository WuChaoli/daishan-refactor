# E2E 测试说明

## 测试概述

本目录包含 `/api/general` 接口的端到端测试，用于验证意图分类流程和流式响应的完整可用性。

## 文件结构

```
tests/
├── conftest.py              # pytest 配置和 E2E 辅助工具
├── test_api_general_e2e.py  # E2E 测试脚本
├── data/
│   └── intent_test_cases.xlsx  # 测试用例数据集
└── README.md                # 本文件
```

## 运行测试

### 前提条件

1. 确保依赖已安装：
   ```bash
   uv add --dev pandas openpyxl httpx
   ```

2. 确保 `.env` 文件配置正确（包含 Dify、RAGFlow、DaiShanSQL 配置）

### 运行方式

#### 方式一：直接运行（推荐）

```bash
cd src/rag_stream
python tests/test_api_general_e2e.py
```

测试将自动：
1. 启动 uvicorn 服务
2. 等待服务健康检查通过
3. 执行所有测试用例
4. 生成测试报告
5. 停止服务

#### 方式二：pytest 运行

```bash
cd src/rag_stream
pytest tests/test_api_general_e2e.py -v
```

#### 方式三：跳过测试

```bash
export SKIP_E2E_TEST=1
python tests/test_api_general_e2e.py
```

## 添加新的测试用例

### 编辑 Excel 文件

1. 打开 `tests/data/intent_test_cases.xlsx`
2. 添加新行，填写以下列：
   - `question`: 测试问题文本
   - `expected_type`: 期望意图类型（1/2/3）
   - `description`: 测试用例描述
   - `notes`: 备注（可选）

### 意图类型说明

| Type | 类型名称 | 说明 | 示例 |
|------|----------|------|------|
| 1 | 岱山-指令集 | 园区整体态势类问题 | "园区安全态势如何？" |
| 2 | 岱山-数据库问题 | 企业具体信息查询 | "XX企业的危化品类目是什么？" |
| 3 | 岱山-指令集-固定问题 | 固定联系人查询 | "园区安全负责人是谁？" |

### 使用代码添加

```python
import pandas as pd

# 读取现有测试用例
df = pd.read_excel("tests/data/intent_test_cases.xlsx")

# 添加新用例
new_case = {
    "question": "你的新问题",
    "expected_type": 1,
    "description": "新问题描述",
    "notes": "备注信息"
}
df = pd.concat([df, pd.DataFrame([new_case])], ignore_index=True)

# 保存
df.to_excel("tests/data/intent_test_cases.xlsx", index=False)
```

## 测试输出

### 控制台输出

```
============================================================
E2E Test Report - /api/general
============================================================
Total: 9, Passed: 9, Failed: 0
Pass Rate: 100.0%
------------------------------------------------------------

[PASS] 园区安全态势查询 - Type1
  Question: 园区安全态势如何？
  Expected Type: 1
  Status Code: 200
  Response Time: 1250.5ms
  Stream Events: 15

...

============================================================
```

### JSON 报告

测试完成后会生成 JSON 报告文件：`e2e_report_YYYYMMDD_HHMMSS.json`

报告包含：
- 测试摘要（总数、通过数、失败数、通过率）
- 时间信息（开始时间、结束时间、持续时间）
- 每个测试用例的详细结果

## 辅助函数

### 在 conftest.py 中

```python
from tests.conftest import E2EConfig, check_e2e_dependencies, get_dependency_install_hint

# 检查依赖
missing = check_e2e_dependencies()
if missing:
    print(get_dependency_install_hint())

# 使用配置
print(E2EConfig.DEFAULT_TIMEOUT)  # 30
print(E2EConfig.BASE_URL)         # http://127.0.0.1:8000
```

### 在测试脚本中

```python
from tests.test_api_general_e2e import (
    load_test_cases,
    parse_intent_classification_logs,
    extract_classification_result,
    ServerManager,
)

# 加载测试用例
cases = load_test_cases(filter_type=1)  # 只加载 Type1

# 解析分类日志
logs = parse_intent_classification_logs(Path(".log-manager/runs"))
type_id, confidence = extract_classification_result(logs)

# 管理服务器
with ServerManager() as server:
    # 服务器已启动
    pass  # 服务器会自动停止
```

## 注意事项

1. **端口占用**：测试使用 8000 端口，确保该端口未被占用
2. **环境变量**：测试会加载 `.env` 文件中的配置
3. **外部依赖**：测试会真实调用 Dify、RAGFlow、DaiShanSQL
4. **日志位置**：意图分类日志保存在 `.log-manager/runs/` 目录
5. **超时设置**：默认服务启动超时 30 秒，API 调用超时 60 秒

## 故障排查

### 服务启动失败

```bash
# 检查端口占用
lsof -i :8000

# 手动启动服务测试
cd src/rag_stream
python main.py
```

### 依赖缺失

```bash
# 安装所有测试依赖
uv add --dev pandas openpyxl httpx
```

### Excel 读取失败

确保 `intent_test_cases.xlsx` 文件存在且格式正确：
- 必须包含列：question, expected_type, description
- expected_type 必须是整数（1/2/3）
