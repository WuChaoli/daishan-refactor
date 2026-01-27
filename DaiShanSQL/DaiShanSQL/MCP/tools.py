import json
import os
class Tool:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        Table_path = os.path.join(current_dir,"岱山字段结果.jsonl")
        self.tableInfoMap = self._parse_jsonl(Table_path)
    def _parse_jsonl(self, file_path):
        table_data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 去除空行和换行符
                line = line.strip()
                if not line:
                    continue
                # 解析单行JSON
                data = json.loads(line)
                table_name = data.get('table')
                field_name = data.get('field_name')
                file_note = data.get('file_Note')
                field_values = data.get('field_values', [])
                
                if not table_name or not field_name:
                    continue
                
                if table_name not in table_data:
                    table_data[table_name] = {}
                
                # 填充该表的列名信息
                table_data[table_name][field_name] = {
                    "字段名称": field_name,
                    "字段注释": file_note,
                    "字段示例": field_values
                }
        
        # 将中间存储转换为目标格式的列表（每个表对应一个字典项）
        result = []
        for table_name, columns in table_data.items():
            result.append({
                "表名": table_name,
                "列名信息": columns
            })
        
        return result


