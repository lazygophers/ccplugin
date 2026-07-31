# for-check — check 阶段作业手册

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 自跑全部验证 (状态切换+checkpoint+场景检查+契约+一致性, 无写权), 失败交 `skein-executor` 修。未过禁 finish。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=check` (exec 产物完成后、finish 前, 派 skein-checker 跑验证), 或 flow 全闭环内 exec 全 subtask done 自动进入。
- **状态切换归 checker 自跑** — `skein check <id>` (进行中→检查中) 由 `skein-checker` 自身工作流第一步自跑, main 只需在派发前确认 task 处于「进行中」态 (硬前置见 [state-before-action.md](state-before-action.md) 硬门 3), 不代跑该命令。
- **禁动 design.md** — design.md 写入归 planning (仅 planning 阶段 + check 失败回 planning 二次进入可写); **exec / check / finish 阶段均禁动**。check 检出方案性冲突 → 回 planning 改 design 后重派。

## 流程步骤

1. **验证 (`Agent(subagent_type="skein:skein-checker", description=..., prompt=...)`; 禁 teammate / team, 禁传 `team_name` — 形式见 [carrier-rules.md 派发调用形式](carrier-rules.md#派发调用形式-照抄-禁自由发挥))** — 传 Active task id + 工作目录 (task 的 `worktree` 字段; null=原地仓库根)。checker 自跑状态切换 + checkpoint 核对 (task+subtask 双层, 未勾项写回 `skein prd check`) + 场景自适应内置检查 + 契约逐条核对 + 一致性核查, 全流程权威定义见 `skein-checker.md` (agents/), 本文件不重复。
2. **判定 (main 保留项)** — 全绿 (含零冲突) → 放行 finish。FAIL 或**检出冲突** → 进修复循环。
3. **回 planning 重确认 (main 保留项, 复用现有 `进行中` 态)** — 通用回退流程详见 [rollback-protocol.md](rollback-protocol.md); check 修复 subtask 操作规范详见 [subtask-operations.md](subtask-operations.md) 第 4 节。check FAIL 或检出冲突, **禁改 task 状态** (依旧 `进行中`)。main 先回 planning 思维重审失败, 用 `AskUserQuestion` 或 grill 与用户确认修复方向, **禁跳过确认直接补 subtask 回 exec**。分级 (一级孤立 / 二级一致性冲突·方案性缺陷 / 三级架构) 以 [rollback-protocol.md §分级处理](rollback-protocol.md) 为准。check 阶段两条增量约束:
   - **方向确认=必经门** (含一级孤立失败): main 不得凭 checker 报原文擅自加 subtask, 必先 grill/AskUserQuestion 让用户拍板。
   - **一致性冲突一冲突一 subtask, 直到全绿且零冲突才放行**; 方案性 / 设计缺陷须回 planning 补充或重设计 design.md (二次进入才可写), 同步修 prd + 改契约, 再据新设计重拆。
4. **重验 (main 保留项)** — 修复 subtask 全 done 后重派 `Agent(subagent_type="skein:skein-checker")` 复跑 (含一致性)。未过回 planning 重确认循环。
5. **放行 (main 保留项)** — 全绿且零冲突 → 进 finish 阶段。

## 完成判据

- [ ] checker 回传 verdict=PASS (checkpoint/场景检查/契约/一致性 全绿)
- [ ] 本轮通过的验收项已回写 `- [x]` (checker 自跑 `skein prd check`)
- [ ] FAIL/冲突 均已经方向确认门 (grill/AskUserQuestion) 才补修复 subtask

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 孤立失败 (单点 lint/type/test/契约 fail) | 回 planning 重确认: grill/AskUserQuestion 敲定修复方向, 同 task `subtask add` 1 个定点修复子任务 (--deps 失败源), task 保持 `进行中` | 反复不过 → 见下「≥3 轮」路径 |
| 一致性冲突 / 根因跨 subtask | 同 task `subtask add` 多个修复子任务 (一冲突一 subtask), 逐条覆盖 | 冲突未全覆盖禁 finish |
| 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 停加子任务循环 → 按 [root-cause-protocol.md](root-cause-protocol.md) 5 维根因复盘 | 带根因回 planning 重确认定向重修; 根因超 exec (需求/设计缺陷) → 停手附根因报告转人工 |

## 延伸引用

- `skein-checker.md` (agents/) — 验证 agent 自身工作流权威定义 (状态切换/checkpoint/场景检查/契约/一致性), 本文件不重复
- [state-before-action.md](state-before-action.md) — 状态先行三环节硬门 (硬门 3 = check 级)
- [rollback-protocol.md](rollback-protocol.md) — check 未过回 planning 重确认通用回退流程
- [subtask-operations.md](subtask-operations.md) — 第 4 节: check 修复 subtask 操作规范
- [root-cause-protocol.md](root-cause-protocol.md) — 修复 ≥3 轮不收敛的 5 维根因复盘
