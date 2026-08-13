---
name: skein-performance
description: 按 session 记录审计 skein 插件的行为偏差、Bug 与 token 浪费, 出可落地修复清单并派 agent 修复
argument-hint: "[claude code session-id] [--research]"
arguments: "[session-id]"
---

# skein 插件审计

对 session `$session-id` 审计 `plugins/tools/skein/`。main 只做调度,审计规范在 `skein-auditor`,修复规范在 `skein-fixer`。

1. 派 `Agent(subagent_type="skein-auditor")`,prompt 给完整的用户描述、本轮是否带 `--research`、仓库根路径。审计方法与硬约束归 agent 自己,别在这里复述。
2. agent 回传 = 报告 + 临时 fixer agent 名单 + HTML 路径。原样转达报告表与两段结论,不重排、不追加自己的判断。
3. `open <HTML 绝对路径>` 打开确认页,再用 `AskUserQuestion` 问用户是否执行修复、是否要跳过某些批次。
4. 用户同意 → 按名字派 `.claude/agents/skein/` 下的临时 fixer agent(`subagent_type="skein-fix-<批次 slug>"`)，提示词传递用户指令,文件面互斥的批次并行派。缺陷清单已写在 agent 自身,prompt 只给仓库根路径,不再转述。临时 agent 缺失或派不动时,才退回 `subagent_type="skein-fixer"` 并在 prompt 里带全清单。
5. fixer 全部回传后,核对暂存区改动与回传是否一致,报告给用户。
6. **清理**:删掉本轮的 `.claude/skein/audit-*.html` 与 `.claude/agents/skein/` 下本轮生成的 md,目录空了一并删。删前把清单报给用户。用户中途放弃修复时同样清理。

## Checkpoints

🛑 **禁用 skein 处理本流程** —— 不建 task,不走 flow
🛑 **审计与修复规范不写在本文件** —— 归 `skein-auditor` / `skein-fixer`,避免两处漂移
🛑 **用户确认走 `AskUserQuestion`** —— 不用纯文本征询
🛑 **并行 fixer 的文件面必须互斥** —— 有重叠就串行派
🛑 **收尾必清临时产物** —— HTML 与临时 agent md 都是一次性的,留着会污染后续会话的 agent 列表
