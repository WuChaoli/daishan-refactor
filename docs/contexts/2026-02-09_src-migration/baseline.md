# 阶段1迁移基线

## 目录快照（迁移前）

- .claude
- .company
- .git
- .pytest_cache
- .serena
- .venv
- .vscode
- DaiShanSQL
- Digital_human_command_interface
- __pycache__
- dify_sdk
- docs
- log_decorator
- logs
- rag_stream
- ragflow_sdk
- scripts
- tests

## 目标迁移项目

- Digital_human_command_interface
- rag_stream
- DaiShanSQL
- dify_sdk
- ragflow_sdk
- log_decorator

## 入口文件清单（迁移前）

DaiShanSQL/DaiShanSQL/Utils/api_intent.py:46:if __name__ == '__main__':
rag_stream/main.py:111:if __name__ == "__main__":
rag_stream/tests/test_query_by_sql.py:161:if __name__ == "__main__":
DaiShanSQL/DaiShanSQL/Utils/AsynchronousCall.py:220:if __name__ == "__main__":
DaiShanSQL/DaiShanSQL/Utils/ProcessUtils.py:141:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_complete.py:282:if __name__ == "__main__":
DaiShanSQL/DaiShanSQL/Utils/OpenAI_utils.py:170:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_comprehensive.py:396:if __name__ == "__main__":
DaiShanSQL/DaiShanSQL/SQL/sql_utils.py:36:if __name__ == "__main__":
rag_stream/tests/test_chat_routes.py:376:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_sorting.py:215:if __name__ == "__main__":
DaiShanSQL/DaiShanSQL/SQL/SQLAgent_toSql.py:119:if __name__ == '__main__':
rag_stream/tests/test_source_dispatch.py:103:if __name__ == "__main__":
rag_stream/tests/test_intent_classification.py:390:if __name__ == "__main__":
rag_stream/tests/test_intent_service_mock.py:362:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_sorting_unit.py:217:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_resource.py:230:if __name__ == "__main__":
Digital_human_command_interface/test.py:53:if __name__ == "__main__":
rag_stream/tests/test_emergency_resources.py:259:if __name__ == "__main__":
rag_stream/src/services/fetch_table_structures.py:166:if __name__ == "__main__":
Digital_human_command_interface/main.py:223:if __name__ == "__main__":
rag_stream/tests/test_source_dispatch_multi.py:156:if __name__ == "__main__":
rag_stream/src/services/dify_client_factory_example.py:68:if __name__ == "__main__":

## 硬编码路径/导入风险扫描（迁移前）

