---
name: skein-workspace
description: 维护 .skein/ 工作区与 task.md 看板。task 生命周期节点 (create/start/阶段推进/finish) 后更新看板时使用 — 一律经 skein.py, 禁直接编辑 task.md。
---

# skein-workspace — 工作区与看板维护

`.skein/` 工作区 + `task.md` 看板的维护规约。**一切经 `skein.py`, 禁直接编辑 `.skein/task.md`** (guard hook 硬阻 + 格式漂移)。

工作区目录布局与 `skein.py` 命令速查详见 references/layout-and-commands.md。

## 看板维护铁律

- **禁直接 Edit/Write/MultiEdit `.skein/task.md`** — guard-skein.sh PreToolUse 硬阻。
- **禁直接读写 `.skein/state.json`** — guard-skein.sh 硬阻 Read/Edit/Write; 取 focus 用 `skein.py current`, 改用 create/start/finish。
- 每个生命周期节点后跑 `skein.py board` 重渲染。看板落后于实际 = 维护失效。
- state.json 变更自动刷 task.md (skein.py 内 `_set_focus` 唯一写入口即刷看板)。
- 状态列: pending → in_progress → check → completed (archived 移出 tasks/)。
- ⭐ 标记 = focus (默认操作对象, 最近 start 的)。

## 与其他 skill 分工

- `skein-flow` 调度全流程, 在各节点调本 skill 的看板更新。
- `skein.py` create/start/finish 已内建 board 重渲染 — 手动 `skein.py board` 仅用于中途状态漂移修正 (如 subtask 进度更新)。
