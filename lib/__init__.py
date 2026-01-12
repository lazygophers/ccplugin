"""
CCPlugin Common Library
插件市场共享库

这个库包含所有插件可复用的通用组件，包括：
- 配置管理 (config)
- 语言常量 (constants)
- 嵌入和向量存储 (embedding)
- 代码解析器 (parsers)
- 搜索引擎 (search)
- 数据库操作 (database)
- 通用工具 (utils)

使用方式：
    # 在插件脚本中添加项目根路径
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

    # 然后导入公共库
    from lib.config import get_data_path, load_config
    from lib.constants import SUPPORTED_LANGUAGES
"""

__version__ = "1.0.0"
__all__ = [
    "config",
    "constants",
    "utils",
    # 其他模块将在后续添加
]
