---
name: skein-grill
description: 对抗式审查 (红队, 非审批)。planning 产物 (prd/implement) start 前硬门、或用户显式 "grill/盘方案/审设计/红队" 时使用 — 多轴逼问挖漏洞/隐藏假设/未定边界, 逐问给推荐答案+codebase 先查, 弱点表交用户裁才放行。main 亲做 (交互式)。
disable-model-invocation: true
user-invocable: false
argument-hint: "[方案/PRD 路径] (缺省=当前 task planning 产物)"
arguments: 要盘的方案或 PRD 路径 (可选, 缺省取当前 task 的 prd.md/implement.md)
---

# skein-grill — 对抗式审查硬门

审查对象 = planning 产物 (`prd.md` / `implement.md`) 或用户点名要盘的方案。目的: **start/exec 前把需求与方案的漏洞、隐藏假设、未定边界逼出来**, 不是复述内容。

**载体**: main 亲做, 交互式 (逐条与用户确认), **禁派 subagent** (它不能 `AskUserQuestion`)。

## 立场 (红队, 不是盖章)

- **对抗非审批** — grill 是挑刺不是审批。**找不到盲点 ≠ 通过, 是 grill 失败** (没问够)。默认「一定有没定的边界 / 没验的假设」, 挖到为止。
- **结构合规 ≠ 实质有效** — PRD 格式齐全不代表需求对。专挖「写得像模像样但实际会翻车」的盲点。

## 提问法 (源自 grill-me: relentless interview)

- **逐问审, 可一次多问** — 强相关 / 同源决策点批量一次 `AskUserQuestion` 确认提效; 互不相关或需先答才能定下一问的分批。
- **每问给推荐答案** — 不空问, 带上你的判断让用户裁 (补 / 接受风险 / 砍需求)。
- **codebase 优先** — 问题能由 Read/Grep 文件答的自己查, 不问用户。只问 codebase 答不了的决策点。

## 触发

- **planning 硬门 (强制)**: skein-planning 产出 planning 产物后、`skein.py start` **前 MUST 跑一轮**。🔴🛑 **未跑 grill 禁 start** — 弱点表未补齐或有未裁决弱点, 停在本步, 禁推进 exec。
- **用户显式**: `/skein-grill` 或 "盘一下这个方案 / 审下设计 / 红队"。

**不触发 (跳过)**: 纯查询 / 问答 (无 planning 产物) · inline 豁免任务 (无 task) · 同一产物未变更且已 grill 过一轮 (无新增改动)。

## 明细 (审查轴 / 失败模式 / 输出弱点表 / 反例)

跑 grill 时详见 `references/review-axes-and-output.md` — 7 条审查轴逼问、失败模式 if-then 三段式、弱点表输出格式、反例。
