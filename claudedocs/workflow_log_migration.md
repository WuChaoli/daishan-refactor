# 日志迁移工作流: log-manager 集成

**生成时间**: 2026-02-24
**任务**: 将 `src/rag_stream` 项目的日志系统从 `log_decorator` 迁移到 `log-manager`
**策略**: 入口用 @entry_trace,内部函数用 @trace,完全移除 logger 调用

---

## 1. 迁移范围确认

### 目标文件(10个核心文件)
- `src/rag_stream/main.py` - 应用入口
- `src/rag_stream/src/routes/chat_routes.py` - 路由层
- `src/rag_stream/src/services/rag_service.py` - RAG服务
- `src/rag_stream/src/services/chat_general_service.py` - 通用聊天服务
- `src/rag_stream/src/services/dify_service.py` - Dify服务
- `src/rag_stream/src/services/guess_questions_service.py` - 猜你想问服务
- `src/rag_stream/src/services/personnel_dispatch_service.py` - 人员调度服务
- `src/rag_stream/src/services/source_dispath_srvice.py` - 资源调度服务
- `src/rag_stream/src/utils/ragflow_client.py` - RAGFlow客户端
- `src/rag_stream/src/utils/session_manager.py` - 会话管理器

### 测试文件(2个)
- `tests/test_intent_service_mock.py`
- `tests/test_source_dispatch_sorting.py`

### 当前日志使用模式
- **导入**: `from log_decorator import logger`
- **调用**: `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()`
- **总计**: 约60+处 logger 调用

---

## 2. 阶段划分与任务列表

### 阶段1: 准备阶段 (预计30分钟)

#### 1.1 环境准备
- [ ] 确认 `log-manager` 已正确安装并可导入
- [ ] 创建迁移分支: `git checkout -b feat/log-manager-migration`
- [ ] 备份当前 `logs/` 目录结构作为对比基准

#### 1.2 配置初始化
- [ ] 在 `src/rag_stream/main.py` 顶部添加 `log_manager` 配置
- [ ] 设置 `base_dir` 为 `src/rag_stream/.log-manager`
- [ ] 配置 `session_id` 为动态生成(如 `rag_stream_{timestamp}`)
- [ ] 配置 `parameter_whitelist` 包含关键参数: `user_id`, `session_id`, `category`, `chat_id`
- [ ] 启用后台线程: `enable_background_threads=True`
- [ ] 配置报告触发器: `trigger_timer_s=60`, `immediate_on_error=True`

#### 1.3 依赖更新
- [ ] 移除 `log_decorator` 依赖(保留用于测试文件的过渡期)
- [ ] 更新 `requirements.txt` 或 `pyproject.toml` 确保 `log-manager` 在列表中

**检查点**:
- `log_manager` 可正常导入和配置
- 配置文件路径正确
- runtime 可成功初始化

---

### 阶段2: 核心入口迁移 (预计1小时)

#### 2.1 main.py 迁移
- [ ] **导入变更**:
  ```python
  # 删除: from log_decorator import logger
  # 新增: from log_manager import LogManagerConfig, configure, marker
  ```

- [ ] **初始化 runtime** (在 lifespan 之前):
  ```python
  cfg = LogManagerConfig(
      base_dir=Path(".log-manager"),
      session_id=f"rag_stream_{int(datetime.now().timestamp())}",
      parameter_whitelist=("user_id", "session_id", "category")
  )
  runtime = configure(cfg)
  ```

- [ ] **lifespan 函数**添加 `@entry_trace("app-lifespan")`

- [ ] **替换所有 `logger.info/warning/error`** 调用:
  - 启动日志 → `marker("服务启动", {"host": settings.server.host})`
  - 连接测试 → `marker("RAGFlow连接测试", {"success": bool})`

- [ ] **添加优雅关闭**: `runtime.shutdown()` 在 lifespan yield 后

#### 2.2 routes/chat_routes.py 迁移
- [ ] 导入变更: `from log_manager import entry_trace, trace, marker`
- [ ] 路由函数添加 `@entry_trace`:
  - `chat_with_category` → `@entry_trace("chat-category")`
  - `chat_with_dify` → `@entry_trace("chat-dify")`
- [ ] 替换 `logger.info/debug/warning` 为 `marker()`
  - 关键节点: 会话创建、流启动、类别验证
- [ ] 移除所有 `logger` 导入和调用

**检查点**:
- main.py 启动时有日志输出到 `.log-manager/runs/`
- 访问任意 API 端点生成 entry 报告
- 控制台有终端格式日志输出

---

### 阶段3: 服务层迁移 (预计2-3小时)

#### 3.1 rag_service.py
- [ ] 添加 `@trace` 到:
  - `get_rag_client()`
  - `create_rag_session()`
  - `get_or_create_session()`
  - `stream_chat_response()`

