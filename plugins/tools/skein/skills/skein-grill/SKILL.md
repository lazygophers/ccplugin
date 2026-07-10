---
name: skein-grill
description: 对抗式审查 (adversarial review)。planning 产物 (prd/implement) start 前的硬门、或用户显式要求盘问方案时使用 — 多轴质疑找漏洞/隐藏假设/未定边界, 弱点表交用户过后才放行。main 亲做 (交互式)。
---

# skein-grill — 对抗式审查硬门

审查对象 = planning 产物 (`prd.md` / `implement.md`) 或用户点名要盘的方案。目的: **start/exec 前把需求与方案的漏洞、隐藏假设、未定边界逼出来**, 不是复述内容。

**载体**: main 亲做, 交互式 (要逐条与用户确认), **禁派 subagent** (它不能 `AskUserQuestion`)。

## 触发

- 🔴 **planning 硬门**: skein-planning 产出 planning 产物后、`skein.py start` 前 MUST 跑一轮。未跑禁 start。
- 用户显式 `/grill` 或"盘一下这个方案"。

## 明细 (审查轴 / 输出弱点表格式 / 反例)

跑 grill 时详见 `references/review-axes-and-output.md` — 7 条审查轴逼问、弱点表输出格式、4 条反例。
