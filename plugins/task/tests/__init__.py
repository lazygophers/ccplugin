"""任务管理插件测试套件。

本包包含完整的单元测试和集成测试。

测试模块：
- test_repository: Repository 层测试（25+ 用例）
- test_mappers: Mapper 层测试（20+ 用例）
- test_database: Database 层测试（10+ 用例）
- test_workspace: Workspace 层测试（15+ 用例）
- conftest: 测试 fixtures 和配置

运行测试：
    # 运行所有测试
    uv run pytest

    # 运行特定模块
    uv run pytest tests/test_repository.py

    # 生成覆盖率报告
    uv run pytest --cov=src/task --cov-report=html

    # 详细输出
    uv run pytest -v

目标覆盖率：≥ 95%
"""

__version__ = "0.2.0"
