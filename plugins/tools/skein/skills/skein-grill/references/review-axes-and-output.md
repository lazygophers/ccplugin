# skein-grill 明细：审查轴 / 输出格式 / 反例

## 审查轴 (按产物动态裁剪, 命中即质疑)

沿决策树逐支往下: 有依赖的轴先答前置再定后续 (如「边界」未定则「验收」无从写), 一个个 resolve 不跳枝。

| 轴 | 逼问 |
|---|---|
| **需求真伪** | PRD 写的 = 用户真想要的? 有无脑补需求 / 过度设计? |
| **边界** | 输入/规模/并发/失败态的边界定了没? "模糊"处点名 |
| **假设** | 有哪些没写出来的隐藏假设? 假设错了会崩哪? |
| **调度** | task.json 的子任务 DAG / depends_on 完整? 有无环 / 漏边? |
| **验收 (SMARC)** | 每条 AC Specific/Measurable/Achievable/Relevant/Context-bound 五项齐全? 出现 user-friendly / 快速 / 好用 / 灵活 类不可测词 → 降为 Open Question 而非 AC (做不到可测 = 不是验收, 是待问) |
| **drift 一致性** | 产出 (subtask DAG + prd) 仍服务原始 Job Story 愿景? 逐条 subtask 溯源 outcome — 与原始愿景无关的即渐进偏离, 砍或回溯; 多轮追问只追澄清不改原始愿景段 |
| **scope 吸收** | 每条 subtask 溯源到 said (明说) / implied (暗示) 哪条源诉求? 溯不回 = AI 脑补, 回 Out-of-Scope 或 Open Question (源说"支持 X", 禁顺手 spec XYZ) |
| **反例** | 最可能翻车的一条路径是什么? 有没有兜底? |
| **YAGNI** | 哪几条是"以后可能要"硬塞的? 砍掉行不行? |

> 轴按产物裁剪, 跳过的轴须在弱点表标 "未审 (无关)", 禁默默跳。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 某轴挖不出弱点 (grill 太顺) | 换角度深挖: 极端输入 / 并发 / 依赖失效 / 需求反向问 ("不做这条会怎样") | 深挖后仍无 → 显式记 "该轴已过, 无阻断项", 禁把"没想到"当"没问题" |
| 用户答不出某问 (需求本身没想清) | 给 2-3 个推荐选项让用户选, 而非开放式问 | 仍答不出 → 该点标 "需求未定", 停手 退回 skein-plan brainstorm 补, 禁带疑点 start |
| 循环 >3 轮弱点仍未收敛 | 归并同源弱点, 一次批量 `AskUserQuestion` 裁完 | 仍发散 → 停手, 提示 scope 过大, 建议拆多 task (交 planning heavy 档) |
| 用户想跳 grill 直接 start | 说明未 grill 的具体风险 (哪条边界/假设没验) | 用户坚持跳 → 记 "用户显式弃 grill 风险自担" 后放行 (禁默默跳, 留痕) |

## 输出 (弱点表, 交用户过)

```
grill 弱点表
─────────────
[轴] 弱点 → 建议补法 (缺 X / 假设 Y 未验 / 边界 Z 未定)
...
```

- 弱点逐条 → `AskUserQuestion` 让用户裁 (补 / 接受风险 / 砍需求); 默认一次一条, 仅互不依赖的同源弱点才一次批量。
- 停手-before-start: 用户确认"这就是我要的" + 每条弱点已补齐或显式接受风险后, 才放行 start; 有未裁决弱点禁 start。
- **无弱点也要输出"已过 N 轴, 无阻断项"** (禁默默放行)。

## 反例

| 禁 | 改为 |
|---|---|
| 复述 PRD 当审查 | 只输出漏洞 / 未定项, 不复述 |
| 派 subagent 盘 (它问不了用户) | main 亲做 AskUserQuestion |
| 未跑 grill 直接 start | planning 硬门, 必跑 |
| 纯文本列弱点让用户选 | 用 AskUserQuestion |
| 挖不出弱点就当"通过" | 找不到 = 没问够, 换角度深挖 (立场: 对抗非审批) |
| 空问不给推荐答案 | 每问带推荐判断 (grill-me 法) |
| 能查 codebase 却问用户 | 先 Read/Grep 自答, 只问文件答不了的 |
| AC 含 wishful 词 (user-friendly/快速/好用/灵活) 当验收通过 | 把不可测词降为 Open Question, AC 只留可执行基准 (SMARC) |
| subtask 溯不回源诉求仍保留 | 回溯到 said/implied; 溯不到回 Out-of-Scope (防 scope absorption) |
| 多轮追问后产出与原始愿景脱节 | 每轮澄清回写 prd 但原始愿景段不动; 偏离 subtask 砍掉 (防 drift) |
