"""测试 DaiShanSQL QueryBySQL 方法的测试文件"""
import sys
import json
from pathlib import Path

# 添加 DaiShanSQL 目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
daishan_sql_path = project_root / "DaiShanSQL"
sys.path.insert(0, str(daishan_sql_path))

# 导入 Server 类
from DaiShanSQL import Server


def print_result(result, title="查询结果"):
    """格式化打印查询结果"""
    print(f"\n{title}:")
    print("=" * 80)

    if isinstance(result, dict):
        # 如果是字典，格式化输出
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 检查是否有错误
        if result.get('code') != 200 and result.get('code') is not None:
            print("\n⚠️  查询返回错误:")
            print(f"   错误码: {result.get('code')}")
            print(f"   错误信息: {result.get('msg')}")
        elif result.get('data') is not None:
            print("\n✓ 查询成功")
            print(f"   返回数据: {result.get('data')}")
    else:
        print(result)

    print("=" * 80)


def test_query_accident_event_by_id():
    """测试查询 IPARK_AE_ACCIDENT_EVENT 表中 ID=5896694001464688 的记录"""

    # 创建 Server 实例
    server = Server()

    # 构造 SQL 查询语句
    sql = "SELECT * FROM IPARK_AE_ACCIDENT_EVENT WHERE ID=5896694001464688"

    print(f"\n执行 SQL: {sql}")

    # 执行查询
    result = server.QueryBySQL(sql)

    # 打印结果
    print_result(result, "查询结果（ID不加引号）")

    # 断言结果不为空
    assert result is not None, "查询结果不应为空"

    return result


def test_query_accident_event_by_id_with_quotes():
    """测试查询 IPARK_AE_ACCIDENT_EVENT 表中 ID='5896694001464688' 的记录（ID作为字符串）"""

    # 创建 Server 实例
    server = Server()

    # 构造 SQL 查询语句（ID加引号）
    sql = "SELECT * FROM IPARK_AE_ACCIDENT_EVENT WHERE ID='5896694001464688'"

    print(f"\n执行 SQL: {sql}")

    # 执行查询
    result = server.QueryBySQL(sql)

    # 打印结果
    print_result(result, "查询结果（ID作为字符串）")

    # 断言结果不为空
    assert result is not None, "查询结果不应为空"

    return result


def test_simple_query():
    """测试简单查询（查询表的前10条记录）"""

    # 创建 Server 实例
    server = Server()

    # 构造简单的 SQL 查询语句
    sql = "SELECT * FROM VIPARK_AE_ACCIDENT_EVENT LIMIT 10"

    print(f"\n执行 SQL: {sql}")

    # 执行查询
    result = server.QueryBySQL(sql)

    # 打印结果
    print_result(result, "查询结果（前10条记录）")

    return result


def test_query_table_columns():
    """测试查询 IPARK_AE_ACCIDENT_EVENT 表的所有字段名（达梦数据库）"""

    # 创建 Server 实例
    server = Server()

    # 达梦数据库使用 USER_TAB_COLUMNS 系统视图查询表结构
    sql_dm = """
    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'IPARK_AE_ACCIDENT_EVENT'
    ORDER BY COLUMN_ID
    """
    print(f"\n执行 SQL (达梦数据库 USER_TAB_COLUMNS): {sql_dm.strip()}")
    result_dm = server.QueryBySQL(sql_dm)
    print_result(result_dm, "字段详细信息（USER_TAB_COLUMNS）")

    # 提取并打印所有字段名
    print("\n" + "=" * 80)
    print("字段名列表:")
    print("=" * 80)

    if isinstance(result_dm, dict) and result_dm.get('data'):
        columns = []
        for row in result_dm['data']:
            if isinstance(row, dict) and 'COLUMN_NAME' in row:
                columns.append({
                    'name': row['COLUMN_NAME'],
                    'type': row.get('DATA_TYPE', ''),
                    'length': row.get('DATA_LENGTH', ''),
                    'nullable': row.get('NULLABLE', '')
                })
            elif isinstance(row, list) and len(row) > 0:
                columns.append({
                    'name': row[0],
                    'type': row[1] if len(row) > 1 else '',
                    'length': row[2] if len(row) > 2 else '',
                    'nullable': row[3] if len(row) > 3 else ''
                })

        if columns:
            print(f"共 {len(columns)} 个字段:")
            for i, col in enumerate(columns, 1):
                nullable_str = "可空" if col['nullable'] == 'Y' else "非空"
                print(f"  {i}. {col['name']:<30} {col['type']:<15} 长度:{col['length']:<10} {nullable_str}")
        else:
            print("未能提取字段名")
    else:
        print("查询结果格式不符合预期")

    print("=" * 80)

    return {
        'dm_columns': result_dm
    }


if __name__ == "__main__":
    print("=" * 80)
    print("开始测试 QueryBySQL 方法")
    print("=" * 80)

    print("\n测试: 查询 IPARK_AE_ACCIDENT_EVENT 表的所有字段名")
    print("-" * 80)
    try:
        result = test_query_table_columns()
        print("\n✓ 测试执行完成")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("测试执行完成")
    print("=" * 80)