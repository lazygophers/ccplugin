# Error Handling

> How errors are raised, caught, propagated, and surfaced across Python plugins, the Rust desktop backend, and Tauri commands.

---

## Scope

Three layers, three contracts:

1. Python (plugins, `lib/`, `scripts/`)
2. Rust (`desktop/src-tauri/src/`)
3. Tauri command boundary (Rust → JS)

---

## Python Rules

- **Raise standard exceptions** for invariants: `ValueError` for invalid input, `TypeError` for wrong types, `RuntimeError` for "should be unreachable"/init order, `FileNotFoundError`/`PermissionError` for FS, `KeyError`/`LookupError` for missing keys.
- **Custom exceptions only on real domain boundaries.** A plugin may define `class MemoryError(Exception)` if callers in other plugins need to discriminate; otherwise a stdlib exception is fine.
- **Do not use bare `except:` or `except Exception` to swallow.** A bare except is acceptable only at the outermost CLI/hook boundary, and it MUST log the traceback and re-exit non-zero (or signal failure to the caller).
- **No `try/except/pass` inside library code.** If you cannot recover, propagate.
- **At system boundaries** (CLI argv parsing, hook stdin parsing, network I/O), validate eagerly:
  ```python
  # .claude/hooks/session-start.py:628-633 — boundary parser
  try:
      hook_input = json.loads(sys.stdin.read())
      if not isinstance(hook_input, dict):
          hook_input = {}
  except (json.JSONDecodeError, ValueError):
      hook_input = {}
  ```
  Catch only the specific exceptions you can recover from; never `except Exception`.
- **Init-order errors are loud.** `lib/db/core.py:165-167` raises `RuntimeError("数据库未初始化，请先调用 initialize()")` when accessed too early. Use this pattern for any singleton.

### Logging vs. raising

- Raise when the caller can recover or report.
- Log + re-raise at observability layers (hooks, command entrypoints).
- Never log a stack trace and silently continue. Either re-raise or convert to a structured error response.

---

## Rust Rules

- **`Result<T, E>` everywhere.** No `panic!`, `unwrap()`, or `expect()` outside test code, build scripts, or process startup with no recovery path.
- **Error type at the command edge is `String`.** This is the project convention: every `#[tauri::command]` returns `Result<T, String>` so the JS side gets a deserializable message.
- **Use `?` for propagation.** Convert library errors with `.map_err(|e| e.to_string())?` at the command boundary.
- **Domain layer may use richer errors.** Inside `services/`, prefer `thiserror`-style enums or `anyhow::Result` — but flatten to `String` when crossing into a `#[tauri::command]`.
- **Background tasks must report failures via events.** A panicking `tokio::spawn` task does NOT bubble to the JS side. Always `match` the result and emit a `*-failed` event on the error branch (see [tauri-patterns](./tauri-patterns.md)).

---

## Tauri Command Error Envelope

Tauri serializes the `Err(String)` of a command to a JS rejected promise. The frontend MUST treat it as an opaque message and display it via the toast/notification layer — do NOT parse it.

Reference (`desktop/src-tauri/src/commands/python.rs:5-22`):

```rust
#[tauri::command]
pub fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    _app_handle: AppHandle,
) -> Result<(), String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;       // string-typed Err

    let task = Task::new(TaskType::Install, plugin_name, Some(marketplace), scope);
    task_queue.add_task(task)?;                          // bubble service error
    Ok(())
}
```

Rules:

- The command does the **shortest** possible work: validate, enqueue, return.
- Long-running failures are surfaced via `*-failed` events with payload `{ "plugin": ..., "error": ... }` (see `.claude/memory/desktop-event-driven-architecture.md`).
- Never return a `Result<_, MyEnum>` from a `#[tauri::command]`; flatten to `String` so the frontend never depends on Rust's enum layout.

---

## Hook Process Errors

Hook processes (Python scripts run by Claude Code) communicate failure via:

- **Exit code**: `0` = success/continue; non-zero = halt.
- **Stderr**: a short human-readable reason (Claude Code may surface this to the user).
- **Stdout**: structured JSON (when applicable) — never write log-noise to stdout in a hook.

Hook handlers should NEVER raise into the Claude Code process. Wrap the entire body and convert to exit codes:

```python
# pattern (see .claude/hooks/session-start.py main())
def main():
    try:
        ...do work...
    except Exception as e:
        print(f"hook failed: {e}", file=sys.stderr)
        sys.exit(0)   # 0 to NOT halt the user's session — choose carefully
```

For non-blocking diagnostic hooks (the common case in this repo) use exit `0` even on internal failure so the user is never blocked. For validating hooks (PreToolUse blockers), use non-zero.

---

## Forbidden Patterns

```python
# ❌ Swallowing all exceptions in library code
try:
    do_thing()
except Exception:
    pass

# ❌ Logging then continuing without recovery
try:
    parse(data)
except Exception as e:
    logging.error(f"failed: {e}")    # then code keeps going as if nothing happened
```

```rust
// ❌ Panic in production
let q = task_queue().expect("must be init");      // crashes the desktop app

// ❌ Custom Err type leaking to JS
#[tauri::command]
fn x() -> Result<(), MyError> { ... }              // frontend now couples to MyError shape

// ❌ Dropping a Result in a spawned task
tokio::spawn(async move {
    do_install().await;                            // ← no match, no event on failure
});
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `except Exception as e: log(e)` then continuing | Re-raise, or convert to a typed return like `(ok, error)` |
| Returning `Err(MyEnum)` from a Tauri command | Map to `String` at the boundary; keep the enum internal |
| Hook raising and crashing the agent process | Wrap top-level body, exit `0` for advisory hooks, non-zero only for blockers |
| `unwrap()` because "this can't fail" | Use `?` or `ok_or(...)`; surface the impossibility as a `String` |
| Background `tokio::spawn` swallowing errors | Always emit `<domain>-<entity>-failed` event in the `Err` branch |
| Catching `BaseException` in Python | Catch `Exception` at most; never `BaseException` (would catch `KeyboardInterrupt`, `SystemExit`) |

---

## References

- `desktop/src-tauri/src/commands/python.rs:5-79` — canonical `Result<T, String>` boundary
- `lib/db/core.py:163-167` — RuntimeError for misuse of singleton
- `.claude/hooks/session-start.py:625-633` — defensive boundary parser
- `.claude/memory/desktop-event-driven-architecture.md` §错误处理 — failed-event pattern
- `plugins/memory/scripts/hooks.py:33-49` — try/finally for resource lifecycle in hooks
