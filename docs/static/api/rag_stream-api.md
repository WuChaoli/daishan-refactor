# rag_stream API 接口清单

- 生成时间: 2026-02-10 09:50:11
- 项目路径: `src/rag_stream`
- 路由总数: 26

## 路由列表

| Method | Path | Handler | 定义位置 |
|---|---|---|---|
| `GET` | `/` | `root` | `src/rag_stream/main.py:106` |
| `POST` | `/api/accidents` | `chat_accidents` | `src/rag_stream/src/routes/chat_routes.py:106` |
| `GET` | `/api/categories` | `get_categories` | `src/rag_stream/src/routes/chat_routes.py:347` |
| `POST` | `/api/chat/{category}` | `chat_with_category` | `src/rag_stream/src/routes/chat_routes.py:40` |
| `POST` | `/api/emergency` | `chat_emergency` | `src/rag_stream/src/routes/chat_routes.py:100` |
| `POST` | `/api/firmsituation` | `chat_firmsituation` | `src/rag_stream/src/routes/chat_routes.py:201` |
| `POST` | `/api/general` | `chat_general` | `src/rag_stream/src/routes/chat_routes.py:158` |
| `POST` | `/api/guess-questions` | `guess_questions` | `src/rag_stream/src/routes/chat_routes.py:357` |
| `POST` | `/api/laws` | `chat_laws` | `src/rag_stream/src/routes/chat_routes.py:88` |
| `POST` | `/api/msds` | `chat_msds` | `src/rag_stream/src/routes/chat_routes.py:112` |
| `POST` | `/api/park` | `chat_park` | `src/rag_stream/src/routes/chat_routes.py:189` |
| `POST` | `/api/policies` | `chat_policies` | `src/rag_stream/src/routes/chat_routes.py:118` |
| `POST` | `/api/prevent` | `chat_prevent` | `src/rag_stream/src/routes/chat_routes.py:183` |
| `POST` | `/api/safesituation` | `chat_safesituation` | `src/rag_stream/src/routes/chat_routes.py:177` |
| `GET` | `/api/sessions` | `get_all_sessions` | `src/rag_stream/src/routes/chat_routes.py:268` |
| `POST` | `/api/sessions/{category}` | `create_category_session` | `src/rag_stream/src/routes/chat_routes.py:224` |
| `DELETE` | `/api/sessions/{session_id}` | `delete_session` | `src/rag_stream/src/routes/chat_routes.py:279` |
| `GET` | `/api/sessions/{session_id}` | `get_session_info` | `src/rag_stream/src/routes/chat_routes.py:258` |
| `POST` | `/api/special` | `chat_special` | `src/rag_stream/src/routes/chat_routes.py:195` |
| `POST` | `/api/standards` | `chat_standards` | `src/rag_stream/src/routes/chat_routes.py:94` |
| `POST` | `/api/stop` | `stop_session` | `src/rag_stream/src/routes/chat_routes.py:206` |
| `GET` | `/api/user/{user_id}/sessions` | `get_user_sessions` | `src/rag_stream/src/routes/chat_routes.py:245` |
| `POST` | `/api/warn` | `chat_warn` | `src/rag_stream/src/routes/chat_routes.py:171` |
| `GET` | `/health` | `health_check` | `src/rag_stream/src/routes/chat_routes.py:335` |
| `POST` | `/ipark-ae/personnel-dispatch` | `people_dispatch` | `src/rag_stream/src/routes/chat_routes.py:288` |
| `POST` | `/ipark-ae/source-dispatch` | `source_dispatch` | `src/rag_stream/src/routes/chat_routes.py:318` |
