# 命令系统

Memory 插件提供的命令。

## 命令列表

| 命令 | 描述 | 用法 |
|------|------|------|
| `/memory read` | 读取记忆 | `/memory read <uri>` |
| `/memory create` | 创建记忆 | `/memory create <uri> <content>` |
| `/memory update` | 更新记忆 | `/memory update <uri> <content>` |
| `/memory delete` | 删除记忆 | `/memory delete <uri>` |
| `/memory search` | 搜索记忆 | `/memory search <query>` |
| `/memory list` | 列出记忆 | `/memory list [domain]` |

## /memory read

### 功能

读取指定 URI 的记忆内容。

### 用法

```bash
/memory read project://structure
/memory read workflow://commands
/memory read system://boot
```

## /memory create

### 功能

创建新的记忆条目。

### 用法

```bash
/memory create project:// "项目依赖: React 18, TypeScript 5" --priority 1
/memory create workflow://commands "构建: npm run build" --priority 2
```

### 选项

| 选项 | 描述 |
|------|------|
| `--priority` | 优先级 (0-10) |
| `--tags` | 标签 |

## /memory update

### 功能

更新现有记忆内容。

### 用法

```bash
/memory update project:// "更新后的内容"
```

## /memory delete

### 功能

删除指定记忆。

### 用法

```bash
/memory delete project://old-memory
```

## /memory search

### 功能

搜索记忆内容。

### 用法

```bash
/memory search "dependencies"
/memory search "review" --domain workflow
```

### 选项

| 选项 | 描述 |
|------|------|
| `--domain` | 搜索域 |
| `--limit` | 结果数量限制 |

## /memory list

### 功能

列出记忆条目。

### 用法

```bash
/memory list
/memory list project
/memory list workflow
```
