---
name: skein-grill
description: 对抗式审查 (adversarial review)。planning 产物 (prd/implement) start 前的硬门、或用户显式要求盘问方案时使用 — 多轴质疑找漏洞/隐藏假设/未定边界, 弱点表交用户过后才放行。main 亲做 (交互式)。
---

# skein-grill — 对抗式审查硬门

审查对象 = planning 产物 (`prd.md` / `implement.md`) 或用户点名要盘的方案。目的: **start/exec 前把需求与方案的漏洞、隐藏假设、未定边界逼出来**, 不是复述内容。

**载体**: main 亲做, 交互式 (要逐条与用户确认), **禁派 subagent** (它不能 `AskUserQuestion`)。

## 触发

- 🔴 **planning 硬门**: skein-add 产出 planning 产物后、`skein.py start` 前 MUST 跑一轮。未跑禁 start。
- 用户显式 `/grill` 或"盘一下这个方案"。

## 审查轴 (按产物动态裁剪, 命中即质疑)

| 轴 | 逼问 |
|---|---|
| **需求真伪** | PRD 写的 = 用户真想要的? 有无脑补需求 / 过度设计? |
| **边界** | 输入/规模/并发/失败态的边界定了没? "模糊"处点名 |
| **假设** | 有哪些没写出来的隐藏假设? 假设错了会崩哪? |
| **调度** | implement 的 mermaid 调度图 / depends_on 完整? 有无环 / 漏边? |
| **验收** | 每个 subtask 有可执行验收基准? 还是"做好了"这种空话? |
| **反例** | 最可能翻车的一条路径是什么? 有没有兜底? |
| **YAGNI** | 哪几条是"以后可能要"硬塞的? 砍掉行不行? |

## 输出 (弱点表, 交用户过)

```
grill 弱点表
─────────────
[轴] 弱点 → 建议补法 (缺 X / 假设 Y 未验 / 边界 Z 未定)
...
```

- 弱点逐条 → `AskUserQuestion` 让用户裁 (补 / 接受风险 / 砍需求)。
- 用户确认"这就是我要的" + 弱点补齐/接受后才放行 start。
- **无弱点也要输出"已过 N 轴, 无阻断项"** (禁默默放行)。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| 复述 PRD 当审查 | 只输出漏洞 / 未定项, 不复述 |
| 派 subagent 盘 (它问不了用户) | main 亲做 AskUserQuestion |
| 未跑 grill 直接 start | planning 硬门, 必跑 |
| 纯文本列弱点让用户选 | 用 AskUserQuestion |
