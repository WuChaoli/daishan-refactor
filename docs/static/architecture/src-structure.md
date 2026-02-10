# src 目录结构与项目 API 清单

- 生成时间: 2026-02-10 09:45:09
- 激活员工: `architect-师爷`
- 生成方式: `architecture-generator` 的结构扫描 + 路由解析

## 1. src 顶层项目概览

| 项目目录 | Python 文件数 | HTTP API 路由数 | 说明 |
|---|---:|---:|---|
| `DaiShanSQL` | 15 | 0 | 未检测到 HTTP 路由装饰器 |
| `dify_sdk` | 17 | 0 | 未检测到 HTTP 路由装饰器 |
| `Digital_human_command_interface` | 9 | 4 | FastAPI 服务 |
| `log_decorator` | 5 | 0 | 未检测到 HTTP 路由装饰器 |
| `logs` | 0 | 0 | 未检测到 HTTP 路由装饰器 |
| `rag_stream` | 49 | 26 | FastAPI 服务 |
| `ragflow_sdk` | 19 | 0 | 未检测到 HTTP 路由装饰器 |

## 2. src 文件结构树

- 总文件数: 202
- 扩展名统计（Top 8）: `.py`: 114, `.log`: 23, `.md`: 17, `.txt`: 12, `.xlsx`: 10, `.json`: 9, `(no ext)`: 8, `.yaml`: 4

