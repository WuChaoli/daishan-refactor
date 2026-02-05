# 测试环境配置

## 基础环境

| 项目 | 配置 |
|------|------|
| Python 版本 | 3.12.3 |
| 虚拟环境 | `.venv/` |
| 测试框架 | pytest 9.0.2 |
| 异步测试 | pytest-asyncio 1.3.0 |

## 环境变量

### Dify 服务配置
```bash
# Dify 基础URL
DIFY_BASE_RUL=http://172.16.11.60/v1

# 通用聊天 API Key（用于实体提取）
DIFY_CHAT_APIKEY_GENRAL_CHAT=app-cgNzdw5v7MtHMefQeLMSIA9v

# 人员调度 API Key
DIFY_CHAT_APIKEY_PERSONNEL_DISPATCHING=app-3CDscxO2oybkMxKAoH3iH8HL
```

### 环境变量加载
测试时需要加载 `rag_stream/.env` 文件中的环境变量。

## 外部服务依赖

### Dify 服务
- **基础URL**: http://172.16.11.60/v1
- **用途**:
  - 实体提取（GENRAL_CHAT）
  - 人员调度（PERSONNEL_DISPATCHING）
- **网络要求**: 需要能够访问 172.16.11.60

## 测试执行命令

### 运行所有测试
```bash
source .venv/bin/activate
cd rag_stream
pytest tests/ -v
```

### 运行特定测试文件
```bash
pytest tests/test_personnel_dispatch_service.py -v
```

### 运行特定测试用例
```bash
pytest tests/test_personnel_dispatch_service.py::test_single_entity -v
```

### 显示详细日志
```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

## 项目结构

```
daishan-refactor/
├── .venv/                          # 虚拟环境
├── rag_stream/
│   ├── .env                        # 环境变量配置
│   ├── src/
│   │   └── services/
│   │       └── personnel_dispatch_service.py  # 待测试文件
│   └── tests/                      # 测试目录
│       └── test_personnel_dispatch_service.py # 测试文件
└── docs/
    ├── testing/
    │   └── env.md                  # 本文件
    └── contexts/
        └── 2026-02-04_personnel-dispatch-test/
            └── testing/
                └── 04-1529_handle-personnel-dispatch/
                    ├── test-cases.md       # 测试用例
                    ├── execution-log.md    # 执行日志
                    ├── error-analysis.md   # 错误分析
                    └── summary.md          # 测试总结
```

## Mock 策略

### 集成测试（推荐）
使用真实 Dify 服务进行测试，验证完整的业务流程。

**优点**:
- 测试真实的业务场景
- 验证与外部服务的集成

**缺点**:
- 依赖网络连接
- 测试速度较慢
- 可能受外部服务影响

### 单元测试
Mock `get_client` 和 `run_chat` 方法，隔离外部依赖。

**优点**:
- 测试速度快
- 不依赖外部服务
- 可以模拟各种异常情况

**缺点**:
- 无法验证与外部服务的集成
- 需要维护 Mock 数据

## 注意事项

1. **网络连接**: 集成测试需要能够访问 Dify 服务（172.16.11.60）
2. **API Key**: 确保 `.env` 文件中的 API Key 有效
3. **异步测试**: 使用 `@pytest.mark.asyncio` 装饰器标记异步测试
4. **日志验证**: 使用 `caplog` fixture 捕获日志输出
5. **超时设置**: Dify 调用可能需要较长时间，建议设置合理的超时时间

## 更新记录

| 日期 | 更新内容 | 更新人 |
|------|---------|--------|
| 2026-02-04 | 初始创建 | 王麻子 |
