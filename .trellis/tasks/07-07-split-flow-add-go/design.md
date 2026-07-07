# Design — 拆分 trellisx-flow 为 add/flow + go

## 1. 架构边界

```
用户 /trellisx-add <描述>        → add skill (阻塞) → 判新旧+create+planning → 停 (task=planning 态)
用户 /trellisx-flow <描述>       → flow skill → [调 add --continue 借 planning] → start→exec→check→finish
用户 /go                         → go command → 枚举所有 planning 态 task → task 级 DAG 滚动执行闭环
model 自动 (复杂/多步/跨文件)     → flow skill (双模) → 同上全闭环
```

**单一真值源**: planning 逻辑 (判新旧 + `task.py create` + brainstorm/grill 硬门1 + 写 prd/design/implement) **只在 add SKILL.md 正文**。flow 与 go 均不复制, 运行时委托 add。

## 2. add 参数契约 (D-3/D-4 落地)

| 调用 | 参数 | 行为 |
|---|---|---|
| 用户 `/trellisx-add <描述>` | 无 | 跑完 planning **即停** (阻塞), task 留 planning 态, 交还控制权 |
| flow 内部委托 | `--continue` (别名 `--exec`) | 跑完 planning **不停**, 返回 planning 产物路径, 由 flow 续 exec |

- 「阻塞/不阻塞」是 **add 入口层行为开关**, 不写进 planning 逻辑本体 → planning 逻辑对两条路径完全一致 (真复用)。
- 参数解析复用 flow 现有前置选项解析风格 (选项在描述前, 中文别名可接: `继续`/`执行`=`--continue`)。

## 3. flow 改造 (P3)

- 现 step2 planning 段 (L73-76 约 4 行 + 硬门措辞) → 替换为:
  > 「planning: 调 `/trellisx-add --continue <描述>` 完成 判新旧+登记+规划 (含 grill 硬门1, 见 add skill); add 返回 planning 产物后, flow 接续 step3 激活。」
- 保留: 载体铁律 / 入参 (worktree/workflow) / step3-6 (激活/exec/check/finish) / 硬规 / 反例黑名单。
- 保名 `trellisx-flow` → 交叉引用 (orchestrate/spec/cleanup/guard) 不动。
- 触发描述保持双模 (SKILL.md:3,4,56 不改), 反而据此修 docs。

## 4. go command 设计 (P2/D-5/D-6)

- frontmatter: `name: go`, `description` 前置触发词 (「go」「执行 pending」「跑规划好的 task」), `argument-hint`。
- 逻辑:
  1. `task.py list` 枚举所有 **planning 态** (已 create 未 start) task = pending 集。
  2. 空集 → 提示「无待执行 task, 先 /trellisx-add」, 退出。
  3. 非空 → 按 task 级 DAG 调度 (复用 orchestrate `scheduling.md` §2 冲突判定 + L47-52 多 task 并发): write-files/exec-scope 相交→串行, 不相交→并行, **task 级并发上限 2 滚动** (完成一个 start 下一个)。
  4. 每 task 走 flow 的 start→exec→check→finish 载体铁律 (worktree 隔离 / subagent 编排)。
- go **不做 planning** (add/go 边界清): 只消费 add 攒下的 planning 态 task。

## 5. 复用机制取舍记录 (grill)

- 用户选「flow 运行时调 add」而非「抽共享 reference」。矛盾 (add 会停) 用**参数化**化解 (§2)。
- 备选「共享 references/plan-phase.md」被否 → 若后续 add 参数分支过复杂, 可回退此方案 (design 保留退路)。

## 6. 兼容性影响面

| 文件 | 改动 | 原因 |
|---|---|---|
| `skills/trellisx-add/` (新) | 新建 SKILL.md (+按需 references) | P1 |
| `commands/go.md` (新) | 新建 | P2 |
| `skills/trellisx-flow/SKILL.md` | planning 段瘦身 | P3 |
| `.claude-plugin/plugin.json` | skills 加 add + 新增 commands 数组 | P4 |
| `skills/trellisx-grill/SKILL.md` | 硬门1 触发点 flow step2 → add planning 阶段 | P5 |
| `docs/prd.md`,`README.md`,`docs/skills-reference.md`,`docs/getting-started.md` | 修 flow 触发矛盾 + 补 add/go 条目 | P5 |

**不改**: orchestrate/spec/cleanup SKILL 实质逻辑, guard.py, scheduling.md (go 复用不改)。

## 7. 风险

| 风险 | 缓解 |
|---|---|
| add 参数分支使 planning 逻辑分叉 | 参数只控入口「停/不停」, planning 本体零分支 (§2) |
| go 与 flow exec 调度重复实现 | go 复用 scheduling.md, 不新写调度 |
| docs 与 SKILL 触发描述再次漂移 | P5 一次对齐, 验收断言 grep 双方一致 |
| claude -p 触发测试 add/flow 误抢 | description 前置差异化触发词 (add=只规划/审规划; flow=强制闭环/一步到位) |
