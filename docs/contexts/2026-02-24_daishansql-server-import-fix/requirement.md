# 需求说明

- 问题：`src/rag_stream/main.py` 启动时出现 `ImportError: cannot import name 'Server' from 'DaiShanSQL'`。
- 目标：
  - 以 `src/DaiShanSQL/DaiShanSQL/api_server.py` 为 `Server` 标准实现来源。
  - 修复调用方导入路径。
  - 同时恢复/补齐 `DaiShanSQL` 顶层导出，保持 `from DaiShanSQL import Server` 的兼容性。
