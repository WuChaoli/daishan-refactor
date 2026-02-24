"""
pytest配置文件
为所有测试设置正确的Python路径
"""
import sys
import os
from pathlib import Path

# 获取项目根目录
# tests/ 位于 src/rag_stream/tests/
# 所以需要向上3级到项目根目录
current_dir = Path(__file__).parent
rag_stream_root = current_dir.parent
project_root = rag_stream_root.parent

# 添加src目录到sys.path
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# 添加DaiShanSQL目录到sys.path
daishan_root = src_root / "DaiShanSQL" / "DaiShanSQL"
if str(daishan_root) not in sys.path:
    sys.path.insert(0, str(daishan_root))
