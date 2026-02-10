# digital_human_command_interface API 接口清单

- 生成时间: 2026-02-10 09:50:11
- 项目路径: `src/Digital_human_command_interface`
- 路由总数: 4

## 路由列表

| Method | Path | Handler | 定义位置 |
|---|---|---|---|
| `GET` | `/` | `root` | `src/Digital_human_command_interface/src/api/routes.py:974` |
| `POST` | `/api/stream-chat` | `instrcution_command` | `src/Digital_human_command_interface/src/api/routes.py:1132` |
| `GET` | `/health` | `health_check` | `src/Digital_human_command_interface/src/api/routes.py:987` |
| `POST` | `/intent` | `intent_recognition` | `src/Digital_human_command_interface/src/api/routes.py:1037` |
