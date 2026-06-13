---
name: trellisx-flow
description: 强制以 Trellis task 闭环处理用户指定的请求 (自判新建/并入 → plan→exec→check→finish 全程不跳步)。**仅用户显式主动调用** (/trellisx-flow 或明确要求"强制走 task 处理这个"); **禁止自动 / 被动 / 推断式调用** —— 不要因为某个请求"看起来该建 task"就自动触发本 skill, 那是 apply 注入的 no_task 倾向的职责。
when_to_use: 仅当用户**显式**输入 `/trellisx-flow`、点名本 skill、或明确说"强制以 task 处理这个请求"时调用。其他任何情况 (包括请求看起来复杂/该建 task) 一律**禁止**自动调用本 skill。
user-invocable: true
argument-hint: [task]
arguments: [任务描述]
---

# trellisx-flow — 强制 Trellis task 闭环

用户**显式调用**本 skill, 要求把其指定的请求**强制作为 Trellis task 处理**, 禁止 inline 直接做 (即使看起来简单)。调用本 skill 即「创建同意」信号 —— 跳过"要不要建 task"的询问 (用户已表态: 要)。但 **调用本 skill ≠ "新建 task"** —— 仍须先判这是**全新任务**还是**对现有 active task 的补充/延续**, 再决定新建还是并入。

处理对象 = 用户调用本 skill 时给出的请求 (任务描述 / arguments)。

## 调用边界 (重要)

- ✅ **仅用户主动**: `/trellisx-flow <描述>` 或用户明确点名。
- ⛔ **禁自动触发**: 不要因为请求"看起来该建 task / 复杂 / 跨文件"就自行调用本 skill。那种"推荐建 task"是 `trellisx-apply` 注入 workflow.md `[workflow-state:no_task]` 的常驻软提示的职责, 不是本 skill。本 skill 只在用户喊它时才动。

## 强制流程 (plan → exec → check → finish, 不可跳步)

> **贯穿全程: 及时维护 `.trellis/task.md` 看板** —— 下列每一步 (create/start/阶段推进/finish) 完成后, **立即用 `trellisx-workspace` skill 更新 `.trellis/task.md`** 看板表中该任务行 (id/名称/状态/阶段/进度/worktree)。看板落后于实际 = 维护失效。

1. **判新旧 + 登记** — 先 `python3 ./.trellis/scripts/task.py current --source` 看有无 active task, **并读 `.trellis/task.md` 看板**对照现有任务全貌 (id/名称/描述/状态), 辅助判断本请求是全新还是匹配某现有任务, 再决定:
   - **全新任务** (与 active task 无关, 或无 active task) → `task.py create "<title>" --slug <name>` 新建。多个独立可验收交付 → parent + child (`--parent`); 单一交付 → 单 task。
   - **现有 task 的补充 / 延续** (扩展、修订、补做当前 active task 的一部分) → **不新建顶层 task**: 回到 planning 修订该 task 的 `prd.md` / `implement.md` 并重新规划; 若是可独立验收的子交付, 用 `task.py create --parent <现有 task>` 挂为 child。
   - 🔴 **判不准 → 🛑 STOP**: MUST 用 AskUserQuestion 问"这是新任务, 还是对 `<active task>` 的补充?", **禁自行替用户决定**, 禁纯文本提问代替工具。
   登记后 → **更新 task.md 看板** (新建/更新该任务行)。
2. **planning** — 加载 `trellis-brainstorm` 探索需求 + `trellisx-orchestrate` 编排, 写 `prd.md` (复杂任务加 `design.md` + `implement.md`); 多交付在 PRD 出 mermaid 调度图显式标并行组 + 依赖箭头。
3. **激活** — 产物评审后 `task.py start` → status=in_progress。→ **更新 task.md 行** (状态 in_progress / 阶段 exec / worktree 路径)。
4. **exec** — worktree 隔离 (全部源码改动落 `<git根>/.worktrees/`, 主工作区保持干净); 多交付无依赖 child 同一回复一次性派多 sub-agent (真并行), 单交付 main 在 worktree 内直接写。→ **更新 task.md 进度**。
5. **check** — `trellis-check` 质量验证 (spec 合规 / lint / type-check / tests); 未过 → 修复重检, 不跳 finish。→ **更新 task.md 阶段 check**。
6. **finish** — check 通过 → 提交 (Phase 3.4) → `task.py archive` 归档收尾。→ **更新 task.md 行** (状态 completed)。

## 硬规

- ⛔ **禁 inline 跳过 task** —— 这是本 skill 的全部意义; 即使请求看起来极简也走 task。
- ⛔ **禁跳过 check 或 finish** —— 闭环不完整 = 未完成; **未 archive 禁宣告 Done / 禁结束本轮**。
- ⛔ check 未过禁推进到 finish; 先修复重检。
- ⛔ **task.md 看板必须及时维护** —— 每个生命周期节点后用 `trellisx-workspace` 更新 `.trellis/task.md`; 看板滞后视为流程缺陷。
- 非 trellis 项目 (无 `.trellis/`) → 提示用户先 `trellis init`, 不强行建 task。

> 与 `trellisx-apply` 的分工: 本 skill 是用户**主动强制建 task**的入口 (喊它才动); apply 注入的 no_task 倾向是**被动推荐建 task**的常驻软提示。两者互补, 不要混用 —— 本 skill 禁自动触发。
