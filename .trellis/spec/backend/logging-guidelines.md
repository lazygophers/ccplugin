# Logging Guidelines

> Logging conventions for ccplugin Python code. Logging is provided by the in-house `lib.logging` module.

---

## Scope

How and when to log in plugins, `lib/`, `scripts/`, and hooks. Rust logging in `desktop/src-tauri/` is out of scope here (use `tracing`/`log` crates per `desktop/` conventions).

---

## Library

- Module: `lib.logging` (`lib/logging/__init__.py:24`).
- Implementation: `lib/logging/manager.py` — Rich-based, single-instance `RichLoggerManager`.
- Output:
  - File: hourly-rotated `YYYYMMDDHH.log` under the project log dir; auto-cleans logs older than 3 hours.
  - Console: off by default. `enable_debug()` turns on console output (DEBUG and above).

---

## Public API

```python
from lib import logging

logging.info("operation started")
logging.debug("internal detail")          # only printed to console after enable_debug()
logging.warn("non-fatal anomaly")          # alias: logging.warning
logging.error("operation failed")
logging.enable_debug()                     # opt-in console output for the current process
```

The exported names come from `lib/logging/__init__.py:24-33`:

```python
from .manager import enable_debug, info, debug, error, warn, warning

__all__ = ['enable_debug', 'info', 'debug', 'error', 'warn', 'warning']
```

---

## Levels

| Level | Use for | Example |
|-------|---------|---------|
| `debug` | Internal flow, intermediate values, only useful when troubleshooting | `logging.debug(f"handle_pre_tool_use: tool={tool_name}")` |
| `info` | Normal lifecycle events visible to users/operators | `logging.info("handle_session_start: 加载会话记忆")` |
| `warn` (`warning`) | Anomaly that did not stop the operation | `logging.warn("config missing optional field 'X'; using default")` |
| `error` | Operation failed; user/operator action may be needed | `logging.error(f"db init failed: {e}")` |

There is no `critical` / `fatal` level. Catastrophic failures should `error` + raise.

---

## Caller Info Is Automatic

`RichLoggerManager` injects the caller's `file:line` into every log line via `inspect.stack()` (`lib/logging/manager.py:148-165`). You do NOT need to prefix messages with the function name or module — duplicated info is noise.

---

## Structured Fields

This logger is text-based, not JSON. To make logs greppable, follow these conventions:

- **Prefix with the handler/operation name**, colon-separated:
  ```python
  logging.info("handle_session_start: loaded 5 memories")
  logging.debug(f"install_plugin: plugin={name} marketplace={mp}")
  ```
- **Use `key=value`** for fields, comma-separated, lowercase keys:
  ```python
  logging.info(f"plugin install: name={name}, scope={scope}, status=ok")
  ```
- Quote values that contain spaces. Keep the line on a single physical line.

---

## What to Log

- **Entry/exit of long operations** (DB init, network calls, plugin install/uninstall).
- **Boundary errors** (failed JSON parse, missing required fields).
- **Resource lifecycle** (connection open/close, file written).
- **Hook events** (which hook fired, which tool, key inputs — see PII rules below).

---

## What NOT to Log

- **Secrets / credentials**: API keys, tokens, passwords, signed URLs.
- **PII**: usernames tied to private data, email addresses (unless the user IS the operator), file contents.
- **Full request/response bodies**: log a fingerprint or size instead.
- **High-frequency tight loops**: throttle or use `debug`. Repeated `info` lines per iteration belong in `debug`.

If a log line might contain user content, redact:

```python
preview = content[:200] if len(content) > 200 else content
logging.info(f"saved memory uri={uri} len={len(content)} preview={preview!r}")
```

(See `plugins/memory/scripts/hooks.py:43-45` for an example of length-bounded preview.)

---

## When to Print vs Log

- **`print` is forbidden** in `lib/`, plugin scripts (except for hook stdout protocol output, see [hooks-contract](./hooks-contract.md)), and any long-running code.
- **CLIs in `scripts/`** may use `rich` for user-facing output (tables, prompts) — that is a UI choice, not logging. Internal events still go through `lib.logging`.
- **Hooks** must keep stdout clean for the hook protocol; diagnostics go to the log file via `lib.logging`, not to stdout.

---

## Code Excerpt — Real Usage

From `plugins/memory/scripts/hooks.py:33-49`:

```python
def handle_session_start(hook_data: Dict[str, Any]) -> None:
    logging.info("handle_session_start: 加载会话记忆")

    async def _handle():
        await init_db()
        try:
            core_memories = await get_memories_by_priority(max_priority=3)
            if core_memories:
                for mem in core_memories[:5]:
                    content_preview = mem.content[:200] if len(mem.content) > 200 else mem.content
                    print(f"[Memory:{mem.uri}] {content_preview}...")
        finally:
            await close_db()

    run_async(_handle())
```

Note:

- `logging.info` for the lifecycle event.
- `print(...)` here is the **hook's stdout protocol output** (injecting context back into the session) — that is the only legitimate use of `print` in this file.

---

## Forbidden Patterns

```python
# ❌ Logging secrets
logging.info(f"login: user={u} password={pw}")
logging.debug(f"api key: {os.environ['CLAUDE_API_KEY']}")

# ❌ Logging the entire request/response body
logging.info(f"response: {response.text}")          # may be huge, may contain PII

# ❌ print() instead of logging in long-running code
def install_plugin(...):
    print("starting install")                        # use logging.info

# ❌ Manual file:line in messages (already added by the logger)
logging.info(f"main.py:42: starting")

# ❌ One log per loop iteration at INFO
for f in thousands_of_files:
    logging.info(f"processing {f}")                  # use debug, or batch summaries
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mixing `print` and `lib.logging` in a hook | All diagnostics → `lib.logging`; `print` only when emitting hook protocol output |
| Logging at INFO inside hot loops | Demote to DEBUG or summarize once per batch |
| Forgetting `enable_debug()` while debugging locally | Add `logging.enable_debug()` at the top of the script (remove before commit) |
| Putting structured data in the message body without keys | Use `key=value` form so logs are grep-friendly |
| Logging exceptions as strings without context | `logging.error(f"step={step} failed: {e}")` — include the operation, not just the exception |

---

## References

- `lib/logging/__init__.py:24-33` — public API
- `lib/logging/manager.py:31-80` — manager init, hourly file rotation, 3h cleanup
- `lib/logging/manager.py:124-146` — `info`/`debug`/`warn`/`error` implementations
- `plugins/memory/scripts/hooks.py:33-49` — real plugin usage with redacted preview
