# Knowledge Plugin - 知识库管理插件

基于向量数据库的知识管理系统。

## 功能特性

### 📚 核心功能

- **知识添加** (`knowledge_add`) - 添加知识到向量数据库
- **知识搜索** (`knowledge_search`) - 语义搜索知识

### 🔍 技术实现

- **当前版本 (v0.1.0)**: 接口实现，参数验证
- **计划版本 (v0.5.0)**: ChromaDB 向量存储，语义搜索

## 安装

### 前置要求

- Python >= 3.10
- uv (推荐) 或 pip
- Claude Code >= 1.0.0

### 安装步骤

```bash
# 进入插件目录
cd plugins/knowledge

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
      "path": "/path/to/ccplugin/plugins/knowledge"
    }
  ]
}
```

## 使用

### knowledge_add - 添加知识

```python
# 基本使用
knowledge_add(
    content="Python 最佳实践文档",
    source="官方文档",
    metadata={"category": "python", "author": "PSF"}
)

# 最小参数
knowledge_add(content="知识内容")
```

**参数**:
- `content` (必需): 知识内容
- `source` (可选): 知识来源，默认 `""`
- `metadata` (可选): 元数据字典，默认 `{}`

### knowledge_search - 搜索知识

```python
# 基本使用
knowledge_search(
    query="Python 异步编程",
    limit=5
)

# 最小参数
knowledge_search(query="搜索关键词")
```

**参数**:
- `query` (必需): 搜索查询
- `limit` (可选): 返回数量限制，默认 `10`

## 开发

### 项目结构

```
plugins/knowledge/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── src/knowledge/
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
uv run pytest --cov=src/knowledge --cov-report=html
```

### 调试 MCP Server

```bash
# 直接运行
uv run python -m knowledge.server

# 调试模式
export LOG_LEVEL=DEBUG
uv run python -m knowledge.server
```

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | MCP SDK |
| pydantic | ≥2.0 | 数据验证 |
| chromadb | ≥0.4.0 | 向量数据库 (v0.5.0) |

## 路线图

### v0.1.0 (当前)
- [x] MCP 工具接口实现
- [x] 参数验证
- [x] 单元测试
- [x] 文档

### v0.5.0 (计划)
- [ ] ChromaDB 向量存储
- [ ] 语义相似度搜索优化
- [ ] 多源知识同步
- [ ] 知识图谱整合
- [ ] 向量索引优化

## 测试

### 运行测试

```bash
# 所有测试
uv run pytest

# 特定测试
uv run pytest tests/test_server.py::test_knowledge_add -v

# 覆盖率报告
uv run pytest --cov=src/knowledge --cov-report=term-missing
```

### 测试覆盖

- ✅ 工具列表
- ✅ knowledge_add (完整参数)
- ✅ knowledge_add (最小参数)
- ✅ knowledge_search (完整参数)
- ✅ knowledge_search (最小参数)

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**版本**: 0.1.0
**最后更新**: 2025-01-15
