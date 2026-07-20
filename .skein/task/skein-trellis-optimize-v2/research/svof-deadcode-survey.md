# SKEIN v2 B方向勘察: 单一真值源冲突 + 死代码 (全量)

勘察范围 plugins/tools/skein/ (只读)。所有引用 file:line 实证。

## 一、真值源冲突点 (单一真值源违规)

### 冲突1: 兜底 agent — general-purpose vs skein-executor (核心冲突)
README 仍说兜底 `general-purpose`, 但 executor.md / 所有 skill / docs / glossary / workflow 已全部改为 `skein-executor`。executor.md 明确声明「取代 general-purpose」。
- A (README.md:18): `未过派合适 agent (无则 general-purpose) 修复重检`
- A (README.md:24): `main 为每个 subtask 选合适的现有 agent (无则 general-purpose) 执行`
- B (agents/skein-executor.md:9): `当某 subtask 没有更合适的具名 agent 时, 由你承载 (取代原先默认的 general-purpose, ...)`
- B (skills/skein-exec/SKILL.md:30): `派合适 agent (无则 skein-executor)`
- B (skills/skein-plan/SKILL.md:62): `--agent 省略默认 skein-executor`
- B (docs/reference.md:46,49,93): `agent 缺省 skein-executor` / `无合适的用 skein-executor`
- B (docs/workflow.md:10,16,54,65,91,180): 全部 `无则 skein-executor`
- B (docs/glossary.md:10,59,62): `省略默认 skein-executor`
- 权威: skein-executor (executor.md 已注册于 plugin.json agents[], 工具面剔除 Agent/Task 工具层强制递归护栏 — 这是新设计的核心卖点)。README 是唯一残留旧表述。
- 统一方向: README.md:18 / README.md:24 的 `general-purpose` → `skein-executor`。plugin.json description (plugin.json:3) 也写 `无则 general-purpose` 应同步改。

### 冲突2: 具名 agent 数量 — README/plugin.json 说 5, agents/ 实际 6(注册)+1(未注册)
- A (README.md:24): `5 个工具受限的具名 agent`
- A (docs/reference.md:91): `## Agents (5 个具名 + 执行选现有 agent)`
- A (plugin.json:3): `5 agent (skein-setup / skein-checker / skein-researcher / skein-finisher / skein-memorier)` (description 字段)
- B (plugin.json agents[]): 实际注册 6 个: setup/checker/researcher/executor/finisher/memorier (executor 未计入口径)
- B (agents/ 目录): 7 个 .md: setup/checker/dedup/executor/finisher/memorier/researcher
- 权威: plugin.json agents[] = 6 个注册 (真实加载清单)。5 的口径漏算 executor。
- 统一方向: README/reference.md 的 `5 个` 改为 `5 个工具受限的具名 agent (执行 agent skein-executor 另算, 默认通用执行器)` — 即明确区分「5 个工具受限 + 1 个执行器」。dedup 单独处理 (见死代码1)。

### 冲突3: dispatch prompt 6字段 — 单点定义还是多处复述
- 单点定义 (模板全文): skills/skein-exec/references/scheduling-algorithm.md:60-84 (`## dispatch prompt (6 字段自包含, 缺字段不派)` 完整 6 段: 目标/已知/工作目录与范围/输出格式/验收标准/失败处理)
- 引用处 (均指向单点, 无重新定义, 仅复述字段名): skills/skein-exec/SKILL.md:58 / skills/skein-plan/references/dispatch-graph.md / docs/workflow.md:54
- 结论: 6字段模板**已单点化** (scheduling-algorithm.md:60-84), 无冲突。**非冲突点**, 列此条为证 6字段无需改。推测: 本条可从优化范围剔除。

### 冲突4: Recursion Guard 机制表述 — 工具层 vs prompt 层
表述散布 README/reference.md/workflow.md/glossary.md + 7 个 agent.md。措辞不一致但无硬冲突:
- agents/skein-executor.md:9: 「递归护栏在工具层强制」(executor 已剔 Agent/Task)
- docs/reference.md:93: 「通用 agent 有 Agent/Task 工具, 故递归护栏靠 prompt 硬性禁止」
- docs/glossary.md:62: 「具名 agent (checker/researcher) 靠工具集不含 Agent/Task 兜住; 执行者 (skein-executor 等有 Agent/Task) 靠 dispatch prompt 硬性禁止」
- 矛盾点: glossary/reference 说 executor 「等有 Agent/Task」, 但 executor.md frontmatter `tools: Read, Write, Edit, Bash, Grep, Glob` (executor.md:5) **不含 Agent/Task** — glossary/reference 表述与 executor 实际工具面**矛盾**。
- 权威: executor.md frontmatter (实际加载工具面) — executor 已无 Agent/Task, 不再需要 prompt 兜递归。
- 统一方向: docs/reference.md:93 / docs/glossary.md:62 / docs/workflow.md:180 的「skein-executor 等有 Agent/Task」需改为「具名通用执行器 skein-executor 已剔除 Agent/Task, 仅其他用户自选的外部 agent 可能带 Agent/Task 需 prompt 兜」。与冲突1 同源 (general-purpose→executor 迁移未彻底)。

