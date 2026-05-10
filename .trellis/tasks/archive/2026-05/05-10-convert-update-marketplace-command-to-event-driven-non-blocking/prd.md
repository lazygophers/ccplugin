# PRD: Convert update_marketplace command to event-driven non-blocking

## Problem

`desktop/src-tauri/src/commands/marketplace.rs:140` `update_marketplace` is `async` but executes blocking `Command::new("claude").output()`, awaited synchronously by `desktop/src/pages/Marketplaces/index.tsx:268` `await MarketplacesService.update(name)`. Worse, `index.tsx:291` `Promise.all(marketplaces.map(...))` blocks entire UI on bulk refresh. Violates spec at `.claude/memory/desktop-event-driven-architecture.md` §1.4 ("命令立即返回, 后台任务通过事件持续推送进度").

## Goal

Refactor `update_marketplace` to use existing `task_queue` infrastructure: enqueue task, return task_id immediately, emit progress + completion events. Frontend listens via event handlers, no `await` on long op.

## Scope

### In-scope

Backend (`src-tauri/src/`):
- `commands/marketplace.rs:140` — change signature to enqueue + return immediately
- `services/task_queue.rs` — extend to handle `MarketplaceUpdate` task variant
- `events.rs` — emit `marketplace-update-started/progress/completed/failed` (already declared but currently emitted from inside the awaited handler; move to background task)

Frontend (`desktop/src/`):
- `services/tauri-commands.ts` or marketplace service — replace `await invoke('update_marketplace')` blocking pattern with: (1) invoke returns task_id, (2) listener handles events
- `pages/Marketplaces/index.tsx:268` — drop `await`, subscribe to events
- `pages/Marketplaces/index.tsx:291` — replace `Promise.all` with parallel enqueue + aggregated event handling

### Out-of-scope

- Other commands (only `update_marketplace`)
- Adding new event types beyond existing 4 marketplace events
- UI redesign (just plumbing)

## Approach

1. Add `MarketplaceUpdateTask { name }` variant in `task_queue` Task enum
2. Move blocking `Command::new("claude")` call into background spawn (already pattern for plugin tasks)
3. Emit `marketplace-update-started` immediately, `progress` periodically, `completed`/`failed` at end
4. Frontend: switch to fire-and-forget invoke + persistent event listener
5. UI state: track per-marketplace updating flag set on `started`, cleared on `completed`/`failed`
6. Bulk refresh: enqueue N tasks, single listener updates progress map

## Acceptance Criteria

- `invoke('update_marketplace', {name})` returns within <50ms regardless of network/subprocess time
- UI thread never blocks during marketplace update
- Bulk refresh triggers all enqueued in parallel, individual marketplaces complete out-of-order
- Failure of one marketplace doesn't block others
- Test: trigger update + click another UI element while running → no freeze
- No `await invoke` on long ops in `pages/Marketplaces/index.tsx`
- Spec compliance: matches plugin install/update/uninstall pattern exactly

## Risk

- Event listener leaks if not cleaned on unmount; use `useEffect` cleanup
- Race condition: rapid duplicate invocations create stacked tasks; dedupe by name in queue
- Backward compatibility: any code path expecting return value must be migrated

## References

- Deep-study report: `research/event-driven-violations.md` (this task)
- `.claude/memory/desktop-event-driven-architecture.md` — spec
- `src-tauri/src/services/task_queue.rs:221-281` — existing pattern
- `src-tauri/src/commands/python.rs:5-65` — reference compliant commands
