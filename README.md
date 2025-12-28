# Claude Code Market Plugin

Claude Code 插件市场 - 提供记忆、上下文、任务和知识库管理功能的综合插件。

## 功能特性

### 🧠 记忆管理
- 基于知识图谱的记忆存储
- 标签化记忆检索
- 元数据关联

### 📝 上下文管理
- 会话上下文持久化
- 多角色上下文追踪
- 历史上下文检索

### ✅ 任务管理
- 结构化任务创建
- 优先级和状态管理
- 标签过滤

### 📚 知识库管理
- 向量数据库存储
- 语义搜索
- 多源知识整合

## 安装

### 前置要求

- Python >= 3.9
- uv (推荐) 或 pip

### 使用 Claude Code 安装

```bash
# 克隆仓库
git clone https://github.com/lyxamour/ccplugin
cd ccplugin

# 使用 uv 初始化环境
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 配置插件

在 Claude Code 的配置文件中添加：

```json
{
  "plugins": [
    {
      "path": "/path/to/ccplugin"
    }
  ]
}
```

## 使用

### MCP Server 工具

插件提供以下 MCP 工具：

#### 记忆管理

```python
# 存储记忆
memory_store(
    content="重要的项目信息",
    tags=["project", "important"],
    metadata={"author": "user"}
)

# 搜索记忆
memory_search(
    query="项目信息",
    tags=["project"],
    limit=10
)
```

#### 上下文管理

```python
# 保存上下文
context_save(
    session_id="session-123",
    content="用户的问题描述",
    role="user"
)

# 检索上下文
context_retrieve(
    session_id="session-123",
    limit=20
)
```

#### 任务管理

```python
# 创建任务
task_create(
    title="实现新功能",
    description="添加用户认证功能",
    priority=1,
    tags=["feature", "auth"]
)

# 列出任务
task_list(
    status="in_progress",
    tags=["feature"]
)
```

#### 知识库管理

```python
# 添加知识
knowledge_add(
    content="Python 最佳实践文档",
    source="官方文档",
    metadata={"category": "python"}
)

# 搜索知识
knowledge_search(
    query="Python 异步编程",
    limit=5
)
```

## 开发

### 项目结构

```
ccplugin/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── src/market/
│   ├── __init__.py
│   ├── __main__.py          # 服务器入口
│   ├── server.py            # MCP Server 实现
│   ├── config.py            # 配置管理
│   ├── types.py             # 类型定义
│   ├── tools/               # 工具实现
│   ├── resources/           # 资源处理
│   └── utils/               # 工具函数
├── tests/                   # 测试
├── pyproject.toml           # Python 项目配置
└── README.md
```

### 开发环境设置

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
ruff check src/ --fix

# 类型检查
mypy src/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=src/market --cov-report=html

# 运行特定测试
pytest tests/test_server.py -v
```

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | INFO |
| `DEBUG` | 调试模式 | false |
| `MAX_TIMEOUT` | 最大超时时间 | 30.0 |
| `MARKET_STORAGE_PATH` | 存储路径 | ./.market_data |
| `ENABLE_MEMORY` | 启用记忆功能 | true |
| `ENABLE_CONTEXT` | 启用上下文功能 | true |
| `ENABLE_TASK` | 启用任务功能 | true |
| `ENABLE_KNOWLEDGE` | 启用知识库功能 | true |

## 技术栈

- **MCP**: Model Context Protocol SDK
- **Pydantic**: 数据验证
- **ChromaDB**: 向量数据库
- **NetworkX**: 知识图谱
- **SQLAlchemy**: 关系数据库 ORM
- **httpx**: HTTP 客户端

## 路线图

- [ ] 记忆管理完整实现
  - [ ] 知识图谱存储
  - [ ] 关系推理
  - [ ] 记忆合并
- [ ] 上下文管理完整实现
  - [ ] 会话持久化
  - [ ] 上下文压缩
  - [ ] 智能摘要
- [ ] 任务管理完整实现
  - [ ] 依赖管理
  - [ ] 状态流转
  - [ ] 优先级调度
- [ ] 知识库管理完整实现
  - [ ] 向量检索优化
  - [ ] 多模态支持
  - [ ] 知识图谱整合

## 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

如有问题或建议，请在 GitHub 上创建 issue。

## 作者

luoxin
