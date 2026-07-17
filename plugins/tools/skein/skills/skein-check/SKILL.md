---
name: skein-check
description: task check 阶段质量验证。exec 产物完成后 finish 前使用 — 派 skein-checker 跑 lint/type-check/tests/契约合规, 未过则回 planning 重确认 (main 重新 grill/AskUserQuestion 与用户确认修复方向, 非直接补 subtask 回 exec) → 确认后同 task 排队修复子任务 → 重新 claim 派发 → 通过才放行 finish。验证与修复分离; 反复不过 (第 3 轮) 做 5 维根因复盘
user-invocable: true
argument-hint: "[task_id]"
arguments: "[task_id]"
model: haiku
effort: medium
---

# skein-check — 质量验证门

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent (无则 `skein-executor`) 修。未过禁 finish。

## 载体

- **验证** → 派 `skein-checker` (只读 + 跑命令, 回传 PASS/FAIL 报告)。
- **修复** → 派合适 agent (按修复性质挑现有 agent, 无则 `skein-executor`) 在 task worktree 内定点改 (dispatch prompt 带执行纪律)。
- main 作调度器串起「验证 → 修复 → 重验」循环, 不亲跑 check、不亲改码。

## 流程

1. **验证** — 派 `skein-checker`: 传 Active task id + worktree 路径 + planning 的验收标准。checker 跑 lint/type/test/build + 契约合规 + 一致性核查, 回传报告。
   - **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail:
     - `skein contract <id>` (列出 planning 阶段锁进 task.json 的契约)
     - 任一条 fail → 进修复循环 (同 lint/type/test 未过路径), 派合适 agent (无则 `skein-executor`) 定点修复后重检。
   - **一致性核查** — checker MUST 检 subtask 产物间 + 与 prd 契约有无冲突: 接口签名对不上 / 重复实现同一职责 / 命名与约定相斥 / 数据流断裂 / 契约互相矛盾。逐条报冲突对 (哪两处 file:line + 冲突点)。
2. **判定** — 全绿 (含零冲突) → 放行 finish。FAIL 或**检出冲突** → 进修复循环 (见下)。
3. **回 planning 重确认 (非新枚举, 复用现有 `进行中` 态)** — check FAIL 或检出冲突, **禁改 task 状态** (依旧 `进行中`/`S_ACTIVE`, 不建新 task; 「回 planning」是**思维回炉语义**, 非状态机新枚举)。main **先回 planning 思维重审失败**: 重新审视 checker 报告的失败原因 (lint/type/test/契约 fail / 一致性冲突), 用 `AskUserQuestion` 或 grill 与用户**确认修复方向是否对** (是定点修一处 / 还是方向错了需重拆 / 还是契约本身要改), **禁跳过确认直接补 subtask 回 exec**。确认方向后, 在**同一 task 内 `subtask add` 排队修复子任务** (--deps 挂失败源), 回 exec 重新 `claim` 派发:
   - **孤立失败** (单点 lint/type/test/契约 fail) → 确认后加 1 个定点修复 subtask: `skein subtask add <tid> <fix-sid> --name "修复: <失败点>" --desc "<报错原文 / file:line>" --agent <合适> --deps <失败 subtask sid>` (只改失败相关文件)。
   - **一致性冲突 / 根因跨 subtask** → 确认后按冲突根因加**多个**修复 subtask (一冲突一 subtask, 逐条覆盖, `--deps` 挂对应源 subtask, 必要时同步更新契约)。**直到全绿且零冲突才放行** — 未覆盖完所有冲突禁 finish。
   - 方向确认=必经门: main 不得凭报原文擅自加 subtask, 必先 grill/AskUserQuestion 让用户对修复方向拍板; 用户认可方向后才 `subtask add`。新增修复 subtask `depends_on` 失败源 subtask (已 done) → 立即 ready, exec `claim` 即派; task 全程 `进行中`, 修复进度落在同 task 看板 DAG。
4. **重验** — 修复 subtask 全 done 后重派 `skein-checker` 复跑 (含一致性)。未过回 planning 重确认循环 (task 始终 `进行中`)。
5. **放行** — 全绿且零冲突 → 回 `skein-flow` 走 finish。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                     | 一线修复                                     | 仍失败兜底                                                       |
| ------------------------ | -------------------------------------------- | --------------------------------------------------------------- |
| 孤立失败 (单点 lint/type/test/契约 fail) | 回 planning 重确认: main 重新 grill/AskUserQuestion 与用户敲定修复方向, 确认后同 task `subtask add` 1 个定点修复子任务 (--deps 失败源), task 保持 `进行中`, 回 exec 重新 claim 派发 | 反复不过 → 见下「≥3 轮」路径                                   |
| 一致性冲突 / 根因跨 subtask | 回 planning 重确认后, 同 task `subtask add` 多个修复子任务 (一冲突一 subtask), task 保持 `进行中`, 回 exec 逐条覆盖 | 冲突未全覆盖禁 finish, 逐条覆盖到零冲突才放行                   |
| 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 停加子任务循环 → 按 [references/root-cause-protocol.md](references/root-cause-protocol.md) 5 维根因复盘 | 带根因回 planning 重确认 (grill 方向) 定向重修; 根因超 exec (需求/设计缺陷) → 停手附根因报告转人工 |

## 反例

违反上文即流程错误: main 亲跑 lint/test (应派 checker) / checker 自己改码 (应交合适修复 agent) / 未全绿就 finish / 只跑 lint 不验契约 (先 `skein contract` 逐条报) / **check 失败跳过 planning 重确认直接补 subtask 回 exec** (应先 grill/AskUserQuestion 与用户敲定修复方向, 确认后才 `subtask add`) / **check 失败改 task 状态或另建 task/加 planning 枚举** (应同 task `subtask add` 排队修复, task 保持 `进行中`, 「回 planning」是思维语义非新枚举) / 冲突未逐条 `subtask add` 覆盖就 finish / 无限重检 (第 3 轮走根因复盘)。
