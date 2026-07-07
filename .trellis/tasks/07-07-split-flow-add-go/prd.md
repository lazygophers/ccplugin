# PRD — 拆分 trellisx-flow 为 add/flow + go command

> 需求经 `/trellisx-grill` 全轮对抗校对锁定 (6 决策 + 5 交付), 用户逐项 AskUserQuestion 确认。

## 1. 目标 (一句话)

把 `trellisx-flow` 单 skill 拆成: `trellisx-add` (只规划不执行) + `trellisx-flow` (全闭环, 复用 add 的规划逻辑) + `go` command (执行所有已 pending 的规划态 task)。消除规划逻辑重复。

## 2. 背景 / 动机

- 现状: `trellisx-flow` 单 skill 强制 plan→exec→check→finish 全闭环, 用户无法「先只规划、审完再执行」。
- 诉求: 主动 `/trellisx-add` 时只做 判新旧+分析+规划 (产出 prd/design/implement), **不执行**; 执行由独立 `go` command 触发。
- 复用: flow 的「规划」部分**引用 add**, 而非复制两份正文。

## 3. 锁定决策 (grill 输出)

| # | 决策 | 结论 |
|---|---|---|
| D-1 | add 边界 | 停在 `task.py start` **之前**: 判新旧 + `task.py create` + 写 prd/design/implement, task 留 planning 态 |
| D-2 | 触发模式 | `add` **仅显式** `/trellisx-add`; `flow` 保留**双模** (显式 + 复杂/多步/跨文件自动全闭环) |
| D-3 | 复用机制 | flow **运行时调 add**; add **参数化**: 无参 = 默认阻塞 (跑完 planning 即停, 用户直呼); 有参 = 不阻塞, 返回 planning 产物 (flow 调) |
| D-4 | flow 续 exec | add 的「停」是**入口层行为** (不写进 planning 逻辑); flow 传参调 add 借完 planning, flow 自接 start→exec→check→finish |
| D-5 | go 语义 | 执行**所有 pending (planning 态) task** |
| D-6 | go 调度 | 锚既存 `flow SKILL.md` L47-52 + orchestrate `scheduling.md` 的 task 级 DAG: write-files/exec-scope 相交→串行, 不相交→并行, task 级并发上限 2 滚动执行 |

## 4. 交付物矩阵 (可验收)

| ID | 交付物 | 验收断言 |
|---|---|---|
| P1 | 新 skill `trellisx-add/SKILL.md` — planning 逻辑 (判新旧+create+prd/design/implement) + 参数化 (无参阻塞/有参不阻塞) | `test -f skills/trellisx-add/SKILL.md`; grep 参数契约 + 「不执行/停在 start 前」语义 |
| P2 | 新 command `commands/go.md` — 执行所有 pending planning task, 锚 task 级 DAG (冲突串行/不冲突并行/上限2滚动), 空态提示 | `test -f commands/go.md`; grep DAG/并发上限2/空态 |
| P3 | 改 `trellisx-flow/SKILL.md` — planning 段 (现 L73-76) 瘦身为「调 /trellisx-add <参数> + 续 exec」, 保名, 保双模触发 | grep flow planning 段指向 trellisx-add, 无重复 planning 正文 |
| P4 | 登记 — `.claude-plugin/plugin.json`: `skills` 数组加 trellisx-add, 新增 `commands` 数组含 `./commands/go.md` | `jq '.skills'` 含 add; `jq '.commands'` 含 go |
| P5 | 引用同步 — `grill/SKILL.md` 硬门1 触发点 flow step2→add planning; docs (`prd.md`/`README.md`/`skills-reference.md`) 修 flow「禁自动触发」↔ SKILL 双模矛盾 | grep grill 硬门指向 add; grep docs flow 触发描述与 SKILL 一致 |

## 5. 兼容性 / 约束

- **flow 保名**: `orchestrate:45,47` / `spec:34,41` / `cleanup:50` / `guard.py:304` 对 "trellisx-flow" 的交叉引用**存活**, 仅 grill 硬门触发点描述需改 (planning 挪进 add)。
- **既存矛盾必修**: `docs/prd.md:73` + `README:23` + `skills-reference:33` 写 flow「禁自动触发」, 与 `SKILL.md:3,4,56` 双模冲突。既裁定 flow 保留自动 → 改 docs 对齐 SKILL。
- **go 空态**: 无 pending planning task → 提示「无待执行 task, 先 /trellisx-add」, 不报错。
- **go 遵守规范**: 执行仍走 flow/workflow 载体铁律 (worktree 隔离 / subagent 编排 / 并发上限)。

## 6. 验收标准 (整体)

1. P1-P5 各断言通过。
2. CLAUDE.md 质量检查规范: `claude -p "<add/flow/go 触发场景>"` 能正确区分三者路由 (add=只规划, flow=全闭环, go=执行 pending)。
3. 无重复 planning 正文 (add 单一真值源)。
4. flow 拆分后其余 trellisx skill 交叉引用不失效。

## 7. 非目标

- 不改 orchestrate/spec/cleanup 实质逻辑 (仅 grill 硬门描述 + docs 同步)。
- 不动 go 之外的 command 体系, 不动 worktree / 载体铁律本身。
