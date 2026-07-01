# PRD — trellisx 调度规约: task.md 锁 + 多 task 并行

## Goal

两交付:
1. **task.md 禁 AI 直接编辑** — settings.json permission deny + PreToolUse hook 双保险硬阻, 仅允许 `trellisx-taskmd.py` 脚本写。保证规范性 + 省 token (脚本一行 vs AI 写表格多行)。
2. **多 task 并行调度** — task.py 支持同 session 内多 active task (current 从单值改多值), 配合冲突判定规约 (跨 task write-files/exec-scope), 并发上限不超最大并行数。

## What I know

### 交付 1 (task.md 锁)
- `trellisx-taskmd.py` 已是"唯一读写入口" (自述 line 2), 但**无硬阻** AI 直接 Edit/Write task.md
- flow SKILL 多处写"用 trellisx-workspace skill 更新 task.md" (经脚本), 但软约束
- 现状: AI 可绕过脚本直接编辑 → 规范性失控 + 耗 token
- 双保险: permission deny (tool 级硬阻) + PreToolUse hook (拦 + 提示用脚本)

### 交付 2 (多 task 并行)
- `common/active_task.py`: `resolve_active_task` 返回单 ActiveTask, session 文件存单 `current_task`
- 跨 session 多 active **已支持** (每 session 独立 current)
- **同 session 内多 task 并行**: 当前用 `start` 切 current (顶替式), 非真多 active 跟踪
- 现实场景: 本会话 audit + sediment 两 child 同时 in_progress, current 指针切来切去
- `scheduling.md` 有 subtask 级 DAG 并行 (并发 2), **无 task 级并行规约**
- 用户裁定: task.py 改支持多 active (current 返回多个)

## 交付 1 范围 (task.md 锁)

- **改**:
  - `.claude/settings.json` (或 `.claude/settings.local.json`): `permissions.deny` 加 `Edit(.trellis/task.md)` + `Write(.trellis/task.md)`
  - 新增 PreToolUse hook 脚本: 拦 Edit/Write task.md → reject + 提示"用 trellisx-taskmd.py"
  - flow SKILL + workspace SKILL: 软约束文本强化 ("禁直接编辑 task.md, 必经脚本")
- **不改**: trellisx-taskmd.py 本身 (已是正确入口), task.md 内容

## 交付 2 范围 (多 task 并行)

- **改**:
  - `common/active_task.py`: session 文件 `current_task` 单值 → `active_tasks` 列表 (向后兼容读旧单值); `resolve_active_task` 返回列表; `set_active_task` 改 add (非 replace); `clear_active_task` 改 remove
  - `task.py`: `cmd_current` 支持列所有 active; `start` 加入 active 集而非顶替; `finish` 从 active 集移除该 task
  - flow SKILL: 加"多 task 并行调度规约"段 (main 内存跟多 in_progress, 冲突判定, 并发上限 2)
  - scheduling.md: 加 task 级并行规约 (跨 task write-files/exec-scope 冲突, 复用 subtask 级算法)
- **不改**: subtask 级 DAG 调度算法 (已正确), worktree 机制

## Deliverable

| ID | 交付 | 验收 |
|---|---|---|
| D1 | settings.json deny + PreToolUse hook 脚本 | AI 试 Edit task.md 被拒; hook 提示用脚本 |
| D2 | flow/workspace SKILL 软约束强化 | grep "禁直接编辑 task.md" 命中 |
| D3 | active_task.py 多 active 支持 (单值→列表, 向后兼容) | start task A → start task B → current 列 [A, B]; finish A → current 列 [B] |
| D4 | task.py current/start/finish 改多 active | current --all 列所有; start 不顶替; finish 移除单个 |
| D5 | flow SKILL + scheduling.md 加多 task 并行规约 | 规约含冲突判定 + 并发上限 + main 调度语义 |
| D6 | 质检: claude -p 读 flow 问"多 task 怎么并行" 返回规约; 试 Edit task.md 验拒 | 双交付都可读出/拒住 |

## 验收

- task.md 直接编辑被双保险硬阻 (deny + hook)
- task.py 多 active: 同 session 可同时跟踪多 in_progress task, current/start/finish 语义正确
- 向后兼容: 旧 session 单值文件可读
- subtask 级调度零回归
- claude -p + 实测 Edit 拒绝

## 风险

- 交付 2 改 active_task.py 核心, 影响所有 task.py 命令 → 需充分回归 (start/finish/archive/list/current 全测)
- 向后兼容旧 session 文件 (单值) 必须读得到, 否则历史 session 破损

## Open

- 并发上限: subtask 级是 2, task 级也用 2 还是另定? (默认复用 2)
- hook 脚本放哪: `.claude/hooks/` 或 `plugins/tools/trellisx/scripts/`?
