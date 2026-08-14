---
name: skein-plan
description: "SKEIN planning 独立入口。归一判定 (并入 vs 新建 task)、research 分流、PRD/design/contracts/subtask DAG/estimate 工件写法、grill 硬门、confirm 人审门。工件写法见 references/plan.md，拆分调度模型见 references/dag.md。skein-flow 在 $1=plan 或含 --plan 时路由到本 skill。"
user-invocable: true
argument-hint: "[任务描述/ID] [--plan]"
arguments: "[任务描述/ID]"
model: sonnet
effort: medium
---

# skein-plan — planning 独立入口

> 🔒 全局流程规则（状态机/调度/优先级等）以 skein-flow/references/ 为单一真值源。本 skill 只管 plan 阶段的工件产出与门控，状态流转/出口规则见 [skein-flow/references/flow-loop.md](../skein-flow/references/flow-loop.md#plan)。

## 输入

任务描述（自然语言）或 task ID（续规划已有 task）。

## 流程

```
1. 归一判定 → 并入现有 task 还是新建
2. research 分流 → 需调研则建 --phase research subtask + skein task research
3. 工件写法 → 见 references/plan.md (PRD 七段 / design.md / contracts / estimate)
4. DAG 拆分 → 见 references/dag.md (tracer-bullet 垂直切片 / depends_on / CPM)
5. 独立审计 → Agent(skein:skein-plan-auditor)，JSON 弱点报告作为 grill 输入
6. grill 硬门 → Skill(skein-grill)，弱点表逐条裁决补回
7. confirm 人审门 → skein task confirm --summary → AskUserQuestion → --approved
```

### 1. 归一判定

先查未完成 task，判新诉求并入现有 task 还是新建。同目标 / 同模块 / 共享改动面 / 互为前置 → **并入拆 subtask**；仅目标独立且无共享改动面才新建。判不准 → AI 自行裁定（默认归一）。

复杂度分档：direct-fix（单文件单处 ≤20 行）不建 task；跨 ≥2 文件、多步、外部调研、文档交付一律建 task。

### 2. research 分流

需要调研时，先登记 `--phase research` subtask，再 `skein task research <id>`；`skein-researcher` 只读调研，结论落 `.skein/task/<id>/research/` 与 `findings.md`，全 done 后 `skein task plan <id>` 收敛回 pending。

### 3. 工件写法

**PRD 三段**（`skein task confirm` 硬校验）：`目标` / `边界` / `验收标准`。占位 `- [ ] TODO` 留一条即被拒。

**design.md**：架构、数据流、取舍、技术选型、测试接缝（必填实）、可能性分支（标触发条件）。

**contracts**：brainstorm / grill 得到的不变量逐条落盘。

**estimate**：先拆 subtask 再逐个估，task 工时 ≥ Σ subtask。🔒 纯 AI 估，禁问用户。

**完整工件写法规范见 [references/plan.md](references/plan.md)。**

### 4. DAG 拆分

tracer-bullet 垂直切片，每个 subtask 切穿所有层（schema→API→UI→tests），声明 `--deps` 阻塞边。协议先行后并行：共享契约抽成前置 subtask。

**完整拆分模型 / ready 判定 / 排序 / 双池模型见 [references/dag.md](references/dag.md)。**

### 5. 独立审计

DAG 与 estimate 就绪后，派 `Agent(subagent_type='skein:skein-plan-auditor')`，传 `{"tid":"<tid>","workdir":"<绝对工作目录>","worktree":"on | off","repo":"<目标 repo 或 null>","action":"审计全部 plan 产物"}`。将返回的 JSON 弱点报告交给 grill；audit 只读、非门控，失败时记录工具失败并继续 grill。

### 6. grill 硬门（STOP）

planning 产物产出并完成独立审计后、`skein task confirm` 前必跑 grill。把 audit findings 纳入弱点表，按 skein-grill 审查轴逐条逼问，交用户裁决。有未裁决弱点禁 confirm。

### 7. confirm 人审门

```
summary = skein task confirm <tid> --summary
answer = AskUserQuestion(question=summary, options=["批准（仅规划，不执行）", "有修改意见"])
if answer != '批准（仅规划，不执行）':
    goto 1 (分析失败原因, 重新规划)
else:
    skein task confirm <tid> --approved
```

confirm 后 **stop** — 不续 exec。续执行归 skein-flow。

🔒 **选项文案禁写「同意并执行」**：skein-plan 是 planning 独立入口，confirm 门批准后固定停在此处，不续 exec —— 选项若含「执行」二字会让用户误以为批准即自动跑起来，跟本节最后一句「confirm 后 stop」自相矛盾。要续执行的场景走 skein-flow（其 confirm 门文案见 [flow-loop.md](../skein-flow/references/flow-loop.md#plan)）。

## CLI 签名速查

| 命令 | 易错点 |
| --- | --- |
| `skein task create <tid> --name <str> --desc <str> [--priority urgent\|high\|normal\|low] [--estimate <小时>]` | `--priority` 只收四个英文值；`--estimate` 单位是小时 |
| `skein subtask add <tid> <sid> --name <str> --desc <str> --estimate <小时> [--deps sid1,sid2] [--skills] [--check] [--phase exec\|research]` | `<sid>` 是位置参数不是 `--id`；四必填缺一即拒 |
| `skein prd write <tid> --type <段名> --list <条目>` | 段名 `goal\|scope\|stories\|acceptance\|verification\|testing`；`--type`/`--list` 可成对重复，一回合写多章 |
| `skein contract <id> --add "契约文本"` | 不变量逐条落盘 |

多条 skein 可以串接，但**串写命令看回显**：中途失败时后续命令照跑，回显里哪条挂了就重跑哪条（落盘状态即真值，不必预先拆）。

## 周期 / 无人值守场景

- **别每轮从零 planning**：先 `skein list --status all --json` 找上一轮同 intent 的 task，用 `skein task create <新tid> --like <上一轮tid>` 克隆骨架。
- **别拿 `--approved` 冒充人审**：无人值守走 `skein task confirm <tid> --unattended`（需用户预先授权）。

## ✅ 正向配方

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| 相关工作 | 归一拆 subtask (❌ 另开多 task 丢上下文一致性) |
| estimate | 先拆 subtask 再逐个估 (❌ 整体拍脑袋 / 问用户) |
| grill | confirm 前必跑，弱点表全裁决 (❌ 跳 grill 直接 confirm) |
| confirm | `--summary` 给用户审 → 明确批准 → `--approved` (❌ 裸 confirm 冒充过门) |
| 工件占位 | 全部替换为真实内容 (❌ 留 TODO 占位 → confirm 硬拒) |
