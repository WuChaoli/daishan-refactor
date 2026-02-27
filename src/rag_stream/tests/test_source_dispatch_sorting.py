"""测试资源调度中的距离排序功能"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from rag_stream.models.schemas import SourceDispatchRequest, AccidentEventData
from rag_stream.models.emergency_entities import FireFightingFacility, Shelter
from rag_stream.services.source_dispath_srvice import _query_resource_by_type


@pytest.mark.asyncio
async def test_distance_sorting_for_fire_facilities():
    """测试消防设施按距离排序"""

    # 创建事故数据（上海某地）
    accident_data = AccidentEventData(
        accident_name="测试事故",
        longitude=121.4737,
        latitude=31.2304,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 模拟数据库返回的消防设施（不同距离）
    mock_db_data = [
        {
            "ID": "1",
            "NAME": "远处消防站",
            "LATITUDE_LONGITUDE": '{"type":"Point","coordinates":[116.4074,39.9042]}'  # 北京
        },
        {
            "ID": "2",
            "NAME": "近处消防站",
            "LATITUDE_LONGITUDE": '{"type":"Point","coordinates":[121.5,31.25]}'  # 上海附近
        },
        {
            "ID": "3",
            "NAME": "中等距离消防站",
            "LATITUDE_LONGITUDE": '{"type":"Point","coordinates":[120.1551,30.2741]}'  # 杭州
        },
    ]

    # 创建请求
    request = SourceDispatchRequest(
        accidentId="test_001",
        sourceType="fireFightingFacilities",
        voiceText="需要消防设施"
    )

    # Mock 日志管理器
    mock_log_manager = Mock()
    mock_logger = Mock()
    mock_log_manager.get_function_logger.return_value = mock_logger

    # Mock SQL 查询结果
    with patch('rag_stream.services.source_dispath_srvice.execute_sql_query', new_callable=AsyncMock) as mock_sql:
        mock_sql.return_value = {"data": mock_db_data}

        # Mock Dify client
        with patch('rag_stream.services.source_dispath_srvice.get_client') as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.answer = '[{"id":"1"},{"id":"2"},{"id":"3"}]'
            mock_client.create_chat_message.return_value = mock_response
            mock_get_client.return_value = mock_client

            # 执行查询
            result = await _query_resource_by_type(
                request=request,
                log_manager=mock_log_manager,
                function_name="test_function",
                accident_data=accident_data,
                number=5
            )

    # 验证结果
    assert len(result) == 3

    # 验证排序：近处 < 中等 < 远处
    assert result[0].name == "近处消防站"
    assert result[1].name == "中等距离消防站"
    assert result[2].name == "远处消防站"

    print("✓ 消防设施按距离排序测试通过")


@pytest.mark.asyncio
async def test_no_sorting_for_medical_institution():
    """测试医疗机构不进行距离排序"""

    # 创建事故数据
    accident_data = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 模拟数据库返回的医疗机构（故意按远近顺序）
    mock_db_data = [
        {
            "ID": "1",
            "INSTITUTION_NAME": "远处医院",
            "LOCAL_POS": '{"type":"Point","coordinates":[121.0,31.0]}'
        },
        {
            "ID": "2",
            "INSTITUTION_NAME": "近处医院",
            "LOCAL_POS": '{"type":"Point","coordinates":[120.1,30.1]}'
        },
    ]

    # 创建请求
    request = SourceDispatchRequest(
        accidentId="test_002",
        sourceType="medicalInstitution",
        voiceText="需要医疗机构"
    )

    # Mock 日志管理器
    mock_log_manager = Mock()
    mock_logger = Mock()
    mock_log_manager.get_function_logger.return_value = mock_logger

    # Mock SQL 查询结果
    with patch('rag_stream.services.source_dispath_srvice.execute_sql_query', new_callable=AsyncMock) as mock_sql:
        mock_sql.return_value = {"data": mock_db_data}

        # Mock Dify client
        with patch('rag_stream.services.source_dispath_srvice.get_client') as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.answer = '[{"id":"1"},{"id":"2"}]'
            mock_client.create_chat_message.return_value = mock_response
            mock_get_client.return_value = mock_client

            # 执行查询
            result = await _query_resource_by_type(
                request=request,
                log_manager=mock_log_manager,
                function_name="test_function",
                accident_data=accident_data,
                number=5
            )

    # 验证结果：医疗机构不排序，保持原顺序
    assert len(result) == 2
    assert result[0].institution_name == "远处医院"  # 保持原顺序
    assert result[1].institution_name == "近处医院"

    print("✓ 医疗机构不排序测试通过")


@pytest.mark.asyncio
async def test_no_sorting_for_entities_without_coords():
    """测试无坐标实体不进行排序"""

    # 创建事故数据
    accident_data = AccidentEventData(
        accident_name="测试事故",
        longitude=120.0,
        latitude=30.0,
        hazardous_chemicals="氨气",
        accident_overview="测试"
    )

    # 模拟数据库返回的应急物资（无坐标）
    mock_db_data = [
        {"id": "1", "material_name": "物资A"},
        {"id": "2", "material_name": "物资B"},
        {"id": "3", "material_name": "物资C"},
    ]

    # 创建请求
    request = SourceDispatchRequest(
        accidentId="test_003",
        sourceType="emergencySupplies",
        voiceText="需要应急物资"
    )

    # Mock 日志管理器
    mock_log_manager = Mock()
    mock_logger = Mock()
    mock_log_manager.get_function_logger.return_value = mock_logger

    # Mock SQL 查询结果
    with patch('rag_stream.services.source_dispath_srvice.execute_sql_query', new_callable=AsyncMock) as mock_sql:
        mock_sql.return_value = {"data": mock_db_data}

        # Mock Dify client
        with patch('rag_stream.services.source_dispath_srvice.get_client') as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.answer = '[{"id":"1"},{"id":"2"},{"id":"3"}]'
            mock_client.create_chat_message.return_value = mock_response
            mock_get_client.return_value = mock_client

            # 执行查询
            result = await _query_resource_by_type(
                request=request,
                log_manager=mock_log_manager,
                function_name="test_function",
                accident_data=accident_data,
                number=5
            )

    # 验证结果：无坐标实体保持原顺序
    assert len(result) == 3
    assert result[0].material_name == "物资A"
    assert result[1].material_name == "物资B"
    assert result[2].material_name == "物资C"

    print("✓ 无坐标实体不排序测试通过")


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        print("开始测试资源调度距离排序功能...\n")

        try:
            await test_distance_sorting_for_fire_facilities()
            await test_no_sorting_for_medical_institution()
            await test_no_sorting_for_entities_without_coords()
            print("\n✓ 所有测试通过！")
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            raise

    asyncio.run(run_tests())
