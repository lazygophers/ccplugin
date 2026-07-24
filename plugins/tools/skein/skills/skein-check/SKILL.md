---
name: skein-check
description: task check 阶段质量验证。exec 产物完成后、finish 前使用。派 skein-checker 跑 lint/type-check/tests/契约 + 一致性核查, 回传通过|失败|冲突报告。未过或检出冲突不放行 finish。验证与修复分离。
user-invocable: true
argument-hint: "[任务ID]"
arguments: "[任务ID]"
model: haiku
effort: medium
---

# skein-check — 质量验证门

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent (无则 `skein-executor`) 修。未过禁 finish。

**禁动 design.md** — design.md 写入归 planning (仅 planning 阶段 + check 失败回 planning 二次进入可写); **exec / check / finish 阶段均禁动**。check 检出方案性冲突 → 回 planning 改 design 后重派, 禁 check 阶段就地改 design。

## 载体

> **工作目录 (worktree 态自适应)** — 本仓 worktree 隔离启用态: !`skein config --json 2>/dev/null | jq -r '.use_worktree' || echo unknown`。`true`=在 **task worktree** 内验证/修复; `false`/`unknown`=**原地在仓库根**。真值以 task 的 `worktree` 字段为准 (null=原地)。下文"task worktree"按此二读。

- **验证** → 派 `skein-checker` (只读 + 跑命令, 回传 PASS/FAIL 报告)。
- **修复** → 派合适 agent (按修复性质挑现有 agent, 无则 `skein-executor`) 在该 task 工作目录 (worktree 或原地仓库根) 内定点改 (dispatch prompt 带执行纪律)。
- main 作调度器串起「验证 → 修复 → 重验」循环, 不亲跑 check、不亲改码。

## 流程

1. **验证** — 派 `skein-checker`: 传 Active task id + 工作目录 (task 的 `worktree` 字段; null=原地仓库根)。checker 分两步: **① checkpoint 核对 → ② 场景自适应内置 check**, 回传报告。
   - **① checkpoint 核对 (task + subtask 双层)** — checker 核对本 task 全部 checkpoint 是否完成:
     - **task 级** — 自跑 `skein prd read <id> --type=acceptance` 取 prd `## 验收标准` (禁 dispatch prompt 传验收全文, 避免上下文漂移 + 省 token), **只验未勾 (`- [ ]`) 项**; 已 `- [x]` 项视为上轮已过, 跳过不重复验。
     - **subtask 级** — 逐个 subtask 核对其 planning 登记的 `--check` 验收 checklist (`skein subtask list <id>` 出各 subtask 验收项)。全过 → checkpoint 满足 (勾验收/标记完成归 step 2 判定回写)。这是 exec **不做**、由 check 统一做的验收 (点1↔点3 对接: exec 只 `done`, check 才勾验收)。
   - **② 场景自适应内置 check** — checker 按项目场景自判跑对应内置检查 (无固定字段, 探测项目特征选; 多特征并存跑命中的多类):
     - **编程类** (有 build/test 配置) — build 能过 / test 能跑通 / lint / type-check / **架构一致性** (接口签名/职责/命名/数据流) + 契约合规。
     - **小说 / 内容类** (有 章节/大纲 目录) — **逻辑一致性** (情节因果不断裂) + 设定一致性 (人物/世界观不自相矛盾) + 伏笔呼应。
     - **数据 / ETL 类** (有 pipeline/迁移脚本/schema) — schema 校验 / 数据管道跑通 / 字段一致性 / 样本抽检。
     - **文档 / 知识类** (以 md/文档为主交付) — 链接有效性 / 结构完整 / 术语一致 / 交叉引用不断裂。
     - **配置 / 基建类** (有 IaC/CI/容器/配置清单) — 配置语法校验 / 幂等性 / dry-run 通过 / 依赖版本锁一致。
     - **设计 / 前端类** (有 组件/样式/前端栈) — 组件渲染 / 可访问性 / 视觉回归 / 响应式断点。
     - 无识别场景 → 该项标 `[工具失败: 未识别项目场景]`, 列已尝试。
   - **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail:
     - `skein contract <id>` (列出 planning 阶段锁进 task.json 的契约)
     - 任一条 fail → 进修复循环 (同 lint/type/test 未过路径), 派合适 agent (无则 `skein-executor`) 定点修复后重检。
   - **一致性核查** — checker MUST 检 subtask 产物间 + 与 prd 契约有无冲突: 接口签名对不上 / 重复实现同一职责 / 命名与约定相斥 / 数据流断裂 / 契约互相矛盾。逐条报冲突对 (哪两处 file:line + 冲突点)。
