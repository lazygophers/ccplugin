# 测试套件

完整的单元测试和集成测试套件，确保代码质量。

## 测试结构

```
tests/
├── __init__.py           # 测试包初始化
├── conftest.py           # pytest fixtures 和配置
├── test_repository.py    # Repository 层测试（25+ 用例）
├── test_mappers.py       # Mapper 层测试（20+ 用例）
├── test_database.py      # Database 层测试（10+ 用例）
└── test_workspace.py     # Workspace 层测试（15+ 用例）
```

## 测试覆盖范围

### Repository 层（test_repository.py）

**TestTaskRepository** (15 个测试):
- ✅ 创建任务
- ✅ 创建重复 ID 任务（错误处理）
- ✅ 根据 ID 获取任务
- ✅ 获取不存在的任务
- ✅ 列出所有任务
- ✅ 带过滤条件列出任务
- ✅ 限制返回数量
- ✅ 更新任务
- ✅ 更新不存在的任务（错误处理）
- ✅ 删除任务
- ✅ 删除不存在的任务（错误处理）
- ✅ 统计任务数量
- ✅ 带过滤的统计

**TestDependencyRepository** (7 个测试):
- ✅ 创建依赖
- ✅ 创建重复依赖（错误处理）
- ✅ 获取任务的依赖列表
- ✅ 获取依赖某任务的任务列表
- ✅ 删除依赖
- ✅ 删除两任务间的依赖

**TestQueryBuilder** (3 个测试):
- ✅ 按字段过滤
- ✅ 排序
- ✅ 分页（limit/offset）

**TestTransactionManager** (3 个测试):
- ✅ 自动提交
- ✅ 手动提交
- ✅ 异常时自动回滚

### Mapper 层（test_mappers.py）

**TestTaskMapping** (6 个测试):
- ✅ TaskModel → Task 转换
- ✅ 带标签的任务转换
- ✅ Task → TaskModel 数据字典转换
- ✅ TaskModel → BriefTask 转换
- ✅ 批量 TaskModel → Task 转换
- ✅ 批量 TaskModel → BriefTask 转换

**TestDependencyMapping** (3 个测试):
- ✅ DependencyModel → Dependency 转换
- ✅ Dependency → DependencyModel 数据字典转换
- ✅ 批量 DependencyModel → Dependency 转换

**TestTaskWithDependencies** (1 个测试):
- ✅ 带依赖信息的任务转换

**TestEnumConversion** (3 个测试):
- ✅ TaskType 枚举转换
- ✅ TaskStatus 枚举转换
- ✅ Priority 枚举转换

**TestEdgeCases** (3 个测试):
- ✅ 空标签列表转换
- ✅ NULL 字段转换
- ✅ 元数据字段转换

### Database 层（test_database.py）

**TestDatabaseManager** (6 个测试):
- ✅ 数据库初始化
- ✅ 健康检查
- ✅ 获取数据库会话
- ✅ 上下文管理器
- ✅ 默认 URL
- ✅ 多个会话

**TestSQLiteOptimization** (2 个测试):
- ✅ WAL 模式启用
- ✅ 外键约束启用

### Workspace 层（test_workspace.py）

**TestWorkspaceManager** (9 个测试):
- ✅ 工作空间初始化
- ✅ 工作空间 ID 生成
- ✅ 不同路径生成不同 ID
- ✅ 获取数据库管理器
- ✅ 获取工作空间信息
- ✅ 删除工作空间
- ✅ 删除需要确认
- ✅ 上下文管理器
- ✅ 自动初始化/禁用自动初始化

**TestWorkspaceSecurity** (3 个测试):
- ✅ 拒绝包含 .. 的路径
- ✅ 拒绝敏感目录
- ✅ 接受安全路径

**TestWorkspaceHelpers** (2 个测试):
- ✅ get_workspace 函数
- ✅ list_workspaces 函数

**TestWorkspaceIsolation** (2 个测试):
- ✅ 独立的数据库
- ✅ 数据隔离

## 运行测试

### 安装依赖

```bash
uv pip install -e ".[dev]"
```

### 运行所有测试

```bash
uv run pytest
```

### 运行特定模块

```bash
# Repository 层测试
uv run pytest tests/test_repository.py

# Mapper 层测试
uv run pytest tests/test_mappers.py

# Database 层测试
uv run pytest tests/test_database.py

# Workspace 层测试
uv run pytest tests/test_workspace.py
```

### 详细输出

```bash
uv run pytest -v
```

### 生成覆盖率报告

```bash
# 终端输出
uv run pytest --cov=src/task --cov-report=term-missing

# HTML 报告
uv run pytest --cov=src/task --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html
```

### 覆盖率要求

```bash
# 要求覆盖率 ≥ 95%
uv run pytest --cov=src/task --cov-fail-under=95
```

## 测试 Fixtures

**conftest.py** 提供以下 fixtures:

- `temp_dir`: 临时目录
- `in_memory_db`: 内存数据库会话
- `db_manager`: 数据库管理器
- `session`: 数据库会话
- `task_repo`: 任务仓库
- `dep_repo`: 依赖仓库
- `workspace`: 工作空间
- `sample_task_data`: 示例任务数据
- `sample_dependency_data`: 示例依赖数据

## 测试统计

- **总测试文件**: 5 个
- **总测试用例**: 70+ 个
- **目标覆盖率**: ≥ 95%
- **测试隔离**: 每个测试使用独立的临时数据库
- **并发支持**: 所有测试可并发运行

## CI/CD 集成

测试可集成到 CI/CD 流程：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      - name: Run tests
        run: uv run pytest --cov=src/task --cov-fail-under=95
```

## 调试测试

### 运行单个测试

```bash
uv run pytest tests/test_repository.py::TestTaskRepository::test_create_task -v
```

### 进入调试模式

```bash
uv run pytest --pdb
```

### 显示打印输出

```bash
uv run pytest -s
```

## 最佳实践

1. **测试隔离**: 每个测试使用独立的数据库和临时目录
2. **清理资源**: 使用 fixtures 和 context managers 自动清理
3. **边界测试**: 覆盖正常、异常和边界情况
4. **错误处理**: 验证错误类型和错误消息
5. **数据验证**: 验证数据完整性和类型安全

## 问题排查

### 测试失败

检查：
1. 依赖是否已安装
2. Python 版本 ≥ 3.10
3. 数据库文件权限
4. 临时目录可用

### 覆盖率不足

运行：
```bash
uv run pytest --cov=src/task --cov-report=term-missing
```

查看未覆盖的代码行。

---

**版本**: 0.2.0
**最后更新**: 2025-12-28
**维护者**: luoxin
