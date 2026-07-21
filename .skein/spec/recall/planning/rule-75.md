---
title: plan 研究期可过度探索, 落地设计守 YAGNI
layer: recall
category: planning
keywords: [planning,yagni,over-design,design,exploration,landing,possibility-branch]
source: -
authored-by: skein-spec
created: 1784599483
status: active
related: []
updated: 1784599483
---

# plan 研究可发散, 落地守现状

## 铁律

planning 期分**研究探索**与**最终设计**两阶段, 过度设计只在研究期允许:

- **研究期 (findings.md / 可能性分支)** — 鼓励过度发散: 探现状之外的扩展方案 / 未来约束变化时的演进分支 / 被否决的备选, 用于**探究当前方案的合理性边界** (为何这样选 / 换个约束会怎样)。每条可能性分支**必须标触发条件** (若未来需 X / 若约束变 Y)。
- **最终设计 (design.md 正文 + task.json DAG)** — **YAGNI 照常挥**, 只写满足当前需求的最小可行设计。禁塞"以后可能要"的扩展点 / 抽象层 / 配置项进落地设计。可能性分支**不进正文、不进 DAG、不生成 subtask**。

## 陷阱 → 正解

- **陷阱**: 把过度设计的产物写进 design.md 正文或 task.json DAG → exec 期实现了一堆当前用不上的抽象, 违背 YAGNI。
  **正解**: 过度设计产物只落 design.md「可能性分支」section + findings.md, 标触发条件, 不进 DAG。
- **陷阱**: plan 期彻底不发散, 只写最小设计 → 失去对方案合理性的探究, 选了次优解而不自知。
  **正解**: 研究环节主动过度探索边界, 用可能性分支反向验证当前方案为何最优。
- **陷阱**: 可能性分支不标触发条件, 变成无依据的臆想清单。
  **正解**: 无触发条件的纯臆想按 YAGNI 砍; 有触发条件才保留留痕。

## 触发场景

- grill YAGNI 轴审到"以后可能要"的 subtask / design 正文条目 → 先问: 这是落地设计还是研究留痕? 落地→砍; 研究→移到可能性分支标触发条件。
- design.md 正文出现抽象层 / 配置项 / 扩展点但当前需求用不上 → 砍到最小可行, 理由记可能性分支。
