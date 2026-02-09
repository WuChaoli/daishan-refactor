import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保可以导入 log_decorator
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