- [ ] 替换所有 `logger` 调用:
  - 创建会话开始/成功 → `marker("创建RAG会话", {"chat_id": ..., "session_name": ...})`
  - 使用现有会话 → `marker("复用现有会话", {"session_id": ...})`
  - 错误日志 → 让装饰器自动捕获异常,或使用 `marker(..., level="ERROR")`

- [ ] 移除 `from log_decorator import logger`

#### 3.2 chat_general_service.py
- [ ] 添加 `@entry_trace("chat-general")` 到主入口函数
- [ ] 添加 `@trace` 到内部辅助函数:
  - `_extract_questions_for_sql`
  - `_extract_question_from_qa_text`
  - `_post_process_type1`

- [ ] 替换所有 `FLOW_MARKER` + `logger` 组合:
  - `logger.debug(f"{FLOW_MARKER} ...")` → `marker("extract_questions.start", {"count": ...})`

- [ ] 异常处理: 移除 `logger.error`,依赖装饰器自动捕获

#### 3.3 dify_service.py
- [ ] 添加 `@entry_trace("dify-chatflow")` 到流式响应函数
- [ ] 内部函数使用 `@trace`
- [ ] 关键 marker: Dify 调用开始、响应类型、错误重试

#### 3.4 guess_questions_service.py
- [ ] 添加 `@entry_trace("guess-questions")` 到 `handle_guess_questions`
- [ ] 内部函数使用 `@trace`
- [ ] 替换 logger 调用为 marker: 意图识别完成、问题生成成功/失败

#### 3.5 personnel_dispatch_service.py
- [ ] 入口函数 `@entry_trace("personnel-dispatch")`
- [ ] 替换所有 logger 调用

#### 3.6 source_dispath_srvice.py
- [ ] 入口函数 `@entry_trace("source-dispatch")`
- [ ] 替换所有 logger 调用

**检查点**:
- 每个服务的主要流程有完整调用链
- 错误场景能正确捕获并生成报告
- 参数白名单正确过滤敏感信息

---

### 阶段4: 工具层迁移 (预计1小时)

#### 4.1 ragflow_client.py
- [ ] 添加 `@trace` 到:
  - `test_connection()`
  - `search()` / `chat()`

- [ ] 替换 logger 调用为 marker
- [ ] API 错误依赖装饰器捕获

#### 4.2 session_manager.py
- [ ] 添加 `@trace` 到:
  - `create_session()`
  - `get_user_session()`
  - `cleanup_all_expired_sessions()`

- [ ] 替换所有 logger 调用

**检查点**:
- 工具函数调用链可追踪
- 会话管理操作有日志记录

---

### 阶段5: 测试文件处理 (预计30分钟)

#### 5.1 测试文件迁移
- [ ] `test_intent_service_mock.py`:
  - 移除 `from log_decorator import logger`
  - 删除测试中的 logger 验证断言
  - 如需验证日志,改为检查 `.log-manager` 目录中的事件文件

- [ ] `test_source_dispatch_sorting.py`:
  - 同上处理

#### 5.2 验证测试通过
- [ ] 运行 `pytest src/rag_stream/tests/`
- [ ] 确保无 `NameError: name 'logger' is not defined`
- [ ] 确保测试逻辑未被破坏

**检查点**:
- 所有测试通过
- 无残留的 log_decorator 导入错误

---

### 阶段6: 验证与清理 (预计1小时)

#### 6.1 功能验证
- [ ] 启动服务: `python main.py`
- [ ] 验证启动日志输出到控制台和文件
- [ ] 调用 `/api/chat/法律法规` 接口
- [ ] 验证生成 entry 报告: `.log-manager/reports/{session}/entries/{entry_id}/latest.txt`
- [ ] 触发错误场景(如关闭 RAGFlow),验证错误报告生成
- [ ] 检查参数脱敏: 确保敏感参数不在日志中

#### 6.2 性能验证
- [ ] 对比迁移前后响应时间(应在5%以内)
- [ ] 检查日志文件大小增长速度
- [ ] 验证后台线程不影响主业务

#### 6.3 代码清理
- [ ] 全局搜索 `log_decorator` 引用,确保全部移除
- [ ] 移除 `log_decorator` 依赖
- [ ] 删除旧的 `logs/` 目录(可选,建议先备份)
- [ ] 更新 README.md 中的日志配置说明

#### 6.4 文档更新
- [ ] 更新 `docs/static/guide/deployment.md`:
  - 日志目录改为 `.log-manager/`
  - 添加 log-manager 配置说明
- [ ] 更新 `docs/static/architecture/` 相关架构图
- [ ] 添加故障排查指南:如何查看 entry 报告

**检查点**:
- 所有功能正常工作
- 日志输出符合预期
- 代码无残留的 log_decorator 引用
- 文档已同步更新

---

## 3. 任务依赖关系

