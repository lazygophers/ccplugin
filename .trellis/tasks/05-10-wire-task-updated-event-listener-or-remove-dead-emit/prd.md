# PRD: Wire task-updated event listener or remove dead emit

## Problem

`desktop/src-tauri/src/services/task_queue.rs:426` emits `task-updated` event but no frontend code subscribes. Dead emit increases IPC traffic and signals broken intent (likely planned per-task progress UI not finished). Audit (deep-study task-updated row in events table) confirms zero listeners.

## Goal

Decide intent: either wire listener for legitimate UX (fine-grained per-task progress) or remove emit. No middle ground.

## Scope

### Decision required (resolve during brainstorm)

**Option A**: Wire listener
- New UI component or store updates (e.g., notification panel, task progress bar)
- Define event payload schema (task_id, status, progress, message)

**Option B**: Remove emit
- Delete `task-updated` emission
- Remove event from `events.rs` if defined there
- Confirm `plugin-event` channel covers all needed UI updates

**Recommendation**: Option B unless concrete UX need surfaces. `plugin-*-{started,progress,completed,failed}` already provides domain-specific events with richer context; `task-updated` was likely a generic placeholder.

### In-scope

If Option A:
- `services/task_queue.rs:426` — keep emit, document payload
- `events.rs` — add to event registry
- `desktop/src/services/` — new listener
- `desktop/src/components/` or page — consume event for UI
- Type definition in `desktop/src/types/`

If Option B:
- `services/task_queue.rs:426` — remove emit
- Audit any other reference to `task-updated`
- Confirm no external (non-frontend) consumer

### Out-of-scope

- Redesigning task progress UX
- Other dead/unused events (separate audit)

## Approach

1. Search `desktop/src/` for `'task-updated'` listener (confirm 0 hits)
2. Check git history for prior usage (if removed earlier, lean Option B)
3. Decide
4. Apply
5. Add lint rule or test asserting all emitted events have at least one listener (optional)

## Acceptance Criteria

- Either: emit + listener pair functional; UI demonstrates use case
- Or: emit removed, no references to `task-updated` anywhere in `desktop/`
- Build passes; no warnings about unused event constants
- Optional: regression test fails if dead emit reintroduced

## Risk

- Removing emit may break external consumer if any plugin/external script listens (unlikely; Tauri events are app-scoped)

## References

- Deep-study event audit: `research/dead-event-emit.md` (this task)
- `src-tauri/src/services/task_queue.rs:426`
- `src-tauri/src/events.rs:221`
