---
name: skein-flow
description: 强制 task 闭环。复杂/多步/跨文件请求, 或用户显式要求把请求作为 SKEIN task 处理时使用 — 强推 plan→exec→check→finish 全流程, main 作调度器派 subagent 在 worktree 内执行, 禁 inline 直接做。
---

# skein-flow — 强制 SKEIN task 闭环

把请求**强制作为 SKEIN task 处理**, 走 plan→exec→check→finish, 禁 inline 直接做 (即使看似简单)。加载本 skill = 「建 task 同意」信号。但**≠ 一定新建** — 先判**全新任务** vs **对现有 active task 的补充**, 再决定新建/并入。

## 执行载体铁律 (最高优先级)

- 🔴 **「派 agent」= 真实调用 `Agent` 工具, 不是叙述**。每个「派 agent」动作 MUST 在同一回复产生真实 tool_use。禁在无 `Agent` 调用时回传「已派出 / 在做」— 宣称 ≠ 调用 = 幻觉跳步。task/看板/worktree 的「已建」同理必须是真跑过命令的结果。
- **main 默认禁写源码** — 改源码 / 跑 check 派 subagent。仅特别情况例外 (≤3 文件微改 / 上下文密集决策 / 用户显式要求), 且必在 task worktree 内。
- **exec/check 派 subagent, main 作调度器** — 动态 DAG 派各 subagent 各执行 1 subtask (并发上限 2, 完成即派), 共享 task worktree。详见 `skein-orchestrate`。
- **有 task 必有 worktree** — task 在其 worktree 内执行 (`skein.py start` 自动建), 主工作区零改动; 默认 1 task 1 worktree。finish 后自动销。
- **`skein.py` 由 main 同步跑** — create/start/finish/archive 是任务记录管理, main 直接跑, 不派 agent、不算实质工作。
- **看板经 `skein.py board`** — 禁直接编辑 `.skein/task.md` (guard hook 硬阻)。
- **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) subagent 不能与用户对话; subagent 缺信息在返回标 `需要: <问题>` 由 main 转达。
- **每个 dispatch prompt 6 字段自包含**: 目标 / 已知 (含 `Active task: <id>` + worktree 路径) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- **完成即时回传** — 每个 subagent 完成或阻塞, main 立即输出摘要, 禁批量延迟汇总。

## 强制流程 (不可跳步)

> 贯穿全程: 每个生命周期节点 (create/start/阶段推进/finish) 后跑 `skein.py board` 更新看板。

0. **前置** — 无 `.skein/` → 先 `python3 <plugin>/scripts/skein.py init`。判新旧 (新建 vs 并入 active task), 不准 → `AskUserQuestion`。
1. **plan** (main 同步) — 委托 `skein-add`: 判新旧 + `skein.py create` 登记 + brainstorm 需求/方案 + grill 硬门。产出 `.skein/tasks/<id>/{prd.md,implement.md}`[+design.md]。
2. **memory recall** (main) — 委托 `skein-memory` recall: 按任务描述召回相关 recall 规则注入 (core 规则已由 SessionStart 常驻)。
3. **激活** (main) — 产物齐 → `AskUserQuestion` 交用户评审 → `skein.py start <id>` (建 worktree, status=in_progress) → 更新看板。
4. **exec** (subagent 编排) — main 作调度器, 动态 DAG 派 subagent 各执行 1 subtask, 改动落 task worktree。见 `skein-orchestrate`。每个 agent 完成即回传。
   - 🔴 **异步等待 MUST 输出任务清单** — 派出异步任务后结束本回合前, 输出全景表 (4 列: id/状态/摘要/进度%)。
   - 🔴 **exec 阶段禁问用户顺序** — 顺序归 planning (调度图 + deps + 冲突 DAG)。ready 即派 / 完成即派 / 并发 2。PRD 缺调度图 → 退回 planning 补, 不在 exec 问。
5. **check** (subagent) — 质量验证 (lint / type-check / tests / spec 合规); 未过 → 派 agent 定点修复重检, 不跳 finish。
6. **finish** (main 同步) — check 通过 →
   - 🔴 **sediment 判定门** — 按 `skein-memory` 的 checklist 逐项 ✅/❌ 输出 trace, 判本 task learning → core/recall/drop。触发 → 走 sediment 提案 (审批后写盘) 再 finish; 全否 → 跳过 (仍输出全 ❌ trace)。
   - **清理** — `TaskList` 查残留 subagent / 后台任务, `TaskStop` 关闭。禁 `sleep` 轮询等后台跑完。
   - `skein.py finish <id>` — 自动 commit worktree → merge --no-ff 回主 → archive → 销 worktree。冲突 → 自动 abort + 报冲突文件, 停, 转手动解, 禁强解 / 禁当成功。
   - 更新看板 (status=completed)。

## 作用域边界 (何时建 task)

| 特征 | 判定 |
| --- | --- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免 |
| 单文件单处改, ≤20 行且位置已知 | 豁免 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤 | **必建 task** |
| 需外部调研 / 产出文档交付 | **必建 task** |
| 边界模糊 | **AskUserQuestion 用户裁定** |

## 完成判定

- 走完 plan→exec→check→finish — **未 archive = 未完成, 禁宣告 Done**。
- finish 前清理悬挂 subagent / 后台任务 (`TaskList`/`TaskStop`), 未关 = 未闭环。
- sediment 判定 trace 未输出 = 流程错误。

## ⛔ 反例 (命中 = 流程错误)

| 禁 | 改为 |
|---|---|
| main 直接改源码 / 跑 check (非特别例外) | 派 subagent 在 worktree 内 |
| 把 skein.py 派 agent 执行 | main 同步跑 |
| inline 跳过 task | 一律走闭环 (本 skill 全部意义) |
| 极简请求 (纯查询 / 单文件 ≤20 行) 强建 task | 该 inline 的 inline |
| check 未过推进 finish / 未 archive 宣告 Done | 先修复重检 / 未闭环 |
| 口头宣称「已派 agent / 已建 task」但无 tool_use | 先真实调用再回传 |
| exec subagent 在主工作区改源码 (无 worktree) | 必在 task worktree |
| 直接 Edit/Write `.skein/task.md` | 经 `skein.py board` |
| 纯文本提问代替 `AskUserQuestion` | 用工具 |
| exec 阶段问用户「先做哪个」 | 顺序归 planning |
| sediment 判定未输出 trace | 逐项 ✅/❌ 输出 |
