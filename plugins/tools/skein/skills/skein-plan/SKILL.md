---
name: skein-plan
description: "SKEIN planning 独立入口。第一步建 task、分析并填 TaskSpec (task spec)、research 分流与调度、subtask DAG 拆分、confirm 人审门。工件写法见 references/plan.md，拆分调度模型见 references/dag.md。skein-flow 在 $1=plan 或含 --plan 时路由到本 skill。"
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

## 流程（五步，一步不破窗）

1. 创建 task → **第一步必须是建 task**，先归一判定 `Bash("skein list --status unfinished --json")`，新建即 `Bash("skein task create <tid> --name <标题> --desc <描述>")`
2. 任务分析 → 填 TaskSpec 四要素 `Bash("skein task spec <tid> --desc <str> --should <a;b> --not <a;b> --acceptance <a;b>")` + design 接缝 `Bash("skein design seam <tid> --list '接缝一\n接缝二'")`
3. research 分流 → 需调研则 `Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时> --phase research")` + `Bash("skein task research <tid>")` + 调度
4. 拆 subtask → 逐个 `Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时> --deps <sid,...>")` 填齐必要信息 + 自下而上估工时 `Bash("skein task estimate <tid> --set <小时>")`
5. 人审门 → 先回显 `Bash("skein task spec <tid>")` + `Bash("skein design read <tid>")` + `Bash("skein subtask list <tid>")`，AskUserQuestion 批准后 `Bash("skein task confirm <tid> --approved")`

**会话纪律**：第 1 步到第 5 步一个不破窗完成（中途禁 `/clear` / `/compact`）；research 全量结论走 `findings.md` 落盘，主对话只引摘要，不引全文。

### 1. 创建 task（第一步）

**归一判定**：先查未完成 task，判新诉求并入现有 task 还是新建。同目标 / 同模块 / 共享改动面 / 互为前置 → **并入拆 subtask**（转到该 task 的第 2 步）；仅目标独立且无共享改动面才新建。

复杂度分档：direct-fix（单文件单处 ≤20 行）不建 task；跨 ≥2 文件、多步、外部调研、文档交付一律建 task。

```
Bash("skein list --status unfinished --json")
Bash("skein task create order-create-api --name '下单接口' --desc '为 C 端新增下单 API' --priority normal")
```

### 2. 任务分析，填写 task 信息

分析代码改动面后，把结论写进 TaskSpec（desc / boundary / acceptance，落盘 prd.md frontmatter）与 design.md 测试接缝。含糊 / 多读法先 `AskUserQuestion` 逼用户拍板 —— 每问附推荐答案，决策归用户、事实归 AI 自查（查得到的不问）。

```
Bash("skein task spec order-create-api --desc '新增 POST /orders 下单接口, 直连 DB 单商品直购' --should 'API 层+DB 迁移+单测;入参校验' --not '不动支付回调;不做购物车;不改老订单接口' --acceptance 'POST /orders 正常单返回 201;非法参数返回 400;单测全绿'")
Bash("skein design seam order-create-api --list 'API 层响应契约\nDB 迁移可回滚'")
```

只读回显：`Bash("skein task spec order-create-api")`（不带参数即读）。工件写法规范见 [references/plan.md](references/plan.md)。

### 3. research 分流（需要时）

需要调研时：先登记 research subtask、切调研态，然后调度 `skein-researcher` 执行。调研结论落 `.skein/task/<tid>/research/` 与 `findings.md`，全 done 后收敛回 pending（命令见下方代码块）。

```
Bash("skein subtask add order-create-api r1-lock --name '库存锁方案调研' --desc '对比乐观/悲观锁在秒杀场景的正确性, 结论写 findings.md' --estimate 2 --phase research")
Bash("skein task research order-create-api")
```

调度：派 `Agent(subagent_type='skein:skein-researcher')`，传 `{"tid":"order-create-api","workdir":"<绝对工作目录>","topic":"<调研主题>"}`。全部 research subtask done 后：

```
Bash("skein task plan order-create-api")
```

**可行性探针**：设计问题纸面定不了（状态模型手感 / 契约是否成立 / UI 形态）→ 先跑最小 throwaway 探针验证，探针代码即弃、不进正式 DAG、不并入交付物；结论回写 design.md（标「已探针验证」），再继续拆分。

### 4. 拆 subtask，逐个填必要信息

tracer-bullet 垂直切片，每个 subtask 切穿所有层（schema→API→UI→tests），声明 `--deps` 阻塞边。协议先行后并行：共享契约抽成前置 subtask。完整拆分模型 / ready 判定 / 双池模型见 [references/dag.md](references/dag.md)。

每个 subtask 必填：sid / name / desc / estimate（缺一即拒）。desc 必须锚定 design.md 接缝（如「按 design.md 测试接缝节的 seam」），保证 executor 自读 `Bash("skein subtask show <tid> <sid>")` 即可独立执行，不回读全局猜上下文。

