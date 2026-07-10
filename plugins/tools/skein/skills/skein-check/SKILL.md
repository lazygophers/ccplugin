---
name: skein-check
description: task check 阶段质量验证。exec 产物完成后 finish 前使用 — 派 skein-checker 跑 lint/type-check/tests/契约合规, 未过则派 skein-implementer 定点修复重检, 通过才放行 finish。验证与修复分离。
---

# skein-check — 质量验证门

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交 `skein-implementer` 修。未过禁 finish。

## 载体

- **验证** → 派 `skein-checker` (只读 + 跑命令, 回传 PASS/FAIL 报告)。
- **修复** → 派 `skein-implementer` (在 task worktree 内定点改)。
- main 作调度器串起「验证 → 修复 → 重验」循环, 不亲跑 check、不亲改码。

## 流程

1. **验证** — 派 `skein-checker`: 传 Active task id + worktree 路径 + planning 的验收标准。checker 跑 lint/type/test/build + 契约合规, 回传报告。
   - 🔴 **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail:
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <focus>` (列出 planning 阶段锁进 task.json 的契约)
     - 任一条 fail → 进修复循环 (同 lint/type/test 未过路径), 派 `skein-implementer` 定点修复后重检。
2. **判定** — PASS → 放行 finish。FAIL → 进修复循环。
3. **定点修复** — 按 checker 报告 (失败项 file:line + 报错原文 + 定位建议) 派 `skein-implementer` 修, 只改失败相关文件。
4. **重验** — 修复后重派 `skein-checker` 复跑。未过继续循环。
5. **放行** — 全绿 → 回 `skein-flow` 走 finish。

## 反复不过 (≥2 轮) 兜底

| 轮次 | 动作 |
|---|---|
| 1-2 轮 FAIL | 按报告定点修复重检 (正常循环) |
| 第 3 轮仍 FAIL | 🛑 STOP 回传用户 — 可能是需求/方案问题, 退回 planning 或转人工, 禁无限调试循环 |

## ⛔ 反例

check 阶段禁止行为与纠正动作详见 [references/anti-patterns.md](references/anti-patterns.md)。
