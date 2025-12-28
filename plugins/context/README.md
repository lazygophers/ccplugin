# Context Plugin - 上下文管理插件

会话上下文的持久化和恢复系统。

## 功能特性

- **上下文保存** (`context_save`) - 保存会话上下文到数据库
- **上下文检索** (`context_retrieve`) - 检索历史会话上下文

## 安装

```bash
cd plugins/context
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pytest -v
```

## 使用

### context_save

```python
context_save(
    session_id="session-123",
    content="用户的问题描述",
    role="user"
)
```

### context_retrieve

```python
context_retrieve(
    session_id="session-123",
    limit=20
)
```

## 技术栈

- MCP SDK >= 1.1.0
- Pydantic >= 2.0
- SQLAlchemy >= 2.0 (v0.3.0)

## 路线图

- [x] v0.1.0: 接口实现
- [ ] v0.3.0: SQLAlchemy 存储、上下文压缩、智能摘要

## 许可证

MIT License

---

**版本**: 0.1.0
