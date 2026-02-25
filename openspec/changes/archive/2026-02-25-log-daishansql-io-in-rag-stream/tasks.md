## 1. Logging Foundation

- [x] 1.1 Define unified `log_manager` field conventions for DaiShanSQL call logs (`method`, `call_site`, `args_preview`, `result_preview`, `duration_ms`, `success`)
- [x] 1.2 Reuse existing serialization/truncation strategy in call-site logging to keep terminal output readable
- [x] 1.3 Add or adjust tests for serialization fallback, truncation behavior, and exception log emission

## 2. Integrate All DaiShanSQL Call Sites In Rag Stream

- [x] 2.1 Add direct `marker` input/output/error logs for `sqlFixed.sql_ChemicalCompanyInfo` and `sqlFixed.sql_SecuritySituation` in `chat_general_service.py`
- [x] 2.2 Add direct `marker` input/output/error logs for `server.get_sql_result` and `server.judgeQuery` in `chat_general_service.py`
- [x] 2.3 Add direct `marker` input/output/error logs for both `QueryBySQL` call paths in `source_dispath_srvice.py`
- [x] 2.4 Replace ad-hoc `print` style around `QueryBySQL` in `fetch_table_structures.py` with `log_manager` style logging where applicable

## 3. Validate Behavior And Observability

- [x] 3.1 Add/adjust tests to verify logs are emitted for success, empty result, and exception paths
- [x] 3.2 Run existing `rag_stream` related tests to ensure no business behavior regression
- [x] 3.3 Perform manual terminal verification to confirm input/output log fields (`call_site`, `method`, `args_preview`, `result_preview`, `duration_ms`, `success`) are present
