# 设计说明

## 根因

`src/DaiShanSQL/` 目录缺失顶层 `__init__.py` 时，`DaiShanSQL` 会被解释为命名空间包，`from DaiShanSQL import Server` 无法直接获得符号导出，导致 ImportError。

## 修复策略

1. 调用方显式使用标准实现路径导入：
   - `from DaiShanSQL.DaiShanSQL.api_server import Server`
2. 增加 `src/DaiShanSQL/__init__.py` 顶层兼容导出：
   - `Server`、`SQLAgent`、`MySQLManager`、`SQLFixed`

这样可以同时满足“标准路径一致性”和“历史调用兼容”。
