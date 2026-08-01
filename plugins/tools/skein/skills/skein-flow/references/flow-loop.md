# flow 循环编排 (缺省路由的推进规则)

`/skein-flow` 无参 / 只给任务描述时的默认模式: 一路推到 finish, 阶段间自主续跑。

## 循环骨架

```
# 入口: 有任务描述 → 先走 plan 建/并入 task; 无参 → 直接扫 .skein 既有 task
while 有可推进 task:                      # task 级并发受 max_active (默认 2) 限
    按状态选阶段, 跑完即续下一阶段, 不回问用户:
      待处理 (未 confirm)  → plan  → 判据勾满 → skein confirm → 落到「就绪」
      就绪                 → skein start (占槽 + 建 worktree) → 进 exec
      进行中               → exec 调度循环 (claim exec → 派 agent → done → 再 claim exec)
      进行中 且 全 subtask done → skein check → 派 skein-checker
      检查中 且 全绿零冲突 → finish (勘察 + merge + 标记 + 异步 sediment)
      检查中 且 FAIL       → 回 planning 重确认 (❗停顿点, 见下)
    finish 完 → 回循环头取下一个 task
无可推进 → 报「无待执行 task」结束
```

阶段内部细则不在此重复: plan / exec / check / finish 各自的流程、硬门、失败模式全部以 SKILL.md 对应章节为准。本文件只定**阶段之间怎么续**。

**本节 `skein confirm` 特指当前循环焦点 task (flow 主循环正在推进的那个)** — flow 视 confirm 为非阻塞门, 判据勾满自动过、禁停手问用户。这与 [dag-scheduling.md](dag-scheduling.md) §6「plan-ahead 填空闲」中「不自动过用户门」**不冲突**: plan-ahead 处理的是**另一个尚未进入本轮循环焦点、exec 空闲时顺手预备的 pending task**, 只推到 confirm/start 门前即停, 待其成为循环焦点 (被 claim exec/exec 选中推进) 时再走本节的自动 confirm。二者分工: 焦点 task 的 confirm 自动过; 非焦点 task 被 plan-ahead 预备后仍停在confirm 门前, 不抢先替非焦点 task 做用户确认。

## 唯一允许停顿的点 (白名单, 其余一律续跑)

停顿 = 结束本回合等用户答。只有这几处:

| 停顿点 | 原因 |
|---|---|
| plan 的 brainstorm / grill 逐问 | 需求归用户, subagent 不能与用户对话 |
| check FAIL 后的修复方向确认 | 「方向确认=必经门」, 禁凭报告原文擅自补 subtask |
| subagent 回传 `需要: <问题>` | 信息缺口只有用户能填 |
| 触发破坏性 / 不可逆操作前 | 需显式授权 |
| plan 失败模式兜底 (需求未定 / scope 过大) | 已判定无法收敛 |

用户答完 → **立刻从停顿处继续循环**, 不要求用户再喊一次命令。

## 禁停顿 (违反 = 流程错误)

- ❌ plan 判据勾满后问「要不要开始执行」→ 直接 `skein confirm` + 续 exec
- ❌ 全 subtask done 后问「要不要 check」→ 直接 `skein check`
- ❌ check 全绿后问「要不要 finish」→ 直接 finish
- ❌ 一个 task finish 完就收工 → 回循环头继续下一个可推进 task
- ❌ 派出异步 subagent 后就地结束 → 等回传接着推 (异步等待须输出任务清单, 见 SKILL.md exec 两条硬规)
- ❌ 借口「这个简单」跳过 flow 内联直接做 (memory: `skein-hook-no-self-downgrade`)

## 终止条件

- 无就绪、无在途、无待处理可推进 task → 报「无待执行 task」
- 命中停顿点白名单 → 输出问题 + 当前进度, 等答
- 失败到兜底 (自愈超上限 / 根因超 scope / DAG 死锁) → 停手回传, 按 SKILL.md 对应失败模式表处置
