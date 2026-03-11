from ..SQL.sql_utils import MySQLManager
import json
import os
class SQLFixed:
    def __init__(self):
        self.sql_manager = MySQLManager()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        Json_path = os.path.join(current_dir,"data/岱山固定查询.jsonl")
        json_data= self.read_jsonl(Json_path)
        self._last_execution_log = []

    def _record_execution(self, sql_text, result=None, error=""):
        self._last_execution_log.append(
            {
                "sql_text": str(sql_text or ""),
                "result": result,
                "error": str(error or ""),
            }
        )

    def consume_last_execution_log(self):
        logs = list(self._last_execution_log)
        self._last_execution_log = []
        return logs
    def read_jsonl(self,JsonPath):
        data_list = []
        with open(JsonPath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    data_list.append(data)
                except json.JSONDecodeError as e:
                    print(f"第 {line_num} 行 JSON 格式错误: {e}")
                except Exception as e:
                    # 捕获其他异常
                    print(f"读取第 {line_num} 行时发生错误: {e}")
        return data_list
    def sql_companyInfo(self):
        """
 `      1. 基础信息‌：企业总数【】家。
        2. 主要企业类型：有限责任公司【】家，其他（含股份公司、外资等）【】家。
        3. 企业规模‌：大型企业【】家，中型企业【】家，小型企业【】家，微型企业【】家。
        4. 企业标签‌：规上企业【】家，国高企业【】家，专精特新【】家，绿色示范【】家，其他【】家。
        5. 行业分布‌：【】行业【】家，【】行业【】家。
        Returns:
        """
        try:
            search_dict_sql={
                "基础企业总数信息":"""SELECT COUNT(*) AS 企业总数 FROM v_ai_ipark_safety_enterprise_info;""",
                "主要企业类型信息":"""
                SELECT  '有限责任公司【' || COUNT_LLC || '】家，其他（含股份公司、外资等）【' || COUNT_OTHER || '】家。' AS RESULT
                FROM (
                    SELECT 
                        SUM(DECODE(SIGN(INSTR(NVL(enterprise_type, ''), '有限责任公司')), 1, 1, 0)) AS COUNT_LLC,
                        SUM(DECODE(SIGN(INSTR(NVL(enterprise_type, ''), '有限责任公司')), 1, 0, 1)) AS COUNT_OTHER
                    FROM v_ai_ipark_safety_enterprise_info
                ) T;
                """,
                "企业规模信息": """SELECT
                '企业规模：大型企业【' || SUM(DECODE(enterprise_size, '大', 1, 0)) || '】家，' ||
                '中型企业【' || SUM(DECODE(enterprise_size, '中', 1, 0)) || '】家，' ||
                '小型企业【' || SUM(DECODE(enterprise_size, '小', 1, 0)) || '】家，' ||
                '微型企业【' || SUM(DECODE(enterprise_size, '微', 1, 0)) || '】家'
                    AS 企业规模分布 FROM v_ai_ipark_safety_enterprise_info;""",
                "企业标签信息":"""
                SELECT 
                    '规上企业【' || TO_CHAR(count_guishang) || '】家，' ||
                    '国高企业【' || TO_CHAR(count_guogao) || '】家，' ||
                    '专精特新【' || TO_CHAR(count_zhuanjingte) || '】家，' ||
                    '绿色示范【' || TO_CHAR(count_lvse) || '】家，' ||
                    '其他【' || TO_CHAR(count_qita) || '】家' AS result
                FROM (
                    SELECT 
                        -- 规上企业：等值判断，直接用DECODE
                        SUM(DECODE(rules_on_corporate, '1', 1, 0)) AS count_guishang,
                        -- 国高企业：模糊匹配，用INSTR+SIGN+DECODE
                        SUM(DECODE(SIGN(INSTR(NVL(enterprise_label, ''), '国高')), 1, 1, 0)) AS count_guogao,
                        -- 专精特新：模糊匹配，用INSTR+SIGN+DECODE
                        SUM(DECODE(SIGN(INSTR(NVL(enterprise_label, ''), '专精特新')), 1, 1, 0)) AS count_zhuanjingte,
                        -- 绿色示范：模糊匹配，用INSTR+SIGN+DECODE
                        SUM(DECODE(SIGN(INSTR(NVL(enterprise_label, ''), '绿色示范')), 1, 1, 0)) AS count_lvse,
                        -- 其他企业：多条件组合，用DECODE嵌套/逻辑判断
                        SUM(
                            DECODE(
                                -- 先判断是否非规上企业
                                DECODE(rules_on_corporate, '1', 0, 1),
                                1,
                                -- 再判断是否不含国高、专精特新、绿色示范标签
                                DECODE(
                                    SIGN(
                                        INSTR(NVL(enterprise_label, ''), '国高') + 
                                        INSTR(NVL(enterprise_label, ''), '专精特新') + 
                                        INSTR(NVL(enterprise_label, ''), '绿色示范')
                                    ),
                                    0, 1, 0
                                ),
                                0
                            )
                        ) AS count_qita
                    FROM v_ai_ipark_safety_enterprise_info
                ) T
            """,
                "行业分布信息":"""
                SELECT 
                '行业分布‌：' || 
                        LISTAGG(industry_level_two || '行业' || cnt || '家', '，') WITHIN GROUP (ORDER BY cnt DESC) AS result
                    FROM (
                        SELECT 
                            industry_level_two,
                            COUNT(*) AS cnt
                        FROM v_ai_ipark_safety_enterprise_info
                        WHERE industry_level_two IS NOT NULL AND industry_level_two != ''
                        GROUP BY industry_level_two
                    ) T
                        """
            }
            results=[]
            # 变量字典
            for key,value in search_dict_sql.items():
                sql_search=self.sql_manager.request_api_sql(value)
                self._record_execution(value, sql_search)
                data={
                    f"{key}":sql_search
                }
                results.append(data)
            return {
                "数据库查询状态": "success",
                "数据库查询结果": results
            }
        except Exception  as e:
            return {
                "数据库查询状态": "error",
                "数据库查询结果": "请稍后进行查询"
            }
    def sql_ChemicalCompanyInfo(self):
            try:
                    sql_dict={
                        "园区化工企业数目":"""SELECT 
                                        COUNT(*) AS "count",
                                        SUM(DECODE(park_name, '东区', 1, 0)) AS "东区",
                                        SUM(DECODE(park_name, '西区', 1, 0)) AS "西区"
                                        FROM 
                                            v_ai_ipark_safety_enterprise_info
                                        WHERE 
                                            industry_level_two LIKE '%化工%';
                                        """,

                        "园区东区和西区化工企业数目":"""SELECT
                                            '东区【' ||
                                            COUNT(DECODE(park_name, '东区', 1, NULL)) ||  -- COUNT忽略NULL，等价原CASE逻辑
                                            '】家，西区【' ||
                                            COUNT(DECODE(park_name, '西区', 1, NULL)) ||
                                            '】家' AS result
                                        FROM v_ai_ipark_safety_enterprise_info;
                                        """,
                                        
                        "东区化工企业":"""
                                        SELECT 
                                            park_name || '化工企业列表: ' || 
                                            '[' || LISTAGG(enterprise_name, '，') WITHIN GROUP (ORDER BY enterprise_name) || ']' AS 企业列表
                                        FROM v_ai_ipark_safety_enterprise_info
                                        WHERE park_name IN ('东区', '西区')
                                        GROUP BY park_name
                                        ORDER BY park_name;
                                        
                                        """,
                                        
                        "生产状态":"""
                                            SELECT 
                                                '生产状态：正常生产' || 
                                                SUM(DECODE(enterprise_status, '正常生产', 1, 0)) || '家，' ||
                                                '试生产' || 
                                                SUM(DECODE(enterprise_status, '试生产', 1, 0)) || '家，' ||
                                                '未投产' || 
                                                SUM(DECODE(enterprise_status, '未投产', 1, 0)) || '家。' AS result
                                            FROM v_ai_ipark_safety_enterprise_info;
                                    """,
                                    
                        "企业规模": """SELECT
                                            '企业规模：大型企业【' || SUM(DECODE(enterprise_size, '大', 1, 0)) || '】家，' ||
                                            '中型企业【' || SUM(DECODE(enterprise_size, '中', 1, 0)) || '】家，' ||
                                            '小型企业【' || SUM(DECODE(enterprise_size, '小', 1, 0)) || '】家，' ||
                                            '微型企业【' || SUM(DECODE(enterprise_size, '微', 1, 0)) || '】家'
                                            AS 企业规模分布
                                        FROM v_ai_ipark_safety_enterprise_info;""",
                                                                
                        "企业标签": """
                                            SELECT
                                                '专精特新小巨人：' ||
                                                SUM(DECODE(SIGN(INSTR(NVL(enterprise_label, ''), '专精特新小巨人')), 1, 1, 0)) || '家。\n' ||
                                                '高新技术企业：' ||
                                                SUM(DECODE(SIGN(INSTR(NVL(enterprise_label, ''), '高新技术企业')), 1, 1, 0)) || '家。' AS result
                                            FROM v_ai_ipark_safety_enterprise_info;
                                    """,
                                    
                        "重点企业":"""SELECT 
                                '' || 
                                LISTAGG(
                                    enterprise_name || '：' || 
                                    enterprise_name || '位于[' || produce_address || ']，' || 
                                    '厂区面积：' || factory_area || '平方公里，' || 
                                    '统一社会信用代码[' || social_credit_id || ']，' || 
                                    '成立日期[' || establish_date || ']，' || 
                                    '注册资金' || '暂无' || '万元，' || 
                                    '从业人员数量' || practitioner_num || '人。' || 
                                    '企业负责人是' || enterprise_leader_name || '，联系方式为[' || en_leader_mobile_phone || ']。' || 
                                    '安全负责人是' || enterprise_leader_name || '，联系方式为[' || en_leader_mobile_phone || ']。'
                                        , '\n'
                                    ) WITHIN GROUP (ORDER BY enterprise_name) AS result
                                FROM v_ai_ipark_safety_enterprise_info
                                WHERE enterprise_name IN ('浙江世倍尔新材料有限公司', '润和催化材料（浙江）有限公司');
                                """
                        }
                    results = []
                    # 变量字典
                    for key, value in sql_dict.items():
                        sql_search = self.sql_manager.request_api_sql(value)["data"]
                        self._record_execution(value, sql_search)
                        data = {
                            f"{key}": sql_search
                        }
                        results.append(data)
                    return {
                        "数据库查询状态": "success",
                        "数据库查询结果": results
                    }
                    # print(self.sql_manager.request_api_sql(sql_dict['重点企业'])['data'])

            except Exception as e:
                return {
                    "数据库查询状态": "error",
                    "数据库查询结果": "请稍后进行查询"
                }
    def sql_SecuritySituation(self):
        '''
        今日安全承诺：应承诺x条，已承诺x条，未承诺x条。
        进行中的开停车大检修：开车中x条，停车中x条，检修中x条。 
        今日作业情况：今日作业总数x条，进行中x条，已结束x条。其中，重点关注作业，今日动火作业x条，受限空间x条。
        今日人员在线情况：接入总数x个，在线人数x个。 
        物联监测设备状态：园区公共视频总数x路，在线数x，离线数x；企业视频监控总数x路，在线数，离线数x；监测指标总数x，在线数x，离线数x
        园区实时风险指数：截止[yyyy-mm-dd hh:mm:ss],当前园区风险指数为x，风险等级为x。
        今日报警情况：报警总数x，待处理报警x，今日新增报警x。
        '''
        try:
            search_dict_sql={
                            '今日作业情况':'''
                            SELECT
                                NVL(sub."当日作业总数", 0) AS "当日作业总数",
                                NVL(sub."正在进行中作业数", 0) AS "正在进行中作业数",
                                NVL(sub."今日已结束作业数", 0) AS "今日已结束作业数",
                                NVL(sub."今日动火作业数", 0) AS "今日动火作业数",
                                NVL(sub."今日受限空间作业数", 0) AS "今日受限空间作业数"
                            FROM
                                dual  -- 虚拟单行表，保证至少返回一行
                            LEFT JOIN (
                                -- 原有查询逻辑作为子查询
                                SELECT
                                    NVL(main.total_today_work_count, 0) AS "当日作业总数",
                                    NVL(main.ongoing_work_count, 0) AS "正在进行中作业数",
                                    NVL(main.completed_today_work_count, 0) AS "今日已结束作业数",
                                    NVL(special.hot_work_count, 0) AS "今日动火作业数",
                                    NVL(special.confined_space_work_count, 0) AS "今日受限空间作业数"
                                FROM
                                    v_ai_ipark_job_today_duration main
                                LEFT JOIN
                                    v_ai_ipark_job_special_job_today special
                                ON
                                    main.park_code = special.park_code
                                    AND TRUNC(main.query_date) = TRUNC(special.query_date) 
                                WHERE
                                    TRUNC(main.query_date) = CURRENT_DATE
                            ) sub ON 1 = 1; 
                            ''',
                            '园区实时风险指数':'''
                                SELECT 
                                    TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') AS 当前时间,
                                    park_name AS 园区名称,
                                    riskTime AS 风险统计时间,
                                    riskValue AS 园区风险值,
                                    riskLevel AS 园区风险等级
                                FROM 
                                    v_ai_ipark_ra_park_daily_risk_summary_park
                                -- 按风险统计时间降序排序，取最新的一条
                                ORDER BY 
                                    riskTime DESC
                                FETCH FIRST 1 ROWS ONLY;  -- Oracle替代LIMIT 1的语法
                            ''',
                            '今日报警情况':'''
                            SELECT
                            NVL((SELECT COUNT(*) FROM v_ai_ipark_alarm_ai_ledger), 0) AS 报警总数,
                            NVL(SUM(DECODE(t.handleStatus, '待处理', 1, 0)), 0) AS 今日待处理报警数,
                            NVL(COUNT(t.alarmStartTime), 0) AS 今日新增报警数
                        FROM
                            DUAL
                        LEFT JOIN
                            v_ai_ipark_alarm_ai_ledger t ON TRUNC(t.alarmStartTime) = TRUNC(SYSDATE);
                            '''
                        }
            results=[]
            # 变量字典
            for key,value in search_dict_sql.items():
                sql_search=self.sql_manager.request_api_sql(value)
                self._record_execution(value, sql_search)
                data={
                    f"{key}":sql_search
                }
                results.append(data)
            return {
                "数据库查询状态": "success",
                "数据库查询结果": results
            }
        except Exception as e:
            return {
                "数据库查询状态": "error",
                "数据库查询结果": "请稍后进行查询"
            }
    def sql_FixedFieldQuery(self,question):
        

        return
if __name__=="__main__":
    fix=SQLFixed()
    print(fix.sql_companyInfo())
