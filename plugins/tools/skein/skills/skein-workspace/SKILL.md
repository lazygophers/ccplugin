---
name: skein-workspace
description: 维护 .skein/ 工作区与 task.md 看板。task 生命周期节点 (create/start/阶段推进/finish) 后更新看板时使用 — 一律经 skein.py, 禁直接编辑 task.md。
---

# skein-workspace — 工作区与看板维护

`.skein/` 工作区 + `task.md` 看板的维护规约。**一切经 `skein.py`, 禁直接编辑 `.skein/task.md`** (guard hook 硬阻 + 格式漂移)。

## 工作区布局

```
.skein/
├── config.json          max_active / auto_commit / worktree_root
├── state.json           {focus: <id>}
├── task.md              看板 (经 skein.py board 渲染)
├── tasks/<id>/
│   ├── task.json        id/name/status/deps/worktree/branch
│   ├── prd.md           需求 (skein-add 写)
│   ├── design.md        方案 (可选)
│   └── implement.md     实现拆解 + 调度图
└── archive/<id>/        finish 后归档
```

## 看板维护铁律

- **禁直接 Edit/Write/MultiEdit `.skein/task.md`** — guard-taskmd.sh PreToolUse 硬阻。
- 每个生命周期节点后跑 `skein.py board` 重渲染。看板落后于实际 = 维护失效。
- 状态列: pending → in_progress → check → completed (archived 移出 tasks/)。
- ⭐ 标记 = focus (默认操作对象, 最近 start 的)。

## 命令速查

| 动作 | 命令 |
|---|---|
| 初始化工作区 | `skein.py init` |
| 建 task | `skein.py create <name> [--desc ..] [--deps a,b]` |
| 激活 (建 worktree) | `skein.py start <id>` |
| 完成 (merge+归档+销 worktree) | `skein.py finish [<id>]` |
| 看 focus / 全部 active | `skein.py current [--all]` |
| 列所有 task | `skein.py list` |
| 重渲染看板 | `skein.py board` |

## 与其他 skill 分工

- `skein-flow` 调度全流程, 在各节点调本 skill 的看板更新。
- `skein.py` create/start/finish 已内建 board 重渲染 — 手动 `skein.py board` 仅用于中途状态漂移修正 (如 subtask 进度更新)。