```
Bash("skein subtask add order-create-api s1-schema --name 'orders 表迁移' --desc '按 design.md 测试接缝节的「DB 迁移可回滚」, 建 orders 表 + 回滚脚本' --estimate 2 --check '迁移可 up/down'")
Bash("skein subtask add order-create-api s2-api --name 'POST /orders 接口' --desc '按 design.md 测试接缝节的「API 层响应契约」, 依赖 s1 的 orders 表' --estimate 4 --deps s1-schema --check '201/400 契约单测全绿'")
Bash("skein subtask add order-create-api s3-e2e --name '端到端验证' --desc '串 s1+s2 跑完整下单流, 按 acceptance 逐条核对' --estimate 1 --deps s1-schema,s2-api")
```

subtask 拆完后自下而上估 task 工时（= Σ subtask + plan/check 开销，**纯 AI 估禁问用户**，铁律见 [references/plan.md](references/plan.md#预计工时硬门-estimate)）：

```
Bash("skein task estimate order-create-api --set 9")
```

产出后跑质量自检：派 `Agent(subagent_type='skein:skein-plan-auditor')`（只读审计，非门控）→ 弱点报告交 grill 逐条裁决。有未裁决弱点禁进第 5 步。

### 5. 人审门（AskUserQuestion）

**先回显产物再问**。按顺序跑下面三条命令，把输出拼进提问内容（spec 信息 + 设计信息 + subtask 编排结果）：

```
Bash("skein task spec order-create-api")
Bash("skein design read order-create-api")
Bash("skein subtask list order-create-api")
```

然后：

```
answer = AskUserQuestion(question=<上述三条命令输出 + 工时/优先级>, options=["批准（仅规划，不执行）", "有修改意见"])
if answer != '批准（仅规划，不执行）':
    goto 2 (按意见改 spec/design/subtask, 重新过人审)
else:
    Bash("skein task confirm order-create-api --approved")
    plan 结束, stop — 不续 exec, 续执行归 skein-flow
```

🔒 **选项文案禁写「同意并执行」**：skein-plan 是 planning 独立入口，confirm 门批准后固定停在此处，不续 exec。要续执行走 skein-flow（其 confirm 门文案见 [flow-loop.md](../skein-flow/references/flow-loop.md#plan)）。

## CLI 签名速查

| 命令 | 易错点 |
| --- | --- |
| `Bash("skein task create <tid> --name <str> --desc <str> [--deps tid1,tid2] [--repos repo1,repo2] [--priority urgent\|high\|normal\|low] [--estimate <小时>] [--like <模板tid>]")` | `<tid>` 是位置参数；`--name`/`--desc` 必填；`--priority` 只收四个英文值；`--estimate` 单位是小时；`--deps` 声明前置 task；`--like` 克隆既有 task 的 spec/design/subtask 骨架，状态全重置 |
| `Bash("skein task spec <tid> [--desc <str>] [--should <a;b;c>] [--not <a;b;c>] [--acceptance <a;b;c>]")` | TaskSpec 落盘 prd.md frontmatter；列表 `;` 分号分隔；不带参数 = 只读回显；confirm 后锁定 |
| `Bash("skein subtask add <tid> <sid> --name <str> --desc <str> --estimate <小时> [--deps sid1,sid2] [--check <a;b>] [--phase exec\|research]")` | `<sid>` 是位置参数不是 `--id`；四必填缺一即拒 |
| `Bash("skein design seam <tid> --list <条目>")` / `Bash("skein design read <tid>")` | seam `--list` 用 `\n` 分隔多条，整段清重建；read 只读回显 |

多条 skein 可以串接，但**串写命令看回显**：中途失败时后续命令照跑，回显里哪条挂了就重跑哪条（落盘状态即真值，不必预先拆）。

## 周期 / 无人值守场景

- **别每轮从零 planning**：先 `Bash("skein list --status all --json")` 找上一轮同 intent 的 task，用 `Bash("skein task create <新tid> --like <上一轮tid> --name <标题> --desc <描述>")` 克隆骨架。
- **别拿 `--approved` 冒充人审**：无人值守走 `Bash("skein task confirm <tid> --unattended")`（需用户预先授权）。

## ✅ 正向配方

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| 第一步 | 先建 task 再分析填信息 (❌ 先长篇分析后补 task) |
| 相关工作 | 归一拆 subtask (❌ 另开多 task 丢上下文一致性) |
| estimate | 先拆 subtask 再逐个估 (❌ 整体拍脑袋 / 问用户) |
| 人审 | 先回显 spec+design+subtask 再 AskUserQuestion (❌ 裸 confirm / 无产物就问) |
| 工件占位 | 全部替换为真实内容 (❌ 留 TODO 占位 → confirm 硬拒) |
