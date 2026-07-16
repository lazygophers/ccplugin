---
name: skein-grill
description: 对抗式审查 (红队, 非审批)。planning 产物 (prd 主入口/design 详细设计/findings 调研 + task.json 子任务) start 前硬门、或用户显式 "grill/盘方案/审设计/红队" 时使用 — 多轴逼问挖漏洞/隐藏假设/未定边界, 逐问给推荐答案+codebase 先查, 弱点表交用户裁才放行。main 亲做 (交互式)。
user-invocable: false
argument-hint: "[方案/PRD 路径] (缺省=当前 task planning 产物)"
arguments: "[方案/PRD 路径] (缺省=当前 task planning 产物)"
model: opus
effort: xhigh
---

# skein-grill — 对抗式审查硬门

审查对象 = planning 产物 (`prd.md` 主入口 / `design.md` 详细设计 / `findings.md` 调研收敛 + task.json 子任务/调度) 或用户点名要盘的方案。目的: **start/exec 前把需求与方案的漏洞、隐藏假设、未定边界逼出来**, 不是复述内容。

**载体**: main 亲做, 交互式 (逐条与用户确认), **禁派 subagent** (它不能 `AskUserQuestion`)。

## 立场 (红队, 不是盖章)

- **对抗非审批** — grill 是挑刺不是审批。**找不到盲点 ≠ 通过, 是 grill 失败** (没问够)。默认「一定有没定的边界 / 没验的假设」, 挖到为止。
- **结构合规 ≠ 实质有效** — PRD 格式齐全不代表需求对。专挖「写得像模像样但实际会翻车」的盲点。

## 提问法 (源自 grill-me / grilling: relentless interview)

- **优先用 /grill-me 引擎** — 若环境装有 `/grill-me` (或 `/grilling`) skill, main 直接用它做访谈引擎跑 relentless interview; skein-grill 只补 skein 专属层 (审查轴 / planning 硬门 / 弱点表 / task.json 契约锁定)。未装则用下列内置提问法兜底。
- **走决策树, 逐个解依赖** — 沿决策树每个分支往下问, 决策间有依赖的先答前置再定后续, 一个个 resolve, 不跳枝。
- **默认一次一问, 仅同源可批** — 一次一问、等反馈再下一问 (多问令人困惑); 仅**互不依赖的同源决策点**才一次 `AskUserQuestion` 批量提效。有依赖 / 需先答才能定下一问的绝不合并。
- **每问给推荐答案** — 不空问, 带上你的判断让用户裁 (补 / 接受风险 / 砍需求)。
- **事实自查, 决策交用户** — 能由 Read/Grep/工具查到的**事实**自己查, 不问用户; **决策**逐条交用户等答复。
- **共识才放行** — 未与用户达成共识 (弱点表全裁决) 前禁动手推进 exec。

## 触发

- 🛑 **planning 硬门 (强制 · STOP)**: skein-plan 产出 planning 产物后、`skein start` **前 MUST 跑一轮**。**未跑 grill 禁 start** — 弱点表未补齐或有未裁决弱点, 停在本步, 禁推进 exec。
- **用户显式**: `/skein-grill` 或 "盘一下这个方案 / 审下设计 / 红队"。

**不触发 (跳过)**: 纯查询 / 问答 (无 planning 产物) · inline 豁免任务 (无 task) · 同一产物未变更且已 grill 过一轮 (无新增改动)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                     | 一线修复                                          | 仍失败兜底                                                       |
| ------------------------ | ------------------------------------------------- | --------------------------------------------------------------- |
| 某轴挖不出弱点 (太顺)    | 换角度深挖: 极端输入 / 并发 / 依赖失效 / 反向问   | 仍无 → 显式记「该轴已过, 无阻断项」, 禁把「没想到」当「没问题」  |
| 用户答不出某问 (需求没想清) | 给 2-3 推荐选项让用户选, 非开放式问              | 仍答不出 → 标「需求未定」, 停手退回 skein-plan brainstorm 补 |
| 循环 >3 轮弱点未收敛     | 归并同源弱点, 一次批量 `AskUserQuestion` 裁完     | 仍发散 → 停手, 提示 scope 过大, 建议拆多 task (planning heavy 档) |

## 反例 (命中 = grill 失败)

- 找不到盲点就放行 — 没问够 ≠ 通过 (默认一定有未定边界 / 未验假设, 挖到为止)。
- 复述 PRD 内容当审查 — grill 是挑刺不是摘要。
- 结构齐全就盖章 — 格式对 ≠ 需求对。
- 空问不给推荐答案 — 每问必带你的判断让用户裁 (补 / 接受风险 / 砍需求)。
- 能 Read/Grep 自查的去问用户 — codebase 优先, 只问文件答不了的决策点。
- 派 subagent 做 grill — 它不能 `AskUserQuestion`, 必 main 亲做。
- 弱点表有未裁决项就放行 start — 未补齐禁推进 exec。
- 装了 /grill-me 引擎却弃用另起炉灶 — 有则复用其访谈法, skein-grill 只叠 skein 专属层。

## 明细 (审查轴 / 失败模式 / 输出弱点表)

跑 grill 时详见 `references/review-axes-and-output.md` — 7 条审查轴逐条逼问、失败模式 if-then 三段式、弱点表输出格式。
