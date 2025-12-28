# Task Plugin - 任务管理插件

开发任务的创建和管理系统。

## 功能特性

### ✅ 核心功能

- **任务创建** (`task_create`) - 创建结构化的开发任务
- **任务列表** (`task_list`) - 列出和过滤任务

### 📊 技术实现

- **当前版本 (v0.1.0)**: 接口实现，参数验证
- **计划版本 (v0.4.0)**: SQLAlchemy 存储，依赖管理，状态流转

## 安装

### 前置要求

- Python >= 3.10
- uv (推荐) 或 pip
- Claude Code >= 1.0.0

### 安装步骤

```bash
# 进入插件目录
cd plugins/task

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS

# 安装依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest -v
```

### 配置 Claude Code

在 Claude Code 配置中添加：

```json
{
  "plugins": [
    {
      "path": "/path/to/ccplugin/plugins/task"
    }
  ]
}
```

## 使用

### task_create - 创建任务

```python
# 基本使用
task_create(
    title="实现新功能",
    description="添加用户认证功能",
    priority=1,
    tags=["feature", "auth"]
)

# 最小参数
task_create(title="修复 Bug")
```

**参数**:
- `title` (必需): 任务标题
- `description` (可选): 任务描述，默认 `""`
- `priority` (可选): 优先级 (0-5)，默认 `2`
- `tags` (可选): 标签列表，默认 `[]`

### task_list - 列出任务

```python
# 基本使用
task_list(
    status="in_progress",
    tags=["feature"]
)

# 列出所有任务
task_list()
```

**参数**:
- `status` (可选): 任务状态过滤 (open/in_progress/done/blocked)
- `tags` (可选): 标签过滤，默认 `[]`

## 开发

### 项目结构

```
plugins/task/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── src/task/
│   ├── __init__.py
│   ├── __main__.py          # 入口点
│   ├── server.py            # MCP Server 实现
│   └── types.py             # 类型定义
├── tests/
│   ├── __init__.py
│   └── test_server.py       # 单元测试
├── pyproject.toml           # Python 配置
└── README.md                # 本文件
```

### 开发工作流

```bash
# 代码格式化
uv run black src/

# 代码检查
uv run ruff check src/ --fix

# 类型检查
uv run mypy src/

# 运行测试
uv run pytest -v

# 测试覆盖率
uv run pytest --cov=src/task --cov-report=html
```

### 调试 MCP Server

```bash
# 直接运行
uv run python -m task.server

# 调试模式
export LOG_LEVEL=DEBUG
uv run python -m task.server
```

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | MCP SDK |
| pydantic | ≥2.0 | 数据验证 |
| sqlalchemy | ≥2.0 | 关系数据库 (v0.4.0) |

## 路线图

### v0.1.0 (当前)
- [x] MCP 工具接口实现
- [x] 参数验证
- [x] 单元测试
- [x] 文档

### v0.4.0 (计划)
- [ ] SQLAlchemy 任务存储
- [ ] 任务依赖关系图
- [ ] 状态流转规则引擎
- [ ] 优先级调度器
- [ ] 任务统计和报表

## 测试

### 运行测试

```bash
# 所有测试
uv run pytest

# 特定测试
uv run pytest tests/test_server.py::test_task_create -v

# 覆盖率报告
uv run pytest --cov=src/task --cov-report=term-missing
```

### 测试覆盖

- ✅ 工具列表
- ✅ task_create (完整参数)
- ✅ task_create (最小参数)
- ✅ task_list (完整参数)
- ✅ task_list (最小参数)

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**版本**: 0.1.0
**最后更新**: 2025-01-15
