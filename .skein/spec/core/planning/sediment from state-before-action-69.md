---
title: 状态先行铁律 (state-before-action) — 三环节硬门·STOP + 单源重述范式
layer: core
category: planning
keywords: [state-before-action,状态先行,硬门,STOP,task,subtask,check,自降级,claim,单一真值源,cross-ref,回链,skein-flow]
source: sediment from state-before-action
authored-by: skein-spec
created: 1785061733
status: active
related: [sediment from skein-flow-align-64,sediment from skein-flow-align-65,sediment from skein-flow-align-68,reconstruct-47,hook-prompt-judge-ai-only-57]
updated: 1785061733
---

## 铁律

- MUST：状态先行铁律 = main 操作 task / subtask / check 之前必须先把对应状态机走对，任一违反 = 流程错误 (非优化空间、非效率取舍)，回退到对应状态命令后再继续
- MUST：三环节同构硬门·STOP，统一格式 `🛑 <级>: 未 <状态命令> 禁 <动作> (硬门·STOP) ... 违反 → 回退先 <状态命令>`：
  - **task 级**：未 `skein confirm` + `skein start` 禁进 exec (待处理/就绪态 task 禁派 subtask、禁跑 exec)
  - **subtask 级**：未 `skein claim` / `skein subtask start` 占 `max_parallel` 槽禁派 agent (pending/failed 态 subtask 禁直接派)
  - **check 级**：未 `skein check` 进检查中态禁跑验证/lint/test/契约核对当 check 结果 (验证归 `skein-checker`)
- MUST：禁自降级 — 文案禁留「简单的可直接」「省一步」「状态机差不多对」类口子；任何"操作前状态机走对"的硬门 MUST 显式 deny 自降级措辞 (引 memory `skein-hook-no-self-downgrade`)
- MUST：核心铁律落地范式 = **单一真值源 (主入口 skill 顶部统一段) + 处处重述带 cross-ref 回链**，禁分散重复各写一份无主源 (状态先行铁律主源在 `skein-flow` SKILL.md 顶部，`skein-exec` / `skein-check` 各重述本环节并带「同 skein-flow 顶部状态先行铁律 X 环节」回链)

## 反例表

| 禁 | 改为 |
|---|---|
| main 待处理/就绪态 task 直接派 subtask | 先 `skein confirm` + `skein start` 进进行中再派 |
| subagent 派发前未 `claim` 占槽 (pending 直派) | 先 `skein claim` / `skein subtask start` 标 running 占槽再 dispatch |
| 全 subtask done 后 main 自跑 lint/test 当 check 结果 | 先 `skein check` 进检查中态，派 `skein-checker` 跑验证 |
| 硬门文案留「简单的可直接」类口子 | 显式 deny 自降级 (引 memory `skein-hook-no-self-downgrade`) |
| 三处 skill 各写一份状态机铁律无主源 | 单一真值源在 skein-flow 顶部 + 处处重述带 cross-ref 回链 |
| 违反 = 优化空间 / 效率取舍 | 违反 = 流程错误，回退到状态命令再继续 |

## 触发场景

- main 在 task/subtask/check 任一环节前跳过状态机直接执行 (主要症状: "先执行后改态")
- skill 文案设计硬门时 (统一 STOP 格式 + 显式 deny 自降级)
- 核心铁律跨多 skill 落地 (单一真值源 + cross-ref 回链范式)

## 落地范式

**三段同构硬门·STOP 文案格式** (本铁律的可复用骨架):

```
🛑 <级>: 未 <状态命令> 禁 <动作> (硬门·STOP) — <前置状态机步骤>。违反 → 回退: 先 <状态命令> 再继续。
```

**单一真值源 + cross-ref 回链** (跨 skill 铁律的组织范式):

- 主入口 skill (如 `skein-flow`) 顶部段定义铁律全貌 (本例三环节)
- 各分 skill (`skein-exec` / `skein-check`) 重述本环节相关条 + 显式回链 `(同 skein-flow 顶部「<铁律名>」<环节>)`
- 禁各 skill 自写一份无主源 (漂移 / 不一致)

**禁自降级显式 deny** (防 AI 自降级绕 flow):

- 硬门段末加独立行: `🔒 本铁律禁自降级 — 无"简单的可直接"口子`
- 引用 memory `skein-hook-no-self-downgrade` 作为依据
- 文案硬，禁留修饰词后缀

## 案例

- commit `07ad7a600` skein(state-before-action): flow 顶部 + exec/check 重述三段同构硬门 + 显式 deny 口子，堵 main 绕状态机
- 代码证据: plugins/tools/skein/skills/skein-flow/SKILL.md:16-24 (主源), skein-exec/SKILL.md:34 (重述), skein-check/SKILL.md:17 (重述)

## 关联

- 铁律: task 状态流转规则（单 task 全 done → check）(core/planning/sediment from skein-flow-align-64.md) — 五态机底层
- 铁律: skein 工作流连线 (core/planning/sediment from skein-flow-align-68.md) — 状态转移路径
- 铁律: skein-check 两步法 (core/planning/sediment from skein-flow-align-65.md) — check 状态先行的具体承载
- 铁律: 并写竞态禁止 (core/arch/reconstruct-47.md) — 互补，本铁律是操作前状态门，reconstruct-47 是并行批次写竞态
- recall: hook 判定防自降级护栏 (recall/planning/hook-prompt-judge-ai-only-57.md) — 同源防自降级范式
- memory: skein-hook-no-self-downgrade (禁泛化「简单的直接做」)
