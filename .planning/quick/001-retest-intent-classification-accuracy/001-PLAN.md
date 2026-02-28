---
type: quick
task: 001
mode: quick
description: 重新测试意图分类准确性，并输出测试正确率文档
date: 2026-02-28
---

<objective>
读取更新的 intent_test_cases.xlsx，通过 IntentService 整体服务测试意图分类准确性（Type 0/1/2/3），计算正确率，输出测试报告文档。

注意：测试的是 IntentService 服务的整体输出，不是单独测试 IntentClassifier 类。
</objective>

<tasks>

<task type="auto">
  <name>读取测试数据并初始化服务</name>
  <files>
    src/rag_stream/tests/data/intent_test_cases.xlsx
    src/rag_stream/src/services/intent_service/intent_service.py
  </files>
  <action>
1. 使用 pandas 读取 xlsx 文件，提取 query 和 expected_intent 列
2. 统计总测试用例数
3. 初始化 IntentService（需要 RagflowClient）
4. 确保配置正确加载
  </action>
  <verify>
    <automated>python -c "import pandas as pd; df = pd.read_excel('src/rag_stream/tests/data/intent_test_cases.xlsx'); print(f'Total cases: {len(df)}'); print(df.head()); print(df['expected_intent'].value_counts())"</automated>
  </verify>
  <done>成功读取测试数据并初始化服务</done>
</task>

<task type="auto">
  <name>运行意图服务测试</name>
  <files>
    src/rag_stream/src/services/intent_service/intent_service.py
    src/rag_stream/tests/data/intent_test_cases.xlsx
  </files>
  <action>
1. 创建测试脚本遍历所有测试用例
2. 对每个查询调用 IntentService.process_query() 或相关方法
3. 从返回结果中提取实际的 intent_type
4. 与 expected_intent 比对，记录正确/错误
5. 统计总体正确率和各类型正确率
6. 记录错误分类的详细情况

注意：IntentService 的输出包含 intent_type (0/1/2/3)，需要根据返回结果的 type 字段判断。
  </action>
  <verify>
    <automated>python src/rag_stream/tests/run_intent_service_test.py 2>&1 | tail -50</automated>
  </verify>
  <done>完成 IntentService 整体意图分类测试</done>
</task>

<task type="auto">
  <name>生成测试正确率报告</name>
  <files>.planning/quick/001-retest-intent-classification-accuracy/intent_classification_report.md</files>
  <action>
生成 Markdown 格式的测试报告：
1. 测试概览：总用例数、正确数、错误数、总体正确率
2. 各意图类型正确率统计（Type 0/1/2/3）
3. 错误分类详细列表：查询文本、期望意图、实际意图
4. 测试结论和建议
  </action>
  <verify>
    <automated>cat .planning/quick/001-retest-intent-classification-accuracy/intent_classification_report.md</automated>
  </verify>
  <done>测试报告文档生成完成</done>
</task>

</tasks>

<success_criteria>
- [ ] 成功读取 intent_test_cases.xlsx
- [ ] 完成 IntentService 整体服务的意图分类测试
- [ ] 生成包含正确率的详细测试报告文档
</success_criteria>
