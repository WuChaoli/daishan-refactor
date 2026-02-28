---
phase: 05-意图分类基础
plan: 01
subsystem: 意图分类
tags: [intent-classification, llm, coarse-classification]
dependency_graph:
  requires: []
  provides: [CLS-03-意图驱动检索]
  affects: [intent-service]
tech_stack:
  added: []
  patterns:
    - name: "LLM-based coarse classification"
      description: "使用 LLM 进行粗粒度意图分类，解决语义混淆问题"
    - name: "Degradation pattern"
      description: "分类失败时降级到默认结果，保证服务可用性"
    - name: "Timeout control"
      description: "使用 asyncio.wait_for 实现 3 秒超时控制"
key_files:
  created:
    - src/rag_stream/src/utils/intent_classifier.py
  modified:
    - src/rag_stream/src/config/settings.py
    - src/rag_stream/config.yaml
decisions: []
metrics:
  duration: "3 minutes"
  completed_date: "2026-02-28"
---

# Phase 5 Plan 1: Intent Classification Foundation Summary

基于 LLM 的粗粒度意图分类服务，解决语义混淆导致分类不准确的问题

## Overview

本计划实现了基于 LLM 的粗粒度意图分类服务，作为向量检索的前置层。通过引入 LLM 进行粗分类（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3），解决不同意图类型在向量空间中语义接近导致的分类混淆问题。

## Key Deliverables

### 1. IntentClassificationConfig 配置模型

**File:** `src/rag_stream/src/config/settings.py`

新增 `IntentClassificationConfig` 配置类，包含：

- `enabled`: bool - 功能开关（默认 false）
- `api_key`: str - 聊天服务 API Key
- `base_url`: str - 聊天服务 Base URL
- `model`: str - 模型名称
- `timeout`: int - HTTP 超时时间（默认 3 秒）
- `temperature`: float - 采样温度（默认 0.0）
- `confidence_threshold`: float - 置信度阈值（默认 0.5）

**字段验证：**
- timeout 必须 > 0
- temperature 必须在 0-2 之间
- confidence_threshold 必须在 0-1 之间

**集成方式：**
- 在 `Settings` 类中添加 `intent_classification` 字段
- 在 `load_from_yaml` 方法中添加配置加载
- 支持环境变量覆盖（INTENT_CLASSIFICATION_* 前缀）

### 2. IntentClassifier 分类服务

**File:** `src/rag_stream/src/utils/intent_classifier.py`

核心类和方法：

#### ClassificationResult 数据类

```python
@dataclass
class ClassificationResult:
    type_id: int  # 1/2/3
    confidence: float  # 0.0-1.0
    raw_response: str  # 原始响应
    degraded: bool  # 是否降级
```

#### IntentClassifier 类

主要方法：

- `_build_client()`: 构建 OpenAI 客户端，验证配置完整性
- `_get_client()`: 懒加载客户端实例
- `_build_prompt()`: 生成结构化分类 prompt
- `_parse_classification_result()`: 解析 JSON 响应
- `_validate_classification_result()`: 验证分类结果有效性
- `_get_degraded_result()`: 返回降级结果
- `classify()`: 分类主方法，包含超时控制和异常处理

**分类 Prompt 格式：**

```
你是问题分类助手。请根据用户的问题，判断其属于以下哪种类型：

1 - 岱山-指令集
2 - 岱山-数据库问题
3 - 岱山-指令集-固定问题

只返回 JSON 格式：{"type": 数字编号, "confidence": 置信度(0.0-1.0)}，不要添加其他说明。
```

**降级策略：**
- 功能禁用时返回 degraded=True
- 输入验证失败时返回 degraded=True
- 超时 3 秒时返回 degraded=True
- API 错误时返回 degraded=True
- JSON 解析失败时返回 degraded=True
- 分类结果无效时返回 degraded=True

