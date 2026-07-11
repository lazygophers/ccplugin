---
name: skein-break-loop
description: check 反复不过时的结构化根因复盘 (break debug loop / 根因定位)。check 第 3 轮仍 FAIL、定点修复 ≥2 轮无效、跳出无限调试循环时使用 — 跨维度定位根因 (需求/设计/实现/环境/测试), 给预防措施, 可复用教训回流 skein-memory sediment。出口: 带根因回 exec 重修, 或 STOP 附根因报告转人工。
---

# skein-break-loop — 结构化根因复盘

check 定点修复 **≥2 轮仍 FAIL**、第 3 轮跳出调试循环时加载。**症状级修补已失败**, 此刻禁再盲改 —— 先做跨维度根因定位, 再决定回 exec 重修还是转人工。

> 🔴 STOP 再改一轮的冲动: 连修 2 轮不过说明问题**不在你改的那层**。第 3 轮继续同层定点改 = 无限循环。必须先复盘 root cause。

## 触发 (由 skein-check 路由进入)

| 条件 | 动作 |
|---|---|
| 定点修复 1-2 轮仍 FAIL | 仍走 skein-check 正常循环, **不进本 skill** |
| 第 3 轮仍 FAIL | 🛑 STOP 定点循环 → 加载本 skill 做结构化根因复盘 |

## 流程 (main 亲做, 复盘需跨维度语义判断)

1. **跨维度根因定位** — 逐维度问「是不是这里」, 收敛到 root cause。协议明细 (5 维度 checklist + 每维度探针问法 + 收敛判据) 详见 [references/root-cause-protocol.md](references/root-cause-protocol.md)。
2. **预防措施** — 定位根因后, 给「本次怎么修 + 同类怎么防」。
3. **可复用教训判定** — 复盘产出走 skein-memory 的 sediment 判定门 (core/recall/drop), 把根因写成**可验证契约**沉淀。禁把一次性 bug 硬凑成规则。详见下节。
4. **出口** — 二选一 (见「出口」节)。

## 沉淀 (复用 skein-memory, 禁新造)

复盘完的根因**不自动沉淀**, 走既有判定门:

- 判定 → 分层 → 审批 → 写盘四步, 完全复用 [skein-memory](../skein-memory/SKILL.md) 的 [sediment-workflow](../skein-memory/references/sediment-workflow.md), 命令是同一个 `memory.py sediment`。
- 🔴 本 skill **不新造沉淀机制**。命中判定门正向项②「踩坑 ≥2 轮 (根因可写可验证契约)」正是 break-loop 的典型场景 —— 反复不过 ≥2 轮本身就是踩坑证据, 但仍须过「排除」项 (一次性 bug / 本 task 私有细节 / 已有规则覆盖 → 跳过)。
- 沉淀正文写**根因契约** (可验证的 MUST/禁), 非流水账。

## 出口 (二选一)

| 出口 | 条件 | 动作 |
|---|---|---|
| **回 exec 重修** | 根因定位明确 (实现 bug / 测试本身错 / 环境可修) | 带**根因 + 预防措施**派 `skein-implementer` 定点重修, 回 skein-check 重验。**根因驱动的修复不计入原 3 轮上限** (是新一轮定向修, 非盲改) |
| **STOP 转人工** | 根因是需求理解偏差 / 方案设计缺陷 (超出 exec 层可修范围) | 🛑 STOP 回传用户: 附**根因报告** (哪个维度 + 证据 + 建议退回 planning / 改方案), 由用户裁定 |

## ⛔ 反例

check 反复不过时的禁止行为与纠正详见 [references/anti-patterns.md](references/anti-patterns.md)。
