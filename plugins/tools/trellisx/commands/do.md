---
name: do
description: 强制以 Trellis task 处理本次请求 (完整 plan→exec→check→finish 闭环); /do 即创建同意, 跳过"是否建 task"询问
argument-hint: [task]
arguments: [任务描述]
---

# /do — 强制 Trellis task 闭环

用户用 `/do` **显式要求**: 把以下请求**强制作为 Trellis task 处理**, 禁止 inline 直接做 (即使看起来简单)。`/do` 跳过"要不要建 task"的询问 (用户已表态: 要)。但 **`/do` 不等于"新建 task"** —— 仍须先判这是**全新任务**还是**对现有 active task 的补充/延续**, 再决定新建还是并入。

请求: $ARGUMENTS

## 强制流程 (plan → exec → check → finish, 不可跳步)

1. **判新旧 + 登记** — 先 `python3 ./.trellis/scripts/task.py current --source` 看有无 active task, 再判断本请求:
   - **全新任务** (与 active task 无关, 或无 active task) → `task.py create "<title>" --slug <name>` 新建。多个独立可验收交付 → parent + child (`--parent`); 单一交付 → 单 task。
   - **现有 task 的补充 / 延续** (扩展、修订、补做当前 active task 的一部分) → **不新建顶层 task**: 回到 planning 修订该 task 的 `prd.md` / `implement.md` 并重新规划; 若是可独立验收的子交付, 用 `task.py create --parent <现有 task>` 挂为 child。
   - **判不准** → 用 AskUserQuestion 问用户"这是新任务, 还是对 `<active task>` 的补充?", 禁自行替用户决定。
2. **planning** — 加载 `trellis-brainstorm` 探索需求 + `trellisx-orchestrate` 编排, 写 `prd.md` (复杂任务加 `design.md` + `implement.md`); 多交付在 PRD 出 mermaid 调度图显式标并行组 + 依赖箭头。
3. **激活** — 产物评审后 `task.py start` → status=in_progress。
4. **exec** — worktree 隔离 (全部源码改动落 `<git根>/.worktrees/`, 主工作区保持干净); 多交付无依赖 child 同一回复一次性派多 sub-agent (真并行), 单交付 main 在 worktree 内直接写。
5. **check** — `trellis-check` 质量验证 (spec 合规 / lint / type-check / tests); 未过 → 修复重检, 不跳 finish。
6. **finish** — check 通过 → 提交 (Phase 3.4) → `task.py archive` 归档收尾。

## 硬规

- ⛔ **禁 inline 跳过 task** —— 这是 `/do` 的全部意义; 即使请求看起来极简也走 task。
- ⛔ **禁跳过 check 或 finish** —— 闭环不完整 = 未完成; **未 archive 禁宣告 Done / 禁结束本轮**。
- ⛔ check 未过禁推进到 finish; 先修复重检。
- 非 trellis 项目 (无 `.trellis/`) → 提示用户先 `trellis init`, 不强行建 task。

> 与 `trellisx-apply` 注入的 workflow 规约一致: 本 command 是「主动强制建 task」的快捷入口, apply 注入的 no_task 倾向是「被动推荐建 task」的常驻提示。两者互补。
