# Implement — exec 调度自动化规程强化

## 改动清单 (顺序执行, main 同步)

### D1: flow SKILL.md step4 exec

`plugins/tools/trellisx/skills/trellisx-flow/SKILL.md` step 4 (exec) 段末, 加 🔴 硬规条:

> 🔴 **exec 阶段 subtask 间禁问用户顺序** —— 顺序决策归 planning (mermaid 调度图 + depends-on + 静态冲突 DAG), exec 阶段只跑动态调度循环 (scheduling.md §4): ready 即派、完成即派下一个、并发上限 2, **禁在任何 subtask 之间停下来问用户"先做哪个 / 下一个做什么"**。唯一例外: planning 阶段就没定顺序 (PRD 缺调度图 / depends-on 缺失) → 🛑 STOP 退回 planning 补, 不在 exec 问。

### D2: scheduling.md

`.../trellisx-orchestrate/references/scheduling.md`:
- §4 调度循环后加禁令框 (§4.1 或并入"关键性质")
- §7 自检加: `- [ ] exec 阶段任一 subtask 完成后, 自动按 DAG 派下一个, 未问用户顺序`

### D3: orchestrate SKILL.md 反例黑名单

`.../trellisx-orchestrate/SKILL.md` 反例表加一行:

| 8 | exec 阶段 subtask 之间停下来问用户"先做哪个" | 顺序归 planning, exec 只跑调度循环 | 按 DAG 自动派 (scheduling.md §4); PRD 缺调度图 → 退回 planning 补 |

(注意现有反例表已有 1-7, 编号续)

### D4: progress-communication.md

先读, 若已有"完成即派禁问序"则跳过 (D4 标 optional); 缺则补一句。

### D5: 质检

```bash
# 各文件 grep 验证禁令落地
grep -rl "exec 阶段.*禁问\|禁问用户顺序\|禁.*问.*顺序" plugins/tools/trellisx/skills/

# claude -p 质检: 模型读改后 flow SKILL, 问 exec 阶段该不该问顺序
claude -p "读 plugins/tools/trellisx/skills/trellisx-flow/SKILL.md 的 step 4 (exec)。一个 subtask 完成后, 下一个该问用户决定还是自动派?" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

预期: 返回含"自动派 / 不问用户"语义。

## 验证命令

- grep 禁令命中 ≥3 文件
- claude -p 返回自动派语义
- token: 每文件增量 < 15 行 (Read 改前改后行数对比)

## Rollback

纯文档改, `git checkout -- <file>` 即回滚单个文件。
