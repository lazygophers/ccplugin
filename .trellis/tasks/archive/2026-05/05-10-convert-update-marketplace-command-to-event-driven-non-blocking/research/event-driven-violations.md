# Event-Driven Violations Audit (extracted from deep-study session 2026-05-10)

## Spec source

`.claude/memory/desktop-event-driven-architecture.md`

Key rules:
- §1.4: 命令立即返回, 后台任务通过事件持续推送进度
- Rust 业务逻辑, TypeScript 仅渲染
- 单向数据流: Rust → Event → Frontend State → UI Render
- 无阻塞 UI: 命令立即返回
- 事件命名: `<domain>-<entity>-<action>`

## Compliance summary

✅ Plugin install/update/uninstall (`commands/python.rs:5-65`) — task queue + emit + non-blocking
✅ Event naming (17/17 events conform)
✅ Frontend listeners wired for plugin operations

## Violation: update_marketplace

### Backend
`desktop/src-tauri/src/commands/marketplace.rs:140`
```rust
#[tauri::command]
async fn update_marketplace(name: String, app_handle: AppHandle) -> Result<...> {
    // currently: emits started event, then awaits Command::new("claude").output()
    // synchronously — caller's Promise resolves only after subprocess completion
}
```

### Frontend (3 violation sites)
1. `desktop/src/pages/Marketplaces/index.tsx:268`
   ```ts
   await MarketplacesService.update(marketName);  // blocks UI thread for entire subprocess
   ```
2. `desktop/src/pages/Marketplaces/index.tsx:291`
   ```ts
   await Promise.all(marketplaces.map((m) => updateMarketplace(m.name)));
   // blocks bulk refresh UI; one slow marketplace stalls all
   ```

## Reference compliant pattern

`commands/python.rs:5` (install_plugin):
```rust
#[tauri::command]
fn install_plugin(name: String, marketplace: String, scope: String, app_handle: AppHandle)
    -> Result<TaskId, String>
{
    let task_id = task_queue::enqueue(Task::Install { name, marketplace, scope })?;
    Ok(task_id)  // returns immediately
}
```

Background task in `services/task_queue.rs:221-281` handles emission:
- `plugin-install-started` at task pickup
- `plugin-install-progress` periodic
- `plugin-install-completed` or `plugin-install-failed` at end

## Refactor plan

### 1. Add task variant

`services/task_queue.rs` — extend `Task` enum:
```rust
enum Task {
    Install { name, marketplace, scope },
    Update { name, marketplace, scope },
    Uninstall { name },
    MarketplaceUpdate { name },  // NEW
}
```

### 2. Background handler

In task queue worker dispatch:
```rust
Task::MarketplaceUpdate { name } => {
    emit("marketplace-update-started", &payload);
    let result = run_claude_marketplace_update(&name);  // blocking subprocess in worker thread
    match result {
        Ok(_) => emit("marketplace-update-completed", &payload),
        Err(e) => emit("marketplace-update-failed", &payload_with_error),
    }
}
```

### 3. Command becomes thin

`commands/marketplace.rs:140`:
```rust
#[tauri::command]
fn update_marketplace(name: String) -> Result<TaskId, String> {
    task_queue::enqueue(Task::MarketplaceUpdate { name })
}
```

Note: signature changes from `async` returning unit-on-completion to sync returning task_id.

### 4. Frontend listener

`desktop/src/services/marketplaces.ts` (or equivalent):
```ts
export class MarketplacesService {
    static update(name: string): Promise<string> {
        return invoke('update_marketplace', { name });  // returns task_id
    }

    static onUpdateEvent(handler: (event: MarketplaceUpdateEvent) => void) {
        listen('marketplace-update-started', handler);
        listen('marketplace-update-progress', handler);
        listen('marketplace-update-completed', handler);
        listen('marketplace-update-failed', handler);
    }
}
```

### 5. Page update

`pages/Marketplaces/index.tsx`:
```tsx
useEffect(() => {
    const unsubs = MarketplacesService.onUpdateEvent((event) => {
        setMarketplaceState((prev) => updateMarketplaceStatus(prev, event));
    });
    return () => unsubs.forEach((u) => u());
}, []);

const handleUpdate = (name: string) => {
    MarketplacesService.update(name);  // fire-and-forget, no await
};

const handleRefreshAll = () => {
    marketplaces.forEach((m) => MarketplacesService.update(m.name));  // parallel enqueue
};
```

## Edge cases

- Duplicate enqueue: dedupe by name in queue (skip if already pending/running for same marketplace)
- Listener leak: `useEffect` cleanup must call returned unsubscribe fns
- Event payload schema: `{ name: string, status: 'started'|'progress'|'completed'|'failed', message?: string, error?: string }`

## Test plan

- Unit: enqueue returns task_id immediately (<10ms)
- Integration: trigger update, click another button — UI responsive
- Bulk: 5 marketplaces update in parallel, individual completions out-of-order
- Failure: one marketplace fails, others continue
