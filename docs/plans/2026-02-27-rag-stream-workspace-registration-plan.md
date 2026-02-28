# rag_stream 统一包注册与包名导入计划（修订版）

## 摘要
目标是让 `rag_stream` 引用的本地包全部完成统一注册（`uv workspace`），并在 `rag_stream` 生产代码中只使用包名导入，不再出现 `src.*` 和 `sys.path` 注入。  
你已确认的决策：
1. 注册方式：统一 `workspace`
2. 覆盖范围：先覆盖生产代码（测试暂不强制改）

## 当前基线
1. `rag_stream` 生产代码存在大量 `from src...` 导入。
2. 存在 `sys.path.insert(...)` 运行时路径注入。
3. `rag_stream` 当前无独立 `pyproject.toml`。
4. 被 `rag_stream` 直接引用的本地包：`DaiShanSQL`、`ragflow_sdk`、`dify_sdk`、`log_manager`。
5. 这 4 个包中，`log_manager` 已有 `pyproject.toml`，其余主要是 `setup.py`。

## 统一目标定义
1. 本地包注册统一到 `uv workspace`。
2. `rag_stream` 生产代码仅允许：
`from rag_stream...`
`from DaiShanSQL...` / `from DaiShanSQL import ...`
`from ragflow_sdk...`
`from dify_sdk...`
`from log_manager...`
3. 禁止在 `rag_stream` 生产代码中出现：
`from src...`
`import src...`
`sys.path.insert(...)` / `sys.path.append(...)`

## 实施方案（决策完备）
1. 包元数据统一
- 为 `src/DaiShanSQL`、`src/ragflow_sdk`、`src/dify_sdk` 补齐 `pyproject.toml`（保留原 `setup.py` 兼容历史流程）。
- 确保每个包的 `project.name`（分发名）与实际导入名关系清晰记录。

2. rag_stream 包化
- 新增 `src/rag_stream/pyproject.toml`，声明 `rag-stream` 包及本地依赖。
- 声明 `rag_stream` 包发现规则（`package-dir`/`packages`）。

3. 根工作区统一注册
- 更新根 `pyproject.toml`：
  - 添加 `[tool.uv.workspace]` members，至少包含：
    - `src/rag_stream`
    - `src/DaiShanSQL`
    - `src/ragflow_sdk`
    - `src/dify_sdk`
    - `src/log-manager`
  - 添加 `[tool.uv.sources]` 将本地依赖绑定到 workspace/path（以 workspace 优先）。

4. 生产代码导入替换（仅生产代码）
- 范围：
  - `src/rag_stream/main.py`
  - `src/rag_stream/src/**`
- 规则：
  - `src.* -> rag_stream.*`
  - 外部本地依赖全部改为包名导入（`DaiShanSQL`、`ragflow_sdk`、`dify_sdk`、`log_manager`）。

5. 移除路径注入
- 删除 `rag_stream` 生产代码中的 `sys.path.insert/append`。
- 对因路径注入移除导致的导入失败，改为标准包依赖声明解决，不做运行时补丁。

6. 入口与启动一致性
- 保证以下命令可用：
  - 仓库根：`uv run python -m rag_stream.main`
  - 子目录：`cd src/rag_stream && uv run python -m rag_stream.main`
- 若存在双入口（兼容入口 + 实际入口），明确单一真实入口并保留兼容转发。

7. 文档与门禁
- 更新 `src/rag_stream/README.md` 的依赖与启动说明。
- 增加导入规范门禁（脚本或命令）：
  - 生产代码扫描 `from src.` 必须为 0
  - 生产代码扫描 `sys.path.insert` 必须为 0

## 对外接口/类型影响
1. HTTP API：不做破坏性变更（`/api/*` 保持）。
2. 主要变化是导入路径与包注册方式，不改变业务请求/响应契约。
3. 若发生 import-time 初始化副作用（如外部 key 依赖），改为懒加载以保证模块可导入。

## 验证与验收
1. 注册验证
- `uv` 能解析 workspace 成员，无命名冲突。
- 根目录与子目录都可完成 `import rag_stream` 与依赖导入。

2. 导入规范验证（生产代码）
- `rg "from src\\.|import src\\." src/rag_stream/main.py src/rag_stream/src` 返回 0。
- `rg "sys.path.insert|sys.path.append" src/rag_stream/main.py src/rag_stream/src` 返回 0。

3. 启动验证
- 两种启动命令可正常启动应用（端口冲突单独标注为环境问题，不视为导入失败）。

4. 最小回归验证
- 跑与导入链直接相关的关键测试子集（本轮不要求全量测试迁移）。

## 风险与对应策略
1. 风险：`setup.py` 到 `pyproject.toml` 迁移引发打包细节差异。
- 策略：先补 `pyproject.toml`，保留 `setup.py`；以导入可用和 workspace 解析通过为第一验收。

2. 风险：移除 `sys.path` 后暴露隐藏循环依赖或初始化时机问题。
- 策略：用懒加载替代顶层重初始化，避免 import-time 失败。

3. 风险：包名与分发名不一致导致依赖声明混淆。
- 策略：在计划实施文档中显式给出“分发名 -> 导入名”映射表并用于校验。

## 显式假设
1. 本轮只治理生产代码导入；`src/rag_stream/tests` 的 `src.*` 后续单独阶段治理。
2. 依赖管理统一使用 `uv` 与项目 `.venv`。
3. 不做跨仓发布，仅做仓内可解析、可启动、可调用。
