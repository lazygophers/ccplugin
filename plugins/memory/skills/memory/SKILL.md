---
name: memory
description: |
  Intelligent memory system with hooks integration. Automatically manages memories 
  across sessions with smart loading, recording, and saving capabilities.
  
  Use this skill to:
  - Read stored memories by URI path
  - Create new memories with priority and disclosure
  - Update existing memories
  - Search memories by keyword
  - View memory index and recent changes
  
auto-activate: always:true
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