**日志标记：**
- `classifier.attempt`: 分类尝试
- `classifier.success`: 分类成功
- `classifier.error`: 分类失败
- `classifier.timeout`: 超时
- `classifier.disabled`: 功能禁用
- `classifier.invalid_input`: 输入无效
- `classifier.empty_query`: 查询为空
- `classifier.invalid_response`: 响应无效

**便捷函数：**
- `get_intent_classifier()`: 获取全局分类器实例
- `classify_intent(query)`: 同步分类接口

### 3. config.yaml 配置文件

**File:** `src/rag_stream/config.yaml`

新增 `intent_classification` 配置块：

```yaml
intent_classification:
  enabled: false
  api_key: "xiyunmu"
  base_url: "http://172.16.11.61:50016/v1"
  model: "Qwen2.5-7B-Instruct"
  timeout: 3
  temperature: 0.0
  confidence_threshold: 0.5
```

**默认配置说明：**
- `enabled: false` - 便于灰度发布
- `timeout: 3` - 快速失败
- `temperature: 0.0` - 确定性输出
- `confidence_threshold: 0.5` - 中等置信度要求

## Technical Implementation

### 复用现有工具

分类服务复用了以下 v1.0 已实现的工具：

- **QueryChat 工具类**: OpenAI 客户端封装模式
- **配置加载机制**: YAML + 环境变量覆盖
- **marker 日志系统**: 统一的事件追踪

### 设计模式

1. **降级兜底模式**: 任何异常都返回安全默认值，保持服务可用性
2. **懒加载模式**: OpenAI 客户端按需初始化
3. **超时控制**: 使用 `asyncio.wait_for` 实现 3 秒超时
4. **配置驱动**: 通过 YAML 和环境变量控制行为

### 错误处理

所有异常都返回降级结果：

```python
except Exception as error:
    marker("classifier.error", {"error": str(error)}, level="ERROR")
    return self._get_degraded_result()
```

## Deviations from Plan

None - plan executed exactly as written.

## Verification

### Configuration Model
- [x] `IntentClassificationConfig` class defined with field validation
- [x] `intent_classification` field added to `Settings`
- [x] YAML loading implemented in `load_from_yaml`
- [x] Environment variable overrides supported

### Classification Service
- [x] `ClassificationResult` dataclass defined
- [x] `IntentClassifier` class implemented
- [x] `_build_prompt` generates structured prompt
- [x] `_parse_classification_result` parses JSON response
- [x] `classify` method with timeout and degradation
- [x] Marker logging: attempt, success, error, timeout, disabled
- [x] Convenience functions: `get_intent_classifier`, `classify_intent`

### Config File
- [x] `intent_classification` config block added
- [x] Default enabled=false
- [x] API config included
- [x] Model params included
- [x] Environment variable overrides documented

## Success Criteria Met

1. ✅ 系统在意图识别前能对用户 query 进行粗粒度分类（岱山-指令集 1 / 岱山-数据库问题 2 / 岱山-指令集-固定问题 3）
2. ✅ 分类服务使用 QueryChat 工具实现，配置专门的分类 prompt
3. ✅ 管理员可在 config.yaml 中配置分类开关、模型参数和阈值
4. ✅ 环境变量可以覆盖配置中的分类参数（如模型名称、温度）

## Next Steps

计划 05-02 将在本计划的基础上，集成意图分类服务到 BaseIntentService，实现两阶段识别流程：
1. 粗分类：LLM 判断问题类型
2. 精检索：仅在对应类型的向量库中检索具体问题

## Self-Check: PASSED

**Created files:**
- [x] `src/rag_stream/src/utils/intent_classifier.py`

**Modified files:**
- [x] `src/rag_stream/src/config/settings.py`
- [x] `src/rag_stream/config.yaml`

**Commits:**
- [x] 2a2ff2c: feat(05-01): add IntentClassificationConfig model
- [x] 0abbcaa: feat(05-01): implement intent classification service
- [x] 5184c4b: feat(05-01): add intent_classification config block

**Key classes verified:**
- [x] IntentClassificationConfig in settings.py
- [x] IntentClassifier in intent_classifier.py
- [x] ClassificationResult in intent_classifier.py