2. **判定** — 全绿 (含零冲突) → 放行 finish。FAIL 或**检出冲突** → 进修复循环 (见下)。**本轮验证通过的验收项** (含部分通过场景), main 经 `skein prd check <id> --type=acceptance --list "<验收项文本>"` 回写勾选态持久化 (脚本写盘, 禁裸 Edit prd.md; 载体是 main 非 checker), 未过项保持 `- [ ]` 留待修复后重验。需反勾 (修复后回退) 用 `skein prd uncheck`。
3. **回 planning 重确认 (非新枚举, 复用现有 `进行中` 态)** — check FAIL 或检出冲突, **禁改 task 状态** (依旧 `进行中`/`S_ACTIVE`, 不建新 task; 「回 planning」是**思维回炉语义**, 非状态机新枚举)。main **先回 planning 思维重审失败**: 重新审视 checker 报告的失败原因 (lint/type/test/契约 fail / 一致性冲突), 用 `AskUserQuestion` 或 grill 与用户**确认修复方向是否对** (是定点修一处 / 还是方向错了需重拆 / 还是契约本身要改), **禁跳过确认直接补 subtask 回 exec**。确认方向后, **按错误性质分档补设计/工件, 再回 exec** (--deps 挂失败源), 回 exec 重新 `claim` 派发。**确认无误后才继续进入 exec 执行**:
   - **孤立失败** (单点 lint/type/test/契约 fail) → 确认后加 1 个定点修复 subtask: `skein subtask add <tid> <fix-sid> --name "修复: <失败点>" --desc "<报错原文 / file:line>" --agent <合适> --deps <失败 subtask sid>` (只改失败相关文件, 设计无需动)。
   - **一致性冲突 / 根因跨 subtask** → 确认后按冲突根因加**多个**修复 subtask (一冲突一 subtask, 逐条覆盖, `--deps` 挂对应源 subtask, 必要时同步更新契约)。**直到全绿且零冲突才放行** — 未覆盖完所有冲突禁 finish。
   - **方案性 / 设计缺陷** (错误根因在设计本身: 架构选型不对 / 契约定义有误 / 需求边界漏了) → 回 planning **补充或重设计 design.md** (check 失败回 planning 二次进入才可写 design.md), 同步用 `skein prd write/add` 修 prd 目标/边界/验收 + `skein contract <id> --add` 补/改契约, 再据新设计 `subtask add` 重拆或补子任务。**新方案经 grill/AskUserQuestion 确认无误, 才回 exec 执行** (禁未确认就补 subtask)。
   - 方向确认=必经门: main 不得凭报原文擅自加 subtask, 必先 grill/AskUserQuestion 让用户对修复方向拍板; 用户认可方向后才 `subtask add`。新增修复 subtask `depends_on` 失败源 subtask (已 done) → 立即 ready, exec `claim` 即派; task 全程 `进行中`, 修复进度落在同 task 看板 DAG。
4. **重验** — 修复 subtask 全 done 后重派 `skein-checker` 复跑 (含一致性)。未过回 planning 重确认循环 (task 始终 `进行中`)。
5. **放行** — 全绿且零冲突 → 回 `skein-flow` 走 finish。

**完成判据 (放行 finish 前勾满)**:
- [ ] checkpoint 核对: task 验收标准 + 各 subtask `--check` 项全完成 (标记完成)
- [ ] 场景内置 check 全绿 (按项目自适应: 编程/小说/数据ETL/文档知识/配置基建/设计前端, 命中类全过)
- [ ] 契约逐条 pass (`skein contract` 全覆盖, 无遗漏)
- [ ] 一致性核查零冲突
- [ ] 本轮通过的验收项已回写 `- [x]`

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                     | 一线修复                                     | 仍失败兜底                                                       |
| ------------------------ | -------------------------------------------- | --------------------------------------------------------------- |
| 孤立失败 (单点 lint/type/test/契约 fail) | 回 planning 重确认: main 重新 grill/AskUserQuestion 与用户敲定修复方向, 确认后同 task `subtask add` 1 个定点修复子任务 (--deps 失败源), task 保持 `进行中`, 回 exec 重新 claim 派发 | 反复不过 → 见下「≥3 轮」路径                                   |
| 一致性冲突 / 根因跨 subtask | 回 planning 重确认后, 同 task `subtask add` 多个修复子任务 (一冲突一 subtask), task 保持 `进行中`, 回 exec 逐条覆盖 | 冲突未全覆盖禁 finish, 逐条覆盖到零冲突才放行                   |
| 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 停加子任务循环 → 按 [references/root-cause-protocol.md](references/root-cause-protocol.md) 5 维根因复盘 | 带根因回 planning 重确认 (grill 方向) 定向重修; 根因超 exec (需求/设计缺陷) → 停手附根因报告转人工 |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: 全绿且零冲突才放行 finish; check 失败走 step 3 回 planning 重确认。

| 场景             | 正确做法 (❌ 反面)                                                              |
| ---------------- | ------------------------------------------------------------------------------ |
| 跑验证           | 派 `skein-checker` (❌ main 亲跑 lint/test)                                     |
| checker 报失败   | 交合适修复 agent 定点改 (❌ checker 自改码)                                     |
| 放行 finish      | 全绿 + 契约逐条 pass + 零冲突 (❌ 未全绿 / 只 lint 不验契约)                     |
| check 失败       | 走 step 3: grill 敲定方向 → 同 task `subtask add`, task 保持 `进行中` (❌ 跳确认补 subtask / 改状态 / 另建 task) |
| 冲突处理         | 逐条 `subtask add` 覆盖到零冲突 (❌ 未覆盖完就 finish)                          |
| 已 `- [x]` 项    | 跳过不重验 (❌ 重复验证)                                                        |
| 通过的验收项     | 回写 `- [x]` (❌ 不回写致下轮重验)                                              |
| 反复失败         | 第 3 轮走根因复盘 (❌ 无限重检)                                                 |
