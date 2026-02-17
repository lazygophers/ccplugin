# CLI 命令设计

## 一、命令结构

```
uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py <command> [options]
```

---

## 二、命令列表

### 2.1 hooks - Hook 模式入口

```bash
uv run ./scripts/main.py hooks [--debug]
```

从 stdin 读取 JSON 格式的 Hook 数据并处理。

**选项**:
- `--debug` - 启用 DEBUG 模式

**用途**: 作为 Claude Code hooks 的入口点，处理会话生命周期事件。

---

### 2.2 web - Web 管理界面

```bash
uv run ./scripts/main.py web [options] [--debug]
```

启动 Web 管理界面，提供可视化的记忆管理功能。

**选项**:
- `-p, --port <port>` - 端口号（默认自动查找可用端口）
- `--no-browser` - 不自动打开浏览器
- `-r, --reload` - 启用热重载（开发模式）
- `--debug` - 启用 DEBUG 模式

**示例**:
```bash
uv run ./scripts/main.py web
uv run ./scripts/main.py web -p 8080 --no-browser
uv run ./scripts/main.py web -r --debug
```

**功能**:
- 记忆树形视图
- 版本历史查看
- 版本对比与回滚
- 记忆清理

---

### 2.3 mcp - MCP Server

```bash
uv run ./scripts/main.py mcp [--debug]
```

启动 MCP Server，让 AI Agent 能直接通过 MCP 协议操作记忆系统。

**选项**:
- `--debug` - 启用 DEBUG 模式

**通信方式**: stdio（标准输入/输出）

**可用工具**:

| 工具 | 描述 |
|------|------|
| `read_memory` | 读取记忆 |
| `create_memory` | 创建记忆 |
| `update_memory` | 更新记忆 |
| `delete_memory` | 删除记忆 |
| `search_memory` | 搜索记忆 |
| `preload_memory` | 预加载记忆 |
| `save_session` | 保存会话 |
| `list_memories` | 列出记忆 |
| `get_memory_stats` | 获取统计 |
| `export_memories` | 导出记忆 |
| `import_memories` | 导入记忆 |
| `add_alias` | 添加别名 |
| `get_memory_versions` | 获取版本历史 |
| `rollback_memory` | 回滚记忆 |
| `diff_versions` | 对比版本 |
| `list_rollbacks` | 列出可回滚版本 |

---

## 三、通用选项

### 3.1 调试选项

所有命令都支持 `--debug` 选项：

```bash
uv run ./scripts/main.py --debug <command>
```

启用 DEBUG 模式后，会输出详细的调试日志。

---

## 四、使用场景

### 4.1 作为 Claude Code Hook

在 Claude Code 配置中注册 hooks 入口，自动处理会话事件。

### 4.2 Web 管理界面

通过 Web 界面进行可视化的记忆管理，适合人工操作。

### 4.3 MCP 协议

作为 MCP Server 运行，让 AI Agent 通过标准协议操作记忆系统。
