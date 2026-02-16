# Memory

智能记忆插件，为 Claude Code 提供持久化、智能化的记忆管理系统。

## 特性

- **URI 结构化记忆**：通过 URI 路径组织记忆，语义清晰
- **Hooks 自动化**：自动记录、预加载、归档记忆
- **SQLite 存储**：轻量级、无依赖、跨平台
- **版本控制**：修改前快照，支持回滚
- **智能推荐**：基于上下文推荐相关记忆
- **多项目支持**：项目隔离，支持共享记忆

## 安装

```
/plugin install memory
```

## 快速开始

### 1. 读取记忆

```
/memory read project://structure
/memory read workflow://commands
/memory read system://boot
```

### 2. 创建记忆

```
/memory create project:// "项目依赖: React 18, TypeScript 5" --priority 1
/memory create workflow://commands "构建: npm run build" --priority 2
```

### 3. 搜索记忆

```
/memory search "dependencies"
/memory search "review" --domain workflow
```

## URI 命名空间

| 命名空间 | 用途 |
|----------|------|
| `project://` | 项目级记忆（结构、依赖、配置） |
| `workflow://` | 工作流记忆（命令、模式、解决方案） |
| `user://` | 用户级记忆（偏好、标准、上下文） |
| `task://` | 任务级记忆（待办、进度、阻塞） |
| `system://` | 系统操作（boot、index、recent） |

## 优先级系统

| 级别 | 含义 | 自动加载 |
|------|------|----------|
| 0-2 | 核心记忆 | 始终加载 |
| 3-5 | 重要记忆 | 按需加载 |
| 6-8 | 参考记忆 | 手动加载 |
| 9-10 | 归档记忆 | 不加载 |

## 自动化 Hooks

| Hook | 操作 |
|------|------|
| SessionStart | 加载核心记忆 |
| PreToolUse | 智能预加载 |
| PostToolUse | 自动记录操作 |
| Stop | 检查未保存内容 |
| SessionEnd | 保存会话摘要 |

## 文档

- [概述](docs/概述.md)
- [架构设计](docs/架构设计.md)
- [Hooks系统设计](docs/Hooks系统设计.md)
- [记忆系统设计](docs/记忆系统设计.md)
- [数据库设计](docs/数据库设计.md)
- [MCP工具设计](docs/MCP工具设计.md)
- [CLI命令设计](docs/CLI命令设计.md)
- [高级特性设计](docs/高级特性设计.md)
- [部署指南](docs/部署指南.md)

## 许可证

Apache-2.0
