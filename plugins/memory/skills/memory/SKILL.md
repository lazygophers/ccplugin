---
description: "Cross-session memory management: read, create, update, search memories. Trigger: 'remember this', 'recall memory', 'save context', 'search memories', 'memory index'."
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

## Checklist

- URI format: `{domain}://{path}` where domain ∈ {project, workflow, user, task, system}
- Priority ≤ 2 = core (auto-loaded), 3-5 = important, 6+ = reference
- Disclosure field drives hook-based preloading

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