log_decorator/__init__.py:10:    from log_decorator import log
log_decorator/config.py:37:    3. log_decorator目录的log_config.yaml（默认配置）
log_decorator/config.py:51:        # 查找顺序：项目根目录 -> log_decorator目录
log_decorator/UPDATELOG.md:1:# log_decorator 更新日志
log_decorator/UPDATELOG.md:7:本次文档更新基于 `log_decorator` 当前代码行为，重点修正与补充：
log_decorator/README.md:1:# log_decorator
log_decorator/README.md:3:`log_decorator` 是一个轻量级函数日志装饰器，核心目标是：
log_decorator/README.md:23:from log_decorator import log
log_decorator/README.md:80:from log_decorator import log
log_decorator/README.md:153:from log_decorator.parser import parse_obj
log_decorator/README.md:162:from log_decorator import log
log_decorator/README.md:182:2. `log_decorator/log_config.yaml`
log_decorator/README.md:206:log_decorator/
log_decorator/README.md:231:from log_decorator import log, logger, parse_obj, load_config
DaiShanSQL/__init__.py:2:DaiShanSQL - 岱山 SQL 查询包
DaiShanSQL/__init__.py:8:from DaiShanSQL.DaiShanSQL.api_server import Server
DaiShanSQL/__init__.py:9:from DaiShanSQL.DaiShanSQL.SQL.SQLAgent_toSql import SQLAgent
DaiShanSQL/__init__.py:10:from DaiShanSQL.DaiShanSQL.SQL.sql_utils import MySQLManager
DaiShanSQL/__init__.py:11:from DaiShanSQL.DaiShanSQL.SQL.sql_fixed import SQLFixed
DaiShanSQL/setup.py:4:    name="DaiShanSQL",          # 包名（外部导入时用这个名字）
DaiShanSQL/DaiShanSQL/__init__.py:2:DaiShanSQL - 岱山 SQL 查询包
DaiShanSQL/DaiShanSQL/__init__.py:11:# 加载 DaiShanSQL 模块的 .env 文件
DaiShanSQL/DaiShanSQL/__init__.py:12:_module_dir = Path(__file__).resolve().parent
rag_stream/运行文档.md:2:conda create -n rag_stream python=3.9 -y
rag_stream/运行文档.md:5:conda activate rag_stream
rag_stream/src/__init__.py:4:# 添加项目根目录到 Python 路径，确保可以导入 log_decorator
rag_stream/src/__init__.py:5:project_root = Path(__file__).parent.parent.parent
rag_stream/src/__init__.py:7:    sys.path.insert(0, str(project_root))
rag_stream/README.md:172:> 说明：历史遗留的 `rag_stream/.env` 仅为兼容保留，重构后的配置加载默认不再读取该文件。
rag_stream/main.py:6:# 添加项目根目录到 Python 路径，以便导入 log_decorator
rag_stream/main.py:9:    sys.path.insert(0, project_root)
rag_stream/main.py:15:from log_decorator import log, logger
rag_stream/main.py:17:# 加载 rag_stream 的 .env 文件（包含 DIFY 配置）
rag_stream/main.py:18:rag_stream_env_path = Path(__file__).parent / ".env"
rag_stream/main.py:19:if rag_stream_env_path.exists():
rag_stream/main.py:20:    load_dotenv(rag_stream_env_path)
rag_stream/main.py:21:    logger.info(f"✓ 已加载 rag_stream 环境变量: {rag_stream_env_path}")
rag_stream/main.py:23:    logger.warning(f"⚠ rag_stream .env 文件不存在: {rag_stream_env_path}")
rag_stream/main.py:25:# 加载 DaiShanSQL 的 .env 文件（包含 OPENAI_API_KEY 等配置）
rag_stream/main.py:26:daishan_env_path = Path(__file__).parent.parent / "DaiShanSQL" / "DaiShanSQL" / ".env"
rag_stream/main.py:29:    logger.info(f"✓ 已加载 DaiShanSQL 环境变量: {daishan_env_path}")
rag_stream/main.py:31:    logger.warning(f"⚠ DaiShanSQL .env 文件不存在: {daishan_env_path}")
rag_stream/main.py:99:static_dir = Path(__file__).parent / "static"
rag_stream/src/utils/session_manager.py:8:from log_decorator import log, logger
rag_stream/src/services/dify_service.py:10:from log_decorator import log, logger
rag_stream/tests/test_emergency_resources.py:11:project_root = Path(__file__).parent.parent.parent
rag_stream/tests/test_emergency_resources.py:12:sys.path.insert(0, str(project_root / "DaiShanSQL"))
rag_stream/tests/test_emergency_resources.py:13:sys.path.insert(0, str(project_root / "rag_stream"))
rag_stream/tests/test_emergency_resources.py:25:from DaiShanSQL import Server
rag_stream/tests/test_emergency_resources.py:43:        # 创建DaiShanSQL Server实例
rag_stream/tests/test_emergency_resources.py:47:        mapping_file = project_root / "rag_stream/src/services/source_type_mapping.json"
rag_stream/tests/test_emergency_resources.py:246:    output_file = project_root / "rag_stream/tests/test_results.json"
rag_stream/src/routes/chat_routes.py:10:from log_decorator import log, logger
rag_stream/src/services/intent_service.py:9:from log_decorator import log, logger
rag_stream/src/services/intent_service.py:12:# import DaiShanSQL.DaiShanSQL.api_server
rag_stream/src/services/intent_service.py:13:from DaiShanSQL import Server
rag_stream/src/services/intent_service.py:40:        # DaiShanSQL 现在使用动态导入，不需要预先初始化
rag_stream/src/services/intent_service.py:134:        集成 DaiShanSQL 模块,执行 SQL 查询
rag_stream/src/services/intent_service.py:167:                f"调用 DaiShanSQL, questions: {questions[:3]}... (共{len(questions)}个)"
rag_stream/src/services/intent_service.py:170:            # 调用 DaiShanSQL
rag_stream/src/services/intent_service.py:178:            logger.info(f"DaiShanSQL 查询完成")
rag_stream/src/services/intent_service.py:192:            logger.error(f"导入 DaiShanSQL 模块失败: {str(ie)}", exc_info=True)
rag_stream/src/services/intent_service.py:193:            return {"type": 2, "data": {"error": f"DaiShanSQL 模块未找到: {str(ie)}"}}
rag_stream/src/config/settings.py:305:    用于 DaiShanSQL 的 OpenAI 兼容接口配置
rag_stream/src/config/settings.py:323:    用于 DaiShanSQL 的数据库连接配置
rag_stream/src/config/settings.py:491:    """获取项目根目录（rag_stream 目录）"""
rag_stream/src/config/settings.py:492:    return Path(__file__).resolve().parents[2]
rag_stream/src/config/settings.py:499:    加载 rag_stream/.env - 包含 DIFY 相关配置
rag_stream/src/config/settings.py:503:    # 加载 rag_stream 的 .env 文件
rag_stream/src/config/settings.py:504:    rag_stream_env_path = base_dir / ".env"
rag_stream/src/config/settings.py:505:    if rag_stream_env_path.exists():
rag_stream/src/config/settings.py:506:        load_dotenv(rag_stream_env_path, override=False)
rag_stream/tests/test_rag_service_stream_end.py:8:# 添加 rag_stream 目录到 Python 路径，确保可以 import src.*
rag_stream/tests/test_rag_service_stream_end.py:9:rag_stream_path = Path(__file__).parent.parent
rag_stream/tests/test_rag_service_stream_end.py:10:sys.path.insert(0, str(rag_stream_path))
rag_stream/tests/test_query_by_sql.py:1:"""测试 DaiShanSQL QueryBySQL 方法的测试文件"""
rag_stream/tests/test_query_by_sql.py:6:# 添加 DaiShanSQL 目录到 Python 路径
rag_stream/tests/test_query_by_sql.py:7:project_root = Path(__file__).parent.parent.parent
rag_stream/tests/test_query_by_sql.py:8:daishan_sql_path = project_root / "DaiShanSQL"
rag_stream/tests/test_query_by_sql.py:9:sys.path.insert(0, str(daishan_sql_path))
rag_stream/tests/test_query_by_sql.py:12:from DaiShanSQL import Server
rag_stream/tests/test_source_dispatch_failed_cases.json:22:    "traceback": "Traceback (most recent call last):\n  File \"/home/wuchaoli/codespace/daishan-refactor/rag_stream/tests/test_source_dispatch_comprehensive.py\", line 125, in test_source_dispatch\n    request = SourceDispatchRequest(\n              ^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/wuchaoli/codespace/daishan-master/.venv/lib/python3.12/site-packages/pydantic/main.py\", line 164, in __init__\n    __pydantic_self__.__pydantic_validator__.validate_python(data, self_instance=__pydantic_self__)\npydantic_core._pydantic_core.ValidationError: 1 validation error for SourceDispatchRequest\naccidentId\n  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.5/v/string_too_short\n"
rag_stream/tests/test_source_dispatch_failed_cases.json:47:    "traceback": "Traceback (most recent call last):\n  File \"/home/wuchaoli/codespace/daishan-refactor/rag_stream/tests/test_source_dispatch_comprehensive.py\", line 125, in test_source_dispatch\n    request = SourceDispatchRequest(\n              ^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/wuchaoli/codespace/daishan-master/.venv/lib/python3.12/site-packages/pydantic/main.py\", line 164, in __init__\n    __pydantic_self__.__pydantic_validator__.validate_python(data, self_instance=__pydantic_self__)\npydantic_core._pydantic_core.ValidationError: 1 validation error for SourceDispatchRequest\nsourceType\n  Input should be 'emergencySupplies', 'rescueTeam', 'emergencyExpert', 'fireFightingFacilities', 'shelter', 'medicalInstitution', 'rescueOrganization' or 'protectionTarget' [type=literal_error, input_value='invalidType', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.5/v/literal_error\n"
rag_stream/tests/test_source_dispatch_resource.py:12:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
rag_stream/tests/test_source_dispatch_resource.py:216:        result_file = Path(__file__).parent / "test_source_dispatch_resource_results.json"
rag_stream/tests/test_source_dispatch_complete.py:12:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
rag_stream/tests/test_source_dispatch_complete.py:39:        from DaiShanSQL import Server
rag_stream/tests/test_source_dispatch_complete.py:268:        result_file = Path(__file__).parent / "test_source_dispatch_results.json"
rag_stream/tests/test_intent_service_mock.py:17:project_root = Path(__file__).parents[2]
rag_stream/tests/test_intent_service_mock.py:18:sys.path.insert(0, str(project_root))
rag_stream/tests/test_intent_service_mock.py:20:from rag_stream.src.services.intent_judgment import IntentResult, QueryResult
rag_stream/tests/test_intent_service_mock.py:21:from rag_stream.src.services.log_manager import LogManager
rag_stream/tests/test_intent_service_mock.py:22:from rag_stream.src.services.intent_service import IntentService
rag_stream/tests/test_intent_service_mock.py:23:from rag_stream.src.services.ragflow_client import RetrievalResult
rag_stream/tests/test_chat_routes.py:12:# 添加 rag_stream 目录到 Python 路径
rag_stream/tests/test_chat_routes.py:13:rag_stream_path = Path(__file__).parent.parent
rag_stream/tests/test_chat_routes.py:14:sys.path.insert(0, str(rag_stream_path))
rag_stream/tests/test_source_dispatch_dify.py:57:        # Mock DaiShanSQL Server
rag_stream/tests/test_source_dispatch_dify.py:126:            # Mock DaiShanSQL Server
Digital_human_command_interface/src/intent_judgment.py:11:from log_decorator import log, logger
Digital_human_command_interface/src/__init__.py:8:# 添加项目根目录到 Python 路径，以便导入 log_decorator
Digital_human_command_interface/src/__init__.py:11:    sys.path.insert(0, project_root)
rag_stream/tests/test_source_dispatch.py:10:# 添加 rag_stream 目录（用于导入 src 包）
rag_stream/tests/test_source_dispatch.py:11:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
rag_stream/tests/test_source_dispatch_multi.py:10:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
Digital_human_command_interface/main.py:15:    sys.path.insert(0, project_root)
Digital_human_command_interface/main.py:23:from log_decorator import log, logger
Digital_human_command_interface/main.py:26:env_path = os.path.join(os.path.dirname(__file__), ".env")
Digital_human_command_interface/main.py:47:        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
Digital_human_command_interface/main.py:229:        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
rag_stream/src/services/intent_judgment.py:9:from log_decorator import log, logger
rag_stream/src/services/source_dispath_srvice.py:24:from log_decorator import log, logger
rag_stream/src/services/source_dispath_srvice.py:25:from DaiShanSQL import Server
rag_stream/src/services/source_dispath_srvice.py:28:MAPPING_FILE = Path(__file__).parent / "source_type_mapping.json"
Digital_human_command_interface/src/api/routes.py:18:from log_decorator import log, logger
Digital_human_command_interface/src/api/routes.py:144:        # 获取 DaiShanSQL 目录路径
Digital_human_command_interface/src/api/routes.py:145:        db_search_dir = Path(__file__).parent.parent / "DaiShanSQL"
Digital_human_command_interface/src/api/routes.py:151:            sys.path.insert(0, db_search_dir_str)
Digital_human_command_interface/src/api/routes.py:157:        api_server_module = importlib.import_module("DaiShanSQL")
Digital_human_command_interface/src/api/routes.py:466:        sql_result: DaiShanSQL 返回的结果
Digital_human_command_interface/src/api/routes.py:468:            格式1 (DaiShanSQL 实际返回):
Digital_human_command_interface/src/api/routes.py:489:        # DaiShanSQL 实际返回的格式
Digital_human_command_interface/src/api/routes.py:517:    # 如果有 SQL 查询语句，显示这部分（DaiShanSQL 返回的 '数据库查询' 字段）
Digital_human_command_interface/src/api/routes.py:540:    集成 DaiShanSQL 模块,执行 SQL 查询
Digital_human_command_interface/src/api/routes.py:548:    1. 调用 DaiShanSQL 获取 SQL 查询结果
Digital_human_command_interface/src/api/routes.py:560:        # 导入 DaiShanSQL 模块
Digital_human_command_interface/src/api/routes.py:566:            # 获取 DaiShanSQL 目录的绝对路径
Digital_human_command_interface/src/api/routes.py:567:            # routes.py 位于 src/api/,需要向上两级到 src/,然后进入 DaiShanSQL/
Digital_human_command_interface/src/api/routes.py:568:            # 注意: 包内使用 from DaiShanSQL.xxx 导入，所以需要添加父目录
Digital_human_command_interface/src/api/routes.py:569:            db_search_dir = Path(__file__).parent.parent / "DaiShanSQL"
Digital_human_command_interface/src/api/routes.py:575:                sys.path.insert(0, db_search_dir_str)
Digital_human_command_interface/src/api/routes.py:579:            # 由于 DaiShanSQL 父目录在 sys.path 中,使用包名导入
Digital_human_command_interface/src/api/routes.py:582:            api_server_module = importlib.import_module("DaiShanSQL")
Digital_human_command_interface/src/api/routes.py:611:            # ======== Step 1: 调用 DaiShanSQL (保持原有逻辑) ========
Digital_human_command_interface/src/api/routes.py:694:                    {"error": f"DaiShanSQL 模块未找到: {str(ie)}"}
rag_stream/src/services/rag_service.py:11:from log_decorator import log, logger
rag_stream/src/services/personnel_dispatch_service.py:10:from log_decorator import log, logger
Digital_human_command_interface/src/ragflow_client.py:15:from log_decorator import log, logger
rag_stream/tests/test_intent_classification.py:15:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
rag_stream/tests/test_intent_classification.py:18:env_path = Path(__file__).parent.parent / '.env'
rag_stream/tests/test_intent_classification.py:365:        output_file = Path(__file__).parent / "test_intent_classification_results.json"
rag_stream/src/services/fetch_table_structures.py:10:# 添加 DaiShanSQL 目录到 Python 路径
rag_stream/src/services/fetch_table_structures.py:11:project_root = Path(__file__).parent.parent.parent.parent
rag_stream/src/services/fetch_table_structures.py:12:daishan_sql_path = project_root / "DaiShanSQL"
rag_stream/src/services/fetch_table_structures.py:13:sys.path.insert(0, str(daishan_sql_path))
rag_stream/src/services/fetch_table_structures.py:15:from DaiShanSQL import Server
rag_stream/src/services/fetch_table_structures.py:23:        server: DaiShanSQL Server 实例
rag_stream/src/services/fetch_table_structures.py:127:    current_dir = Path(__file__).parent
rag_stream/src/services/ragflow_client.py:12:from log_decorator import log, logger
rag_stream/tests/test_source_dispatch_comprehensive.py:15:sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
rag_stream/tests/test_source_dispatch_comprehensive.py:21:from DaiShanSQL import Server
rag_stream/tests/test_source_dispatch_comprehensive.py:359:        result_file = Path(__file__).parent / "test_source_dispatch_comprehensive_results.json"
rag_stream/tests/test_source_dispatch_comprehensive.py:380:            failed_file = Path(__file__).parent / "test_source_dispatch_failed_cases.json"
rag_stream/tests/TEST_DOCUMENTATION_INDEX.md:32:cd /home/wuchaoli/codespace/daishan-refactor/rag_stream
