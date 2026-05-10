# Tauri Patterns

> Conventions for `#[tauri::command]` and event-driven Rust ↔ TypeScript communication in `desktop/`.

---

## Scope

- How to define a Tauri command.
- The "return-immediately + emit events" pattern.
- Event naming.
- What goes in `commands/` vs `services/`.

This file is the canonical spec. The session-learning notes in `.claude/memory/desktop-event-driven-architecture.md` (cited extensively here) provide the rationale and full migration playbook.

---

## Architecture Principles

From `.claude/memory/desktop-event-driven-architecture.md` §一:

1. **Rust-first**: business logic lives in Rust; TypeScript renders UI only.
2. **Event-driven**: Rust pushes state changes via events; the frontend never blocks on a long Tauri command.
3. **Unidirectional data flow**: Rust → Event → Frontend State → UI.
4. **Non-blocking UI**: commands return immediately; background tasks emit progress events.

---

## Command Shape

A Tauri command MUST:

- Be annotated `#[tauri::command]`.
- Return `Result<T, String>` where `T` is small and `Serialize`. Use `()` when the only purpose is to enqueue work.
- Do the smallest possible work synchronously: validate args, enqueue, emit a "started" event if useful, return.
- Spawn long work via `tokio::spawn` / `tauri::async_runtime::spawn`, not `.await` in the command body.

### Reference Pattern

`desktop/src-tauri/src/commands/python.rs:4-23`:

```rust
use crate::services::task_queue::{Task, TaskType};
use tauri::AppHandle;

#[tauri::command]
pub fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    _app_handle: AppHandle,
) -> Result<(), String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    let task = Task::new(
        TaskType::Install,
        plugin_name,
        Some(marketplace),
        scope,
    );

    task_queue.add_task(task)?;
    Ok(())
}
```

What this demonstrates:

- Returns `Result<(), String>` — the frontend only learns "accepted" vs "rejected at submission".
- No `.await`, no I/O, no subprocess.
- Real work happens later inside `services::task_queue`, which emits events as the task progresses.
- Errors are mapped to `String` at the boundary (see [error-handling](./error-handling.md)).

---

## Where Logic Lives

| Concern | Location |
|---------|----------|
| Validate args, enqueue, return | `desktop/src-tauri/src/commands/<domain>.rs` |
| Long-running work, retries, side effects | `desktop/src-tauri/src/services/<service>.rs` |
| Background queue + emission | `desktop/src-tauri/src/services/task_queue.rs` |
| Event constants and helpers | `desktop/src-tauri/src/events.rs` (e.g. `emit_plugin_event`) |

Commands MUST NOT import database, filesystem, or subprocess directly — go through a service.

---

## Background Tasks + Events

Once a command has enqueued work, the worker reports status via events. See `services/task_queue.rs:151-249` (uses `tauri::async_runtime::spawn` and emits `emit_plugin_event(...)` at lifecycle transitions).

Skeleton:

```rust
tauri::async_runtime::spawn(async move {
    emit_plugin_event(&app, PluginEventType::InstallStarted, &payload);

    match do_install(&plugin_name).await {
        Ok(result) => {
            emit_plugin_event(&app, PluginEventType::InstallCompleted, &result);
        }
        Err(e) => {
            emit_plugin_event(&app, PluginEventType::InstallFailed, &json!({
                "plugin": plugin_name, "error": e.to_string()
            }));
        }
    }
});
```

Rules:

- Always handle both `Ok` and `Err`. A spawned task that drops its `Result` silently strands the UI.
- Throttle high-frequency progress events server-side (~10 Hz max). See `.claude/memory/desktop-event-driven-architecture.md` §七.
- Emit a terminal `*-completed` or `*-failed` event for every started operation — UI cleanup depends on it.

---

## Event Naming

Format: **`<domain>-<entity>-<action>`**, kebab-case, all lowercase.

Action suffixes:

| Suffix | Meaning |
|--------|---------|
| `-started` | operation has begun (once per operation) |
| `-progress` | intermediate update (may fire many times) |
| `-completed` | terminal success |
| `-failed` | terminal failure (payload includes `error`) |
| `-changed` | state change (no started/completed pairing required) |

Standard events in this project (excerpt from `.claude/memory/desktop-event-driven-architecture.md` §二):

```
plugin-install-started        plugin-install-progress
plugin-install-completed      plugin-install-failed
plugin-uninstall-progress     plugin-uninstall-completed
plugin-update-progress        plugin-update-completed
plugin-list-changed
marketplace-refresh-started   marketplace-refresh-completed
cache-clean-completed
task-updated
```

When in doubt, extend the existing `<domain>-<entity>-<action>` pattern; do not invent ad-hoc names.

---

## Frontend Counterpart (summary)

The UI MUST:

- Register listeners with `listen<T>("event-name", ...)` in a top-level effect; clean up on unmount.
- Avoid `await invoke(...)` for long-running operations. `invoke` is fire-and-forget; the result arrives via events.
- Update state on events, not on command return values.

Full pattern + React examples: `.claude/memory/desktop-event-driven-architecture.md` §四–§五.

---

## Forbidden Patterns

```rust
// ❌ Long-running work inside the command
#[tauri::command]
async fn install_plugin(name: String) -> Result<CommandResult, String> {
    bridge.install_plugin(&name).await   // blocks the JS promise; UI freezes
}

// ❌ panic / unwrap in production paths
let q = task_queue().expect("must be init");

// ❌ Returning a custom enum from a #[tauri::command]
#[tauri::command]
fn x() -> Result<(), MyDomainError> { ... }   // frontend now coupled to MyDomainError

// ❌ Spawned task without error handling
tokio::spawn(async move {
    install(name).await;                       // dropped Result → no -failed event
});

// ❌ camelCase event names
app.emit("pluginInstallProgress", &payload);   // use kebab-case: plugin-install-progress
```

```typescript
// ❌ Awaiting a long-running command
const result = await invoke<CommandResult>("install_plugin", { pluginName });
// ✅ Instead: invoke("install_plugin", { pluginName }); listen for plugin-install-* events.
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| UI hangs on install | Command awaits the work; refactor to enqueue + return |
| Toast never fires on failure | Spawned task dropped its `Result`; add `match` and emit `*-failed` |
| Frontend can't deserialize the error | Returning a non-string `Err`; flatten to `String` at the boundary |
| Progress bar jumps wildly | Emitting raw progress; throttle to ~10 Hz on the Rust side |
| Events stop after a refresh | Listener registered inside a component that unmounts; lift to a top-level provider |
| Two listeners triggering twice | Forgot to call the `unlisten()` returned by `listen()` on cleanup |

---

## References

- `desktop/src-tauri/src/commands/python.rs:4-79` — canonical commands (install/uninstall/update/get_tasks)
- `desktop/src-tauri/src/services/task_queue.rs:151-249` — background spawn + event emission
- `.claude/memory/desktop-event-driven-architecture.md` — full architecture spec, naming table, migration guide
- `.claude/memory/desktop-code-quality-2026-04-05.md` — audit findings and refactor patterns
- See also: [error-handling](./error-handling.md)
