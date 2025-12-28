# Memory Plugin - 记忆管理插件

基于知识图谱的记忆存储和检索系统。

## 功能特性

### 🧠 核心功能

- **记忆存储** (`memory_store`) - 将信息存储到知识图谱
- **记忆搜索** (`memory_search`) - 基于关键词和标签搜索记忆

### 📊 技术实现

- **当前版本 (v0.1.0)**: 接口实现，参数验证
- **计划版本 (v0.2.0)**: NetworkX 知识图谱存储，关系推理

## 安装

### 前置要求

- Python >= 3.10
- uv (推荐) 或 pip
- Claude Code >= 1.0.0

### 安装步骤

```bash
# 进入插件目录
cd plugins/memory

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
      "path": "/path/to/ccplugin/plugins/memory"
    }
  ]
}
```

## 使用

### memory_store - 存储记忆

```python
# 基本使用
memory_store(
    content="重要的项目信息",
    tags=["project", "important"],
    metadata={"author": "user", "date": "2025-01-15"}
)

# 最小参数
memory_store(content="简单记忆")
```

**参数**:
- `content` (必需): 记忆内容
- `tags` (可选): 标签列表，默认 `[]`
- `metadata` (可选): 元数据字典，默认 `{}`

### memory_search - 搜索记忆

```python
# 基本使用
memory_search(
    query="项目信息",
    tags=["project"],
    limit=10
)

# 最小参数
memory_search(query="搜索关键词")
```

**参数**:
- `query` (必需): 搜索关键词
- `tags` (可选): 标签过滤，默认 `[]`
- `limit` (可选): 返回数量限制，默认 `10`

## 开发

### 项目结构

```
plugins/memory/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── src/memory/
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
uv run pytest --cov=src/memory --cov-report=html
```

### 调试 MCP Server

```bash
# 直接运行
uv run python -m memory.server

# 调试模式
export LOG_LEVEL=DEBUG
uv run python -m memory.server
```

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | MCP SDK |
| pydantic | ≥2.0 | 数据验证 |
| networkx | ≥3.0 | 知识图谱 (v0.2.0) |

## 路线图

### v0.1.0 (当前)
- [x] MCP 工具接口实现
- [x] 参数验证
- [x] 单元测试
- [x] 文档

### v0.2.0 (计划)
- [ ] NetworkX 知识图谱存储
- [ ] 记忆关系建模 (节点 + 边)
- [ ] 标签索引和图遍历查询
- [ ] 记忆合并去重算法
- [ ] 关系推理功能

## 测试

### 运行测试

```bash
# 所有测试
uv run pytest

# 特定测试
uv run pytest tests/test_server.py::test_memory_store -v

# 覆盖率报告
uv run pytest --cov=src/memory --cov-report=term-missing
```

### 测试覆盖

- ✅ 工具列表
- ✅ memory_store (完整参数)
- ✅ memory_store (最小参数)
- ✅ memory_search (完整参数)
- ✅ memory_search (最小参数)

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**版本**: 0.1.0
**最后更新**: 2025-01-15
