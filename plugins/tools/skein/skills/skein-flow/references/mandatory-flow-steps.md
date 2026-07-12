# 强制流程分步细则 (不可跳步)

> 贯穿全程: 每个生命周期节点 (create/start/阶段推进/finish) 后跑 `skein.py board` 更新看板。
> 骨架表见 `../SKILL.md`「强制流程」段; 本文每步一章节, 展开触发/命令/硬门/失败处理。

## 步骤 0 · 前置

- 无 `.skein/` → 先 `python3 <plugin>/scripts/skein.py init`。
- 判新旧: 全新任务 → 新建; 对现有 active task 的补充/延续 → 并入。判不准 → `AskUserQuestion`, 禁自行替用户决定。

## 步骤 1 · plan (main 同步)

- 委托 `skein-planning`: 判新旧 + `skein.py create` 登记 + brainstorm 需求/方案 + grill 硬门 (必走)。
- 产出 `.skein/task/<id>/{prd.md,implement.md}`[+`design.md`]。
- planning 为交互式 (brainstorm/grill 逐问用户), subagent 不能与用户对话, 故全程 main 同步前台, 不派 subagent。

## 步骤 2 · memory recall (main)

- 委托 `skein-memory` recall: 按任务描述召回相关 recall 规则注入。
- core 规则已由 SessionStart 常驻, 此步只补 recall 层。

## 步骤 3 · 激活 CHECKPOINT (main)

- 产物齐 → `AskUserQuestion` 交用户评审 → **用户批准前禁 start**。
- `skein.py start <id>` (建 worktree, status=in_progress) → 更新看板。
- 用户驳回 → 退回 plan 修工件重审, 禁绕过。
- **start 前须已 `subtask add` ≥1** (planning 拆分产物); 无 subtask 时 `start` 直接报错 — 拆分未落 subtask = planning 未完, 退回补。

## 步骤 4 · exec (agent 编排)

- main 作调度器, 动态 DAG 为每个 subtask 选合适 agent (按任务性质挑现有 agent, 无合适的用 `skein-executor`) 各执行 1 subtask, 改动落 task worktree。
- 调度算法 (并行只看 depends_on DAG / ready 即派 / 并发 2 / 完成即派 / dispatch prompt 6 字段携带执行纪律与递归护栏) 见 [scheduling-algorithm.md](scheduling-algorithm.md)。每个 agent 完成即回传。
- **异步等待 MUST 输出任务清单** — 派出异步任务后结束本回合前, 输出全景表 (4 列: id/状态/摘要/进度%, 状态枚举 进行中/等待中/阻塞), 格式见 [progress-reporting.md](progress-reporting.md)。
- **exec 阶段禁问用户顺序** — 顺序归 planning (调度图 + depends_on DAG)。ready 即派 / 完成即派 / 并发 2。PRD 缺调度图 → 退回 planning 补, 不在 exec 问。

## 步骤 5 · check (委托 `skein-check`)

- 派 `skein-checker` 验证 (lint / type-check / tests / 契约合规)。
- 未过 → 派合适 agent (无则 `skein-executor`) 定点修复重检, 不跳 finish。

## 步骤 6 · finish (main 同步)

check 通过 →

- **journal** — finish 前 main 用 `skein.py journal --add "<本 task 做了什么>"` 追加过程记录 (append-only, 无审批门, 随 task 归档; 区别于 sediment 的过审规则)。
- **sediment 判定门** — 按 `skein-memory` 的 checklist 逐项输出 trace, 判本 task learning → core/recall/drop。触发 → 走 sediment 提案 (审批后写盘) 再 finish; 全否 → 跳过 (仍输出全 trace)。
- **清理** — `TaskList` 查残留 subagent / 后台任务, `TaskStop` 关闭。禁 `sleep` 轮询等后台跑完。
- `skein.py finish <id>` — 自动 commit worktree → merge --no-ff 回主 → archive → 销 worktree。冲突 → 自动 abort + 报冲突文件, 停, 转手动解, 禁强解 / 禁当成功。
- 更新看板 (status=completed)。