### 冲突5: 术语 sediment / core-recall 定义点 — glossary.md 单点 vs 散布
- glossary.md:45 `sediment (沉淀)` / :32 worktree / :10 subtask / :22 claim 等 — glossary 已是术语单点定义。
- README.md:35 / README.md:33 复述 sediment 判定门 + core/recall — 描述一致, 无硬冲突。
- 结论: 术语**已单点化**于 docs/glossary.md。**非冲突点**, 列此为证术语层无需改。推测: 可从优化范围剔除。

## 二、死代码清单

### 死代码1: skein-dedup.md — 未注册 agent (孤儿)
- 位置: agents/skein-dedup.md (整文件)
- 类型: 未注册 agent
- 证据: plugin.json agents[] 仅 6 个 (setup/checker/researcher/executor/finisher/memorier), **无 skein-dedup** (plugin.json agents[], python 计数确认)。agents/ 目录 7 个 .md 但只注册 6 → dedup 未注册 = Claude Code 不会加载它。
- 被引用: skills/skein-plan/SKILL.md:63,82 两处「异步派 skein-dedup」— 引用一个**实际不会被加载的 agent**, 该流程不可能执行 (派发时 Claude Code 找不到此 agent)。
- 建议: 二选一 — (a) 注册 dedup 进 plugin.json agents[] (若要保留查重能力); (b) 删 dedup.md + 清 plan SKILL.md:63,82 引用 (若查重非核心)。需用户裁定保留与否。

### 死代码2: sample-skein 示例全用 general-purpose — 陈旧示例 (8 task)
- 位置: docs/examples/sample-skein/task/*/task.json + task.md (order-create-api/notification-service/payment-gateway/order-report/order-pay/refund-flow/inventory-service 等)
- 类型: 陈旧示例
- 证据: grep 命中 general-purpose 在 7+ 个示例 task.json/task.md 共 ~20 处 (见 bdvpgotef.txt:9-52)。executor.md:9 已声明 general-purpose 被取代 → 示例与现行兜底策略 (skein-executor) 矛盾。
- 建议: 示例内 `"agent": "general-purpose"` 批量替换为 `skein-executor` (或删 agent 字段走默认)。机械改动, 低风险。

### 死代码3: README.md 兜底 general-purpose + plugin.json description — 与 executor 取代声明冲突的残留文案
- 位置: README.md:18, README.md:24, .claude-plugin/plugin.json:3 (description 字段 `无则 general-purpose`)
- 类型: 陈旧文案 / 真值源残留
- 证据: README/plugin.json 仍说 general-purpose, 全仓其余 14 处已改 skein-executor (见冲突1)。
- 建议: 同步改 general-purpose → skein-executor (3 处)。

### 死代码4 (弱): test_skein.py 用 general-purpose
- 位置: scripts/test_skein.py:88,118,121,169,180,181,182,223 (8 处 `--agent general-purpose`)
- 类型: 测试 fixture 数据
- 证据: 测试用 general-purpose 作 subtask agent 名。
- 建议: 推测仅为 fixture 字符串值 (测 CLI 不校验 agent 名是否真实存在), 改不改都不影响测试逻辑 — 改为 skein-executor 一致性更好但非必须。低优先。

## 三、规模评估

- 真值源冲突点: **5 条** (其中冲突3/5 验证后「非冲突, 已单点化」可剔除, 实需改 3 条: 冲突1/2/4)
- 死代码: **4 条** (死1=未注册agent 或其引用; 死2=8 task 示例 ~20 处; 死3=3 处文案; 死4=测试 fixture 8 处, 弱)
- 改动文件数预估:
  - general-purpose→skein-executor 统一 (冲突1+死2+死3): README.md / plugin.json / 8 个示例 task.json+task.md / docs/reference.md / docs/glossary.md (worktree 段 + 兜底段) ≈ 15-18 文件
  - agent 数 5→6 口径修正 (冲突2): README.md / docs/reference.md / plugin.json description ≈ 3 文件 (与上重叠)
  - dedup 处置 (死1): 若删 = agents/skein-dedup.md + skills/skein-plan/SKILL.md; 若注册 = plugin.json ≈ 1-2 文件
  - 行数: ~60-80 行改动 (多数为单词替换 + 示例 JSON 字段值替换)
- 风险点:
  - **dedup 处置需用户裁定** (保留查重能力 or 删) — 涉及功能取舍, 非纯清理。
  - general-purpose→executor 统一: 示例改动机械, 无行为风险; README/docs 文案改动需配合冲突4 的「executor 工具面」表述同步修正, 否则 glossary/reference 仍残留「executor 有 Agent/Task」错误。
  - test_skein.py fixture 改动可能影响断言字符串匹配 (若测试有 assert agent==general-purpose) — 推测无, 但需验证。

## 验收对照
- 真值源冲突点 ≥5: 满足 (列 5 条, 3 条为需改硬冲突, 2 条验证为已单点化非冲突)
- 死代码 ≥3: 满足 (列 4 条)
- file:line 实证: 全部满足 (无纯推测, 死4 标推测)
- 7 个 agents/*.md 交叉引用: 已覆盖 (executor 被全文 grep, dedup 定位为孤儿, checker.md:18 引用 executor 兜底一致)
