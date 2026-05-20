---
name: desktop-event-driven-architecture
description: @desktop 事件驱动架构核心规则 - Rust 业务 + 事件通知 + 单向数据流, 无阻塞 UI
type: project
---

# @desktop 事件驱动架构

> 仅核心规则。完整 Rust/TS 代码样板、迁移示例、Context Provider 模板见 @desktop 项目 `docs/architecture.md` (待迁出本 memory 时建)。

## 4 原则

1. **Rust 优先**: 业务逻辑全在 Rust 侧, TS 仅负责 UI 渲染
2. **事件驱动**: Rust → Event → Frontend State → UI Render, 禁同步等待结果
3. **单向数据流**: 前端不直接改业务状态, 必经事件
4. **无阻塞 UI**: 命令立即返回 (fire-and-forget), 进度走事件持续推

## 反模式 vs 正模式

```typescript
// ❌ Command-and-Wait — UI 阻塞
const result = await invoke<CommandResult>("install_plugin", { pluginName });

// ✅ Event-Driven — 立即返回 + 监听
invoke("install_plugin", { pluginName });
const unlisten = await listen<PluginInstallProgress>(
  "plugin-install-progress",
  (event) => updateUI(event.payload),
);
```

## 事件命名约定

格式: `<domain>-<entity>-<action>` (全 kebab-case)。

动作后缀:
- `-started` 操作开始
- `-progress` 进行中 (可多次触发)
- `-completed` 成功完成
- `-failed` 失败
- `-changed` 状态变化

### 标准事件列表

| 事件 | 方向 | Payload |
|---|---|---|
| `plugin-install-progress` | Rust→Front | `PluginInstallProgress` |
| `plugin-install-completed` | Rust→Front | `CommandResult` |
| `plugin-install-failed` | Rust→Front | `{ error: string }` |
| `plugin-uninstall-progress` | Rust→Front | `PluginInstallProgress` |
| `plugin-uninstall-completed` | Rust→Front | `CommandResult` |
| `plugin-update-progress` | Rust→Front | `PluginInstallProgress` |
| `plugin-update-completed` | Rust→Front | `CommandResult` |
| `plugin-list-changed` | Rust→Front | `{ plugins: PluginInfo[] }` |
| `marketplace-refresh-started` | Rust→Front | `{}` |
| `marketplace-refresh-completed` | Rust→Front | `{ plugins }` |
| `cache-clean-completed` | Rust→Front | `CommandResult` |

## 迁移优先级

1. **高频用户操作** (install/uninstall/update) — 优先迁
2. **耗时长任务** (marketplace refresh / cache clean) — 次优
3. **快速查询** (plugin list / config get) — 不迁, 保持 invoke 同步返

## 关键约束 (复盘防回归)

- 命令必须立即返回, 不能 `await Rust 完成`
- 事件监听器在组件 unmount 必 `unlisten()`, 防内存泄漏
- 进度事件 throttle (~16ms / 60fps), 防过载
- 状态管理走 React Context + reducer, 不在事件 handler 里直接 setState
