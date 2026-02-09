class ProcessUtils:
    '''
    基于规则对匹配到的表进行扩充
    '''
    def __init__(self):
        self.avaliable_function = {
            "v_ai_ipark_hm_hazard_info_detail": self.process_weixianyuan,
            "v_ai_ipark_hm_hazard_info": self.process_weixianyuan,
            "v_ai_ipark_hm_monitor_metric": self.process_weixianyuan,
            "v_ai_ipark_hm_defend_statistics_company": self.process_weixianyuan,
            "v_ai_ipark_hm_warning_event": self.process_weixianyuan,
            # "v_ai_ipark_hm_company_promise_today": self.process_zuoyeshuo,
            # "v_ai_ipark_job_special_job_key_today": self.process_zuoyeshuo,
            # "v_ai_ipark_job_special_job_today": self.process_zuoyeshuo,
            "v_ai_ipark_alarm_job": self.process_baojing,
            "v_ai_ipark_alarm_monitor": self.process_baojing,
            "v_ai_ipark_alarm_ai_ledger": self.process_baojing,
            "v_ai_ipark_ra_daily_risk_summary_company": self.process_fengxian,
            "v_ai_ipark_ra_latest_risk_snapshot": self.process_fengxian,
            "v_ai_ipark_hm_company_promise": self.process_fengxian,
            "v_ai_ipark_ipark_dp_risk_obj": self.process_fengxiangAnalysis,
            "v_ai_ipark_dp_evaluation": self.process_fengxiangAnalysis,
            "v_ai_ipark_hm_chemical":self.process_chemical,
            "v_ai_ipark_hm_chemical_detail":self.process_chemical,
            "v_ai_ipark_hm_hazard_info":self.process_hazard_info,
            "v_ai_ipark_hm_hazard_info_detail":self.process_hazard_info,
            "v_ai_ipark_hm_craft":self.process_craft,
            "v_ai_ipark_hm_craft_detail":self.process_craft
        }

    # 危险源
    def process_weixianyuan(self, query, origin_table):
        if any(keyword in query for keyword in [
            "重大危险源名称", "危险源等级", "重大危险源分类", "投用日期", "生产状态（中文）", "主要负责人",
            "主要负责人联系方式", "技术负责人", "技术负责人联系方式", "操作负责人", "操作负责人联系方式",
            "联系方式"
        ]):
            return ["v_ai_ipark_hm_hazard_info_detail"]

        elif any(keyword in query for keyword in [
            "危险源类型", "重大危险源等级", "危险源等级"
        ]):
            return ["v_ai_ipark_hm_hazard_info"]

        elif any(keyword in query for keyword in [
            "指标名称", "指标位号", "企业名称", "设备设施名称"
        ]):
            return ["v_ai_ipark_hm_monitor_metric"]

        elif any(keyword in query for keyword in [
            "包保排查任务总数", "包保排查任务总完成率",
            "主要负责人任务数", "主要负责人完成率",
            "技术负责人任务数", "技术负责人完成率",
            "操作负责人任务数", "操作负责人完成率",
            "完成情况", "完成率"
        ]):
            return ["v_ai_ipark_hm_defend_statistics_company"]

        elif any(keyword in query for keyword in [
            "预警描述", "预警等级", "预警起始时间", "预警销警时间", "预警状态"
        ]):
            return ["v_ai_ipark_hm_warning_event"]

        else:
            return [origin_table]

        # 作业数
    def process_zuoyeshuo(self, query, origintable):
            # v_ai_ipark_hm_company_promise_today的关键词
            KeyWords = ["特级", "一级", "二级", "倒罐", "清罐", "切水", "承包商", "检维修", "检修", "维修", "开车装置",
                        "停车装置", "试生产", "承诺作业总数"]
            table = []
            if any(keyword in query for keyword in KeyWords):
                table.append("v_ai_ipark_hm_company_promise_today")
            else:
                table.append("v_ai_ipark_job_special_job_key_today")
            if table == []:
                return [origintable]
            return table

        # 报警
    def process_baojing(self, query, origintable):
        return ["v_ai_ipark_alarm_ai_ledger","v_ai_ipark_alarm_job","v_ai_ipark_alarm_monitor"]

        # 风险
    def process_fengxian(self, query, origintable):
            table = []
            # v_ai_ipark_ra_daily_risk_summary_company关键词
            KeyWords_1 = ["最高风险等级", "最低风险值"]
            # v_ai_ipark_ra_latest_risk_snapshot关键词
            KeyWords_2 = ["当前", "园区", "风险指数", "分险等级"]
            # v_ai_ipark_hm_company_promise关键词
            KeyWords_3 = ["承诺"]
            if any(keyword in query for keyword in KeyWords_1):
                table.append("v_ai_ipark_ra_daily_risk_summary_company")
            if any(keyword in query for keyword in KeyWords_2):
                table.append("v_ai_ipark_ra_latest_risk_snapshot")
            if any(keyword in query for keyword in KeyWords_3):
                table.append("v_ai_ipark_hm_company_promise")
            if table == []:
                return [origintable]
            return table

    # 风险分析
    def process_fengxiangAnalysis(self, query, origin_table):
        if any(keyword in query for keyword in
               ["分线分享对象总数", "风险分析单元总数", "安全分险事件总数", "管控措施总数"]):
            return ["v_ai_ipark_ipark_dp_risk_obj"]
        elif any(keyword in query for keyword in
                 ["运行效果", "隐患排查完成率", "隐患整改完成率", "企业状态", "风险分析完成率", "风险分析对象类型",
                  "得分"]):
            return ["v_ai_ipark_dp_evaluation"]
        else:
            return [origin_table]
    
    def process_chemical(self,query,origin_table):
        return ["v_ai_ipark_hm_chemical_detail","v_ai_ipark_hm_chemical"]
    def process_hazard_info(self,query,origin_table):
        return ["v_ai_ipark_hm_hazard_info_detail","v_ai_ipark_hm_hazard_info"]
    def process_craft(self,query,origin_table):
        return ["v_ai_ipark_hm_craft","v_ai_ipark_hm_craft_detail"]
    
    def process_Includefengxiang(self,query):
        if "风险" in query:
            return ["v_ai_ipark_ra_daily_risk_summary_company","v_ai_ipark_ra_park_daily_risk_summary_park"]
        else:
            return []
    # 这里处理所有的表
    def process_all(self, query, tables):
        res_table = []
        for table in tables:
            if table in self.avaliable_function:
                now_table = self.avaliable_function[table](query, table)
                res_table.extend(now_table)
            else:
                res_table.append(table)
        fengxiangTable=self.process_Includefengxiang(query)
        FinalTable = list(set(tables + res_table+ fengxiangTable))
        return FinalTable

if __name__ == "__main__":
    psutils=ProcessUtils()
    res=psutils.process_all("隐患排查完成率和危险源",["v_ai_ipark_ipark_dp_risk_obj","v_ai_ipark_hm_hazard_info","v_ai_ipark_alarm_monitor"])
    print(res)