```
阶段1(环境准备)
  ↓
阶段2(main.py + routes) ← 必须先完成,因为其他文件依赖runtime初始化
  ↓
阶段3(服务层) ← 可并行迁移不同service文件
  ├─ rag_service.py
  ├─ chat_general_service.py
  ├─ dify_service.py
  ├─ guess_questions_service.py
  ├─ personnel_dispatch_service.py
  └─ source_dispath_srvice.py
  ↓
阶段4(工具层) ← 可与服务层并行
  ↓
阶段5(测试文件) ← 依赖代码迁移完成
  ↓
阶段6(验证清理) ← 最后执行
```

**并行机会**:
- 阶段3的不同 service 文件可并行迁移
- 阶段4可与阶段3并行
- 阶段5可在阶段3-4部分完成后开始

---

## 4. 风险点识别与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| **装饰器改变函数签名** | 类型检查失败 | 中 | 使用 `functools.wraps`,验证 FastAPI 路由兼容性 |
| **异步函数装饰不当** | 运行时错误 | 中 | `log_manager` 已支持 async,测试异步场景 |
| **参数白名单漏配** | 关键参数未记录 | 低 | 迁移后查看事件文件,补充 whitelist |
| **后台线程资源占用** | 性能下降 | 低 | 使用 `lite` 模式,调整采样间隔 |
| **测试文件 logger 引用** | 测试失败 | 高 | 单独处理测试文件,移除断言中的 logger 验证 |
| **配置路径错误** | 日志未输出 | 中 | 绝对路径配置,验证 base_dir 可写 |
| **marker 过度使用** | 性能影响 | 低 | 仅在关键节点使用,高频循环避免 marker |

---

## 5. 验证检查清单

### 启动验证
- [ ] 服务正常启动,无异常日志
- [ ] `.log-manager/runs/` 目录生成
- [ ] 控制台有格式化的日志输出
- [ ] entry 报告文件生成: `.log-manager/reports/{session}/entries/*/latest.txt`

### 功能验证
- [ ] `/api/chat/{category}` 正常响应
- [ ] `/api/guess-questions` 正常响应
- [ ] `/api/personnel-dispatch` 正常响应
- [ ] `/api/source-dispatch` 正常响应
- [ ] 会话创建和复用逻辑正常

### 日志验证
- [ ] API 请求生成 entry 报告
- [ ] 调用链完整记录(从入口到服务层)
- [ ] 错误场景生成错误报告
- [ ] 参数脱敏正确(无敏感信息泄露)
- [ ] marker 在关键节点正确记录

### 性能验证
- [ ] 响应时间增加 <5%
- [ ] CPU/内存占用无异常增长
- [ ] 后台线程不影响主业务

### 清理验证
- [ ] 代码中无 `log_decorator` 导入
- [ ] 代码中无 `logger.` 调用
- [ ] 测试全部通过
- [ ] 文档已更新

---

## 6. 回滚方案

如果迁移后出现严重问题:

### 快速回滚
```bash
git checkout main  # 切换回迁移前分支
git branch -D feat/log-manager-migration
```

### 保留数据
- 备份 `.log-manager/` 目录用于问题分析
- 保留迁移分支用于调试

### 回滚条件
- 核心功能不可用
- 性能下降 >10%
- 日志丢失导致无法排查问题

---

## 7. 预期成果

迁移完成后:

- ✅ **日志输出**: 统一到 `.log-manager/` 目录
- ✅ **调用追踪**: 完整的 entry 报告和调用链
- ✅ **错误诊断**: 增强的错误上下文报告
- ✅ **性能监控**: 可选的内存监控(enhanced 模式)
- ✅ **代码简洁**: 移除散落的 logger 调用
- ✅ **可维护性**: 装饰器统一管理,减少样板代码

---

## 8. 关键文件参考

### 需要修改的文件
- `src/rag_stream/main.py` - 应用入口,需要初始化 runtime
- `src/rag_stream/src/routes/chat_routes.py` - API 路由层
- `src/rag_stream/src/services/rag_service.py` - 核心服务
- `src/rag_stream/src/services/chat_general_service.py` - 通用聊天服务
- `src/rag_stream/src/services/dify_service.py` - Dify服务
- `src/rag_stream/src/services/guess_questions_service.py` - 猜你想问服务
- `src/rag_stream/src/services/personnel_dispatch_service.py` - 人员调度服务
- `src/rag_stream/src/services/source_dispath_srvice.py` - 资源调度服务
- `src/rag_stream/src/utils/ragflow_client.py` - RAGFlow客户端
- `src/rag_stream/src/utils/session_manager.py` - 会话管理器

### log-manager API 参考
- `src/log-manager/log_manager/__init__.py` - 导出 API: `configure()`, `entry_trace`, `trace`, `marker()`
- `src/log-manager/log_manager/config.py` - 配置类定义
- `src/log-manager/docs/usage.md` - 使用文档
- `src/log-manager/README.md` - 项目说明

---

**工作流状态**: ✅ 已生成,等待执行

**下一步**: 使用 `/sc:implement claudedocs/workflow_log_migration.md` 开始执行此工作流
