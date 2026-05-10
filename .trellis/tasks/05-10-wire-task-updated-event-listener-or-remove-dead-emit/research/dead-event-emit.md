# Dead Event Emit Audit (extracted from deep-study session 2026-05-10)

## Finding

Event `task-updated` emitted at `desktop/src-tauri/src/services/task_queue.rs:426` has zero listeners in `desktop/src/`.

## Verification command

```bash
grep -rn "task-updated" desktop/src/ desktop/src-tauri/src/
```

Expected: emit-only locations in src-tauri; no `listen('task-updated')` in src.

## Existing event channels

All other events follow `<domain>-<entity>-<action>` and have live listeners:

| Event | Listener |
|-------|----------|
| plugin-install-* | tauri-commands.ts:94 |
| plugin-update-* | tauri-commands.ts:94 |
| plugin-uninstall-* | tauri-commands.ts:94 |
| cache-clean-* | tauri-commands.ts:94 |
| plugin-info-* | tauri-commands.ts:94 |
| marketplace-update-* | Marketplaces/index.tsx:127 |
| **task-updated** | **NONE** |

`tauri-commands.ts:94` is unified `plugin-event` channel handler — covers domain-specific events. `task-updated` is generic and bypassed by domain-specific events.

## Decision

### Option A: Wire listener (KEEP)

Need a UX use case. Candidates:
- Aggregated task progress panel (all task types in one view)
- System tray task counter
- Notification toast on any task completion

If chosen: define payload `{ task_id, task_type, status, progress, message }`. Add component or store hook to consume.

### Option B: Remove (DROP)

If no UX justification: delete emission and any event constant.

Files to touch:
- `services/task_queue.rs:426` — delete `app_handle.emit("task-updated", ...)`
- `events.rs` — remove constant if defined
- Confirm via grep no other emitter

**Recommendation**: Option B. Domain-specific events provide all needed signals. Generic `task-updated` was likely scaffolding from initial task_queue design; obsoleted by the 4-state-per-domain model.

## Optional: prevent regression

Add CI check or pre-commit hook:
```python
# scripts/check_events.py (pseudocode)
emitted = grep_emit_calls("desktop/src-tauri/src/")
listened = grep_listen_calls("desktop/src/")
orphan = emitted - listened
if orphan:
    sys.exit(f"Dead event emits: {orphan}")
```

## Search commands

```bash
# All emit calls
rg "\.emit\([\"']" desktop/src-tauri/src/

# All listen calls
rg "listen\([\"']" desktop/src/

# Event constants
rg "task-updated" desktop/
```