```text
src/
├── DaiShanSQL/
│   ├── DaiShanSQL/
│   │   ├── SQL/
│   │   │   ├── __pycache__/
│   │   │   ├── SQLAgent_toSql.py
│   │   │   ├── __init__.py
│   │   │   ├── sql_fixed.py
│   │   │   └── sql_utils.py
│   │   ├── Utils/
│   │   │   ├── __pycache__/
│   │   │   ├── data/
│   │   │   │   ├── 岱山字段结果.jsonl
│   │   │   │   └── 岱山生成问题与SQL.jsonl
│   │   │   ├── AsynchronousCall.py
│   │   │   ├── OpenAI_utils.py
│   │   │   ├── ProcessUtils.py
│   │   │   ├── Prompt_Templete.py
│   │   │   ├── __init__.py
│   │   │   ├── api_intent.py
│   │   │   └── tools.py
│   │   ├── __pycache__/
│   │   ├── .env
│   │   ├── __init__.py
│   │   └── api_server.py
│   ├── DaiShanSQL.egg-info/
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   └── top_level.txt
│   ├── __pycache__/
│   ├── __init__.py
│   └── setup.py
├── Digital_human_command_interface/
│   ├── __pycache__/
│   ├── logs/
│   │   ├── archive/
│   │   ├── functions/
│   │   │   └── ragflow_client.log
│   │   └── global/
│   │       ├── debug.log
│   │       ├── error.log
│   │       ├── info.log
│   │       └── timing.log
│   ├── src/
│   │   ├── __pycache__/
│   │   ├── api/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── intent_judgment.py
│   │   ├── models.py
│   │   └── ragflow_client.py
│   ├── .env
│   ├── .gitignore
│   ├── README.md
│   ├── config.yaml
│   ├── main.py
│   ├── pyproject.toml
│   ├── test.py
│   ├── uv.lock
│   ├── 接口文档.md
│   └── 运行文档.md
├── dify_sdk/
│   ├── __pycache__/
│   ├── core/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── config_loader.py
│   │   └── exceptions.py
│   ├── dify_sdk.egg-info/
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── requires.txt
│   │   └── top_level.txt
│   ├── http/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── models/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── file.py
│   │   └── workflow.py
│   ├── parsers/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── block.py
│   │   └── streaming.py
│   ├── __init__.py
│   ├── client.py
│   └── setup.py
├── log_decorator/
│   ├── __pycache__/
│   ├── README.md
│   ├── UPDATELOG.md
│   ├── __init__.py
│   ├── config.py
│   ├── decorator.py
│   ├── log_config.yaml
│   ├── mermaid.py
│   └── parser.py
├── logs/
│   ├── chat_with_category.log
│   ├── error.log
│   ├── global.log
│   └── root.log
├── rag_stream/
│   ├── __pycache__/
│   ├── src/
│   │   ├── __pycache__/
│   │   ├── config/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── models/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   ├── emergency_entities.py
│   │   │   └── schemas.py
│   │   ├── routes/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   └── chat_routes.py
│   │   ├── services/
│   │   │   ├── __pycache__/
│   │   │   ├── intent_service/
│   │   │   │   ├── __pycache__/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_intent_service.py
│   │   │   │   └── intent_service.py
│   │   │   ├── __init__.py
│   │   │   ├── chat_general_service.py
│   │   │   ├── dify_service.py
│   │   │   ├── guess_questions_service.py
│   │   │   ├── intent_mapping.example.json
│   │   │   ├── personnel_dispatch_service.py
│   │   │   ├── rag_service.py
│   │   │   └── source_dispath_srvice.py
│   │   ├── utils/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   ├── dify_client_factory.py
│   │   │   ├── fetch_table_structures.py
│   │   │   ├── geo_utils.py
│   │   │   ├── prompts.py
│   │   │   ├── ragflow_client.py
│   │   │   ├── session_manager.py
│   │   │   ├── source_type_mapping.json
│   │   │   └── table_structures.json
│   │   └── __init__.py
│   ├── static/
│   │   └── chat-test.html
│   ├── table_structure/
│   │   ├── IPARK_AE_ACCIDENT_EVENT.xlsx
│   │   ├── IPARK_AE_DEFEND_TARGET.xlsx
│   │   ├── IPARK_AE_EMERGENCY_EXPERT.xlsx
│   │   ├── IPARK_AE_EMERGENCY_SUPPLIES.xlsx
│   │   ├── IPARK_AE_FIRE_PROTECTION.xlsx
│   │   ├── IPARK_AE_MATERIEL_TYPE.xlsx
│   │   ├── IPARK_AE_MEDICAL_INSTITUTION.xlsx
│   │   ├── IPARK_AE_RESCUE_INSTITUTION.xlsx
│   │   ├── IPARK_AE_RESCUE_TEAM.xlsx
│   │   └── IPARK_AE_SHELTER.xlsx
│   ├── tests/
│   │   ├── __pycache__/
│   │   ├── logs/
│   │   │   ├── archive/
│   │   │   ├── functions/
│   │   │   │   ├── source_dispatch.log
│   │   │   │   ├── source_dispatch_SourceType.医疗机构.log
│   │   │   │   ├── source_dispatch_SourceType.应急专家.log
│   │   │   │   ├── source_dispatch_SourceType.应急物资.log
│   │   │   │   ├── source_dispatch_SourceType.救援机构.log
│   │   │   │   ├── source_dispatch_SourceType.救援队伍.log
│   │   │   │   ├── source_dispatch_SourceType.消防设施.log
│   │   │   │   └── source_dispatch_SourceType.避难场所.log
│   │   │   └── global/
│   │   │       ├── debug.log
│   │   │       ├── error.log
│   │   │       ├── info.log
│   │   │       └── timing.log
│   │   ├── TEST_DOCUMENTATION_INDEX.md
│   │   ├── TEST_RESULTS.md
│   │   ├── __init__.py
│   │   ├── test_base_intent_service.py
│   │   ├── test_chat_routes.py
│   │   ├── test_comprehensive_output.log
│   │   ├── test_dify_client_factory.py
│   │   ├── test_dify_integration.py
│   │   ├── test_emergency_resources.py
│   │   ├── test_geo_utils.py
│   │   ├── test_intent_classification.py
│   │   ├── test_intent_classification_report.md
│   │   ├── test_intent_classification_results.json
│   │   ├── test_intent_judgment_general.py
│   │   ├── test_intent_recognizer.py
│   │   ├── test_intent_service_mock.py
│   │   ├── test_personnel_dispatch_service.py
│   │   ├── test_query_by_sql.py
│   │   ├── test_rag_service_stream_end.py
│   │   ├── test_results.json
│   │   ├── test_settings_database_mapping_compat.py
│   │   ├── test_source_dispatch.py
│   │   ├── test_source_dispatch_complete.py
│   │   ├── test_source_dispatch_comprehensive.py
│   │   ├── test_source_dispatch_comprehensive_output.log
│   │   ├── test_source_dispatch_comprehensive_plan.md
│   │   ├── test_source_dispatch_comprehensive_report.md
│   │   ├── test_source_dispatch_comprehensive_results.json
│   │   ├── test_source_dispatch_dify.py
│   │   ├── test_source_dispatch_failed_analysis.md
│   │   ├── test_source_dispatch_failed_cases.json
│   │   ├── test_source_dispatch_multi.py
│   │   ├── test_source_dispatch_resource.py
│   │   ├── test_source_dispatch_resource_results.json
│   │   ├── test_source_dispatch_results.json
│   │   ├── test_source_dispatch_sorting.py
│   │   ├── test_source_dispatch_sorting_unit.py
│   │   └── test_source_dispatch_summary.md
│   ├── .env
│   ├── .gitignore
│   ├── API接口文档.md
│   ├── README.md
│   ├── chatID记录.md
│   ├── config.yaml
│   ├── main.py
│   ├── requirements.txt
│   ├── 快速启动.md
│   └── 运行文档.md
└── ragflow_sdk/
    ├── __pycache__/
    ├── config/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── default.yaml
    │   └── manager.py
    ├── core/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── client.py
    │   └── exceptions.py
    ├── http/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   └── client.py
    ├── models/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── chats.py
    │   ├── chunks.py
    │   ├── datasets.py
    │   └── documents.py
    ├── parsers/
    │   ├── __pycache__/
    │   ├── __init__.py
    │   ├── base.py
    │   └── ragflow.py
    ├── ragflow_sdk.egg-info/
    │   ├── PKG-INFO
    │   ├── SOURCES.txt
    │   ├── dependency_links.txt
    │   ├── requires.txt
    │   └── top_level.txt
    ├── utils/
    │   ├── __pycache__/
    │   └── helpers.py
    ├── __init__.py
    └── setup.py
```