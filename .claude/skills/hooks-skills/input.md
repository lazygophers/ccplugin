# 钩子输入

Hooks 通过 stdin 接收包含会话信息和事件数据的 JSON：

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "EventName",
  ...
}
```

## 常见字段

| 字段 | 说明 |
|------|------|
| `session_id` | 会话 ID |
| `transcript_path` | 对话 JSON 路径 |
| `cwd` | 当前工作目录 |
| `permission_mode` | 权限模式 |
| `hook_event_name` | 事件名称 |

## PreToolUse 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

## PostToolUse 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

## Notification 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission",
  "notification_type": "permission_prompt"
}
```

## UserPromptSubmit 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate factorial"
}
```

## Stop/SubagentStop 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

## PreCompact 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

## SessionStart 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup"
}
```

## SessionEnd 输入

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "exit"
}
```

## 读取输入

### Bash 脚本

```bash
#!/bin/bash
INPUT=$(cat)
echo "$INPUT" | jq -r '.tool_name'
echo "$INPUT" | jq -r '.tool_input.command'
```

### Python 脚本

```python
#!/usr/bin/env python3
import json
import sys

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")
```
