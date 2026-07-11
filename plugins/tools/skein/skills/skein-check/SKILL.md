---
name: skein-check
description: task check 阶段质量验证。exec 产物完成后 finish 前使用 — 派 skein-checker 跑 lint/type-check/tests/契约合规, 未过则派合适 agent (无则 general-purpose) 定点修复重检, 通过才放行 finish。验证与修复分离; 反复不过 (第 3 轮) 做 5 维根因复盘。
---

# skein-check — 质量验证门

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent (无则 `general-purpose`) 修。未过禁 finish。

## 载体

- **验证** → 派 `skein-checker` (只读 + 跑命令, 回传 PASS/FAIL 报告)。
- **修复** → 派合适 agent (按修复性质挑现有 agent, 无则 `general-purpose`) 在 task worktree 内定点改 (dispatch prompt 带执行纪律)。
- main 作调度器串起「验证 → 修复 → 重验」循环, 不亲跑 check、不亲改码。

## 流程

1. **验证** — 派 `skein-checker`: 传 Active task id + worktree 路径 + planning 的验收标准。checker 跑 lint/type/test/build + 契约合规, 回传报告。
   - **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail:
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id>` (列出 planning 阶段锁进 task.json 的契约)
     - 任一条 fail → 进修复循环 (同 lint/type/test 未过路径), 派合适 agent (无则 `general-purpose`) 定点修复后重检。
2. **判定** — PASS → 放行 finish。FAIL → 进修复循环。
3. **定点修复** — 按 checker 报告 (失败项 file:line + 报错原文 + 定位建议) 派合适 agent (无则 `general-purpose`) 修, 只改失败相关文件。
4. **重验** — 修复后重派 `skein-checker` 复跑。未过继续循环。
5. **放行** — 全绿 → 回 `skein-flow` 走 finish。

## 反复不过 (≥2 轮) 兜底

| 轮次 | 动作 |
|---|---|
| 1-2 轮 FAIL | 按报告定点修复重检 (正常循环) |
| 第 3 轮仍 FAIL | STOP 定点循环 → 按 [references/root-cause-protocol.md](references/root-cause-protocol.md) 做结构化根因复盘 (5 维定位 root cause + 预防措施), 禁无限盲改。2 出口: 带根因回 exec 定向重修, 或 STOP 附根因报告转人工 |

## 反例

违反上文即流程错误: main 亲跑 lint/test (应派 checker) / checker 自己改码 (应交合适修复 agent) / 未全绿就 finish / 只跑 lint 不验契约 (先 `skein.py contract` 逐条报) / 无限重检 (第 3 轮走根因复盘)。
