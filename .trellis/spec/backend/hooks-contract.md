# Hooks Contract

> Claude Code hook events, the JSON I/O protocol, exit codes, and timeout budget — as implemented in this repo.

---

## Scope

Every hook handler in this repo (`.claude/hooks/*.py`, `plugins/*/scripts/hooks.py`) is a short-lived process invoked by Claude Code on specific lifecycle events. This file documents the contract every handler must satisfy.

---

## How Hooks Are Wired

Hooks are declared in two places:

1. **Repo-level** Claude Code config (under `.claude/`) — for cross-cutting concerns like Trellis context injection.
2. **Plugin manifests** — `plugin.json:hooks` map event names to commands. Real example, `plugins/memory/.claude-plugin/plugin.json:22-34`:
   ```json
   "hooks": {
     "SessionStart": [
       {
         "hooks": [
           {
             "type": "command",
             "command": "PLUGIN_NAME=memory uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks",
             "async": true,
             "timeout": 1000
           }
         ]
       }
     ]
   }
   ```

Each entry has:

| Field | Notes |
|-------|-------|
| `type` | `"command"` (only supported value here) |
| `command` | shell command; `${CLAUDE_PLUGIN_ROOT}` resolves to the install dir |
| `async` | `true` lets the hook return immediately while work continues |
| `timeout` | budget in milliseconds; the hook process is killed past this |

---

## Supported Event Names

The events validated by `scripts/check.py:37-60`:

```
SessionStart            UserPromptSubmit         PreToolUse
PermissionRequest       PostToolUse              PostToolUseFailure
Notification            SubagentStart            SubagentStop
Stop                    StopFailure              TeammateIdle
TaskCompleted           InstructionsLoaded       ConfigChange
CwdChanged              FileChanged              WorktreeCreate
WorktreeRemove          PreCompact               PostCompact
Elicitation             ElicitationResult        SessionEnd
```

A plugin / repo hook can register for any subset. Unknown event names are ignored by Claude Code (and rejected by `scripts/check.py`).

---

## Input: stdin JSON

Every hook receives a single JSON object on stdin. Common fields (every event):

```jsonc
{
  "session_id": "string",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default" | "grant" | "deny",
  "hook_event_name": "<one of the names above>"
}
```

Event-specific fields are added on top. Examples (`scripts/check.py:217-249`):

- `InstructionsLoaded` adds `file_path`, `memory_type`, `load_reason`.
- `FileChanged` adds `file_path`, `event` (e.g. `"change"`).
- `PreToolUse` adds `tool_name`, `tool_input`.
- `Notification` adds `notification_type`, `title`, `message`.

Always read stdin defensively. Reference (`.claude/hooks/session-start.py:625-633`):

```python
def main():
    if should_skip_injection():
        sys.exit(0)
    try:
        hook_input = json.loads(sys.stdin.read())
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}
```

Rules:

- If stdin is empty or invalid JSON, fall back to `{}` and continue (advisory hooks) OR exit `0` (no-op).
- Never raise — always convert to `{}` or an exit code.

---

## Output: stdout JSON / Text

There are two valid stdout shapes depending on the hook's purpose:

1. **Advisory hooks** (the common case): write text that should be injected back into the session. The repo-level Trellis hooks use this — `.claude/hooks/session-start.py` builds a string in `StringIO` and prints it. The memory plugin uses bare `print(...)` for memory previews (`plugins/memory/scripts/hooks.py:43-45`):
   ```python
   for mem in core_memories[:5]:
       content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
       print(f"[Memory:{mem.uri}] {content_preview}...")
   ```
2. **Validating hooks** (e.g. `PreToolUse` blockers): emit a JSON object on stdout describing the decision; non-zero exit code means "block".

Either way, **stdout is a protocol channel**. Diagnostics MUST go to `lib.logging` (which writes to a log file), never to stdout.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | Success / continue. Advisory hooks should ALWAYS exit `0` even on internal failure so the user is not blocked. |
| non-zero | Halt the action that triggered the hook (only meaningful for blocking hooks like `PreToolUse`). |

Pattern for an advisory hook that wraps everything:

```python
def main():
    try:
        ...do work...
    except Exception as e:
        # Log, but do NOT block the user's session.
        logging.error(f"hook failed: {e}")
        sys.exit(0)
```

Choose non-zero only when you genuinely intend to block the operation.

---

## Timeout Budget

`timeout` (ms) in the manifest is hard. Common budgets in this repo:

| Event | Budget | Why |
|-------|--------|-----|
| `SessionStart` | 1000 ms | runs once per session; small budget keeps startup snappy |
| `PreToolUse` | 500 ms | runs before EVERY tool call; must be fast |
| `PostToolUse` | 1000 ms | runs after every tool call; can do a bit more work |
| `SessionEnd` | 1000 ms | persistence + cleanup |

If you can't finish inside the budget, set `async: true` and do work in the background — but remember: a backgrounded hook can be killed when the session ends. Persist any state explicitly.

---

## Resource Lifecycle in Hooks

Hook processes are short-lived. If you open external resources, you MUST close them, otherwise the hook process hangs at exit and the timeout kills it. Reference (`plugins/memory/scripts/hooks.py:33-49`):

```python
async def _handle():
    await init_db()
    try:
        core_memories = await get_memories_by_priority(max_priority=3)
        if core_memories:
            for mem in core_memories[:5]:
                content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
                print(f"[Memory:{mem.uri}] {content_preview}...")
    finally:
        await close_db()       # critical — hook process otherwise blocks
```

Always pair `init_db` / `close_db`, file open / close, network connect / close.

---

## Forbidden Patterns

```python
# ❌ Logging to stdout (pollutes the protocol channel)
print(f"DEBUG: tool_name={tool_name}")     # use logging.debug() instead

# ❌ Crashing on bad input
hook_input = json.loads(sys.stdin.read())  # raises if stdin is empty/invalid

# ❌ Exit non-zero on internal failure in an advisory hook
except Exception:
    sys.exit(1)                             # blocks the user's session for no good reason

# ❌ Long-running synchronous work inside a sub-second budget
await fetch_remote_index()                  # set async: true and use a background queue

# ❌ Leaving DB / file handles open
await init_db()
do_work()
# missing close_db() → process hangs, killed by timeout
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hook silently does nothing | Verify the manifest event name matches exactly (case-sensitive) |
| Hook is killed mid-work | Increase `timeout` OR set `async: true` and persist incrementally |
| Hook output never appears in session | You wrote to stderr or to the log file; advisory hooks must use stdout |
| Hook crashes the agent | Replace bare `raise` with try/except + `sys.exit(0)` for advisory; non-zero only for blockers |
| Wrong subcommand dispatched | Plugins use a single `main.py hooks` entry that switches on `hook_event_name`; ensure your dispatcher covers the event you registered |

---

## References

- `scripts/check.py:37-60` — canonical event-name list
- `scripts/check.py:99-291` — example payload schemas per event
- `.claude/hooks/session-start.py:625-680` — repo-level advisory hook (Trellis injection)
- `plugins/memory/scripts/hooks.py` — plugin hook handlers (12 handlers)
- `plugins/memory/.claude-plugin/plugin.json:22-...` — manifest hook registration
- See also: [plugin-conventions](./plugin-conventions.md), [logging-guidelines](./logging-guidelines.md)
