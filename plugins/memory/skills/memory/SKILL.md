---
description: |
	Intelligent memory system with hooks integration. Automatically manages memories
	across sessions with smart loading, recording, and saving capabilities.

	Use this skill to:
	- Read stored memories by URI path
	- Create new memories with priority and disclosure
	- Update existing memories
	- Search memories by keyword
	- View memory index and recent changes
user-invocable: true
context: fork
auto-activate: always:true
model: sonnet
memory: project
---

# Memory Commands

## Automatic Memory Management

This plugin automatically manages memories through hooks:

| Hook | Action |
|------|--------|
| **SessionStart** | Load core memories (priority ≤ 2) |
| **PreToolUse** | Preload relevant context for file operations |
| **PostToolUse** | Record file modifications automatically |
| **Stop** | Check for pending memories, prompt to save |
| **SessionEnd** | Save session summary |

## Manual Commands

### Read Memory
Access stored memories by URI path.

```
/memory read <uri>
```

**Examples:**
```
/memory read project://structure
/memory read workflow://commands
/memory read user://preferences
/memory read system://boot
```

### Create Memory
Store new information with URI path and priority.

```
/memory create <parent_uri> <content> [--priority N] [--title TITLE] [--disclosure TEXT]
```

**Examples:**
```
/memory create project:// "Main dependencies: React 18, TypeScript 5" --priority 1
/memory create workflow://commands "Build: npm run build" --priority 2
/memory create user://preferences "Prefer functional components" --priority 1
```

### Update Memory
Modify existing memories.

```
/memory update <uri> [--old TEXT --new TEXT] [--append TEXT]
```

**Examples:**
```
/memory update project://structure --old "src/components" --new "src/ui/components"
/memory update task://todos --append "\n- Review PR #123"
```

### Search Memory
Find memories by keyword.

```
/memory search <query> [--domain DOMAIN] [--limit N]
```

**Examples:**
```
/memory search "dependencies"
/memory search "review" --domain workflow
```

### Save Session
Manually save current session as memory.

```
/memory save [--title TITLE]
```

## URI Namespace

| Domain | Purpose | Examples |
|--------|---------|----------|
| `project://` | Project-level memories | structure, dependencies, patterns |
| `workflow://` | Workflow memories | commands, snippets, review |
| `user://` | User-level memories | preferences, standards, context |
| `task://` | Task-level memories | todos, progress, blockers |
| `system://` | System operations | boot, index, recent |

## Priority System

| Priority | Meaning | Auto-load |
|----------|---------|-----------|
| 0-2 | Core memories | Always loaded |
| 3-5 | Important memories | On-demand |
| 6-8 | Reference memories | On-demand |
| 9-10 | Archive memories | Manual only |

## Disclosure Field

The `disclosure` field describes **when** to recall this memory:

```
--disclosure "When starting a new feature"
--disclosure "When reviewing code"
--disclosure "When working with TypeScript files"
```

Hooks use this field for intelligent preloading.

## 执行过程检查清单

### 读取记忆检查（/memory read）
- [ ] URI 路径格式正确（project://、workflow://、user://、system://）
- [ ] 记忆存在于存储中
- [ ] 记忆内容成功加载
- [ ] 记忆内容格式正确

### 创建记忆检查（/memory create）
- [ ] 父级 URI 路径正确
- [ ] 内容格式正确
- [ ] 优先级设置合理（priority ≤ 2 为核心记忆）
- [ ] 标题和描述清晰
- [ ] disclosure 字段设置正确（用于智能预加载）
- [ ] 记忆成功创建并保存

### 更新记忆检查（/memory update）
- [ ] 目标记忆存在
- [ ] 更新内容格式正确
- [ ] 更新字段合法（title/content/priority/disclosure）
- [ ] 记忆成功更新

### 搜索记忆检查（/memory search）
- [ ] 关键词明确
- [ ] 搜索结果相关
- [ ] 搜索结果数量合理

### Hooks 集成检查
- [ ] SessionStart hook 正确加载核心记忆（priority ≤ 2）
- [ ] PreToolUse hook 智能预加载相关上下文
- [ ] PostToolUse hook 自动记录文件修改
- [ ] Stop hook 提示保存待定记忆
- [ ] SessionEnd hook 保存会话摘要

## 完成后检查清单

### 记忆质量检查
- [ ] 记忆内容准确完整
- [ ] 记忆组织清晰
- [ ] URI 路径结构合理
- [ ] 优先级设置恰当

### 自动化检查
- [ ] Hooks 正常工作
- [ ] 记忆自动加载和保存
- [ ] 上下文智能预加载
- [ ] 会话摘要自动记录

### 持久化检查
- [ ] 记忆已保存到存储
- [ ] 跨会话访问正常
- [ ] 记忆索引正确
- [ ] 最近更改记录完整