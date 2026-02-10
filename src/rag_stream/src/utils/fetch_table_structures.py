"""
表结构查询工具
用于查询 source_type_mapping.json 中所有表的结构信息
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# 添加 DaiShanSQL 目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
daishan_sql_path = project_root / "DaiShanSQL"
sys.path.insert(0, str(daishan_sql_path))

from DaiShanSQL import Server


def query_table_structure(server: Server, table_name: str) -> List[Dict[str, Any]]:
    """
    查询指定表的结构信息

    Args:
        server: DaiShanSQL Server 实例
        table_name: 表名

    Returns:
        List[Dict]: 包含字段信息的列表，每个字段包含 name, type, length, nullable
    """
    # 达梦数据库使用 USER_TAB_COLUMNS 系统视图查询表结构
    sql = f"""
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = '{table_name}'
    ORDER BY COLUMN_ID
    """

    print(f"查询表 {table_name} 的结构...")

    try:
        result = server.QueryBySQL(sql)

        columns = []
        if isinstance(result, dict) and result.get('data'):
            for row in result['data']:
                if isinstance(row, dict):
                    columns.append({
                        'name': row.get('COLUMN_NAME', ''),
                        'type': row.get('DATA_TYPE', ''),
                        'length': row.get('DATA_LENGTH', ''),
                        'nullable': row.get('NULLABLE', '')
                    })
                elif isinstance(row, list) and len(row) >= 4:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'length': row[2],
                        'nullable': row[3]
                    })

        print(f"  ✓ 成功获取 {len(columns)} 个字段")
        return columns

    except Exception as e:
        print(f"  ✗ 查询失败: {e}")
        return []


def fetch_all_table_structures(
    mapping_file: Path,
    output_file: Path
) -> Dict[str, List[Dict[str, Any]]]:
    """
    查询所有表的结构并保存到JSON文件

    Args:
        mapping_file: source_type_mapping.json 文件路径
        output_file: 输出的JSON文件路径

    Returns:
        Dict: 表名到字段列表的映射
    """
    # 读取映射配置
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping_config = json.load(f)

    # 创建 Server 实例
    server = Server()

    # 存储所有表的结构
    all_structures = {}

    print("=" * 80)
    print("开始查询表结构")
    print("=" * 80)

    # 遍历所有表
    for source_type, config in mapping_config.items():
        table_name = config['table_name']
        print(f"\n处理资源类型: {source_type}")
        print(f"  表名: {table_name}")

        # 查询表结构
        columns = query_table_structure(server, table_name)

        # 保存结果
        all_structures[table_name] = {
            'source_type': source_type,
            'columns': columns
        }

    # 保存到JSON文件
    print("\n" + "=" * 80)
    print(f"保存结果到: {output_file}")
    print("=" * 80)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_structures, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 成功保存 {len(all_structures)} 个表的结构信息")

    return all_structures


def main():
    """主函数"""
    # 文件路径
    current_dir = Path(__file__).parent
    mapping_file = current_dir / "source_type_mapping.json"
    output_file = current_dir / "table_structures.json"

    # 执行查询
    try:
        structures = fetch_all_table_structures(mapping_file, output_file)

        # 打印摘要
        print("\n" + "=" * 80)
        print("查询结果摘要")
        print("=" * 80)

        for table_name, info in structures.items():
            column_count = len(info['columns'])
            print(f"\n{table_name}:")
            print(f"  资源类型: {info['source_type']}")
            print(f"  字段数量: {column_count}")

            if column_count > 0:
                print(f"  字段列表:")
                for col in info['columns'][:5]:  # 只显示前5个字段
                    nullable_str = "可空" if col['nullable'] == 'Y' else "非空"
                    print(f"    - {col['name']:<30} {col['type']:<15} {nullable_str}")

                if column_count > 5:
                    print(f"    ... 还有 {column_count - 5} 个字段")

        print("\n" + "=" * 80)
        print("执行完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
