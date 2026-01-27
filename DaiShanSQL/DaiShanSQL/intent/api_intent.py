import json

class API_Embedding():
    def __init__(self, sentence_origin_path):
        self.sentenceList = self.read_jsonl_file(sentence_origin_path)
        self.sentence_map = {item["sentence"]: item for item in self.sentenceList}

    def read_jsonl_file(self,file_path: str):
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    data_list.append(data)
                except json.JSONDecodeError as e:
                    print(f"警告：第{line_num}行JSON格式错误，已跳过 - {e}")

        return data_list

    def predict_table(self, questions:list):
        top_k_results = []
        for question in questions:
            clean_question = question.strip()
            if clean_question in self.sentence_map:
                match_data = self.sentence_map[clean_question]
                # 提取需要返回的字段
                result_item = {
                    "待查询表": match_data["intent"],
                    "相关问题": match_data["sentence"],
                    "数据库sql": match_data["sql"]
                }
                top_k_results.append(result_item)
            else:
                # 无匹配时可返回空字典或提示（根据需求选择）
                top_k_results.append({"提示": f"未找到与「{clean_question}」完全匹配的内容"})
        return top_k_results


if __name__ == '__main__':
    # 全局单例（避免重复加载模型）
    api_embed = API_Embedding(sentence_origin_path="./岱山生成问题与SQL.jsonl")
    que=["哪家企业的AI报警次数最多？","目前还有哪些AI报警是待处理状态？"]
    print(api_embed.predict_table(que))
