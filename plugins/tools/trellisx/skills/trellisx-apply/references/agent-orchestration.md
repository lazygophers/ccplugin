# Agent 编排模型 (main 编排 + 并行流水线)

trellisx-apply 不再由 main 串行手做, 而是 **main 编排 + subagent 并发执行**。本文件定义 agent 清单、并发分组、文件集分区与 6 字段 prompt 模板。

## 总览

```
Phase A 并行规划 (6 read-only agent, 同批)
   plan-diagnose  plan-workflow  plan-spec  plan-hook  plan-agent  plan-finishcmd
        └──────────────┴─────┬───────┴──────────┴──────────┴──────────┘
                             ▼
Gate 审批 (main 仅 AskUserQuestion + 编排)
   汇总 plan → 展示 diff plan → AskUserQuestion
                             ▼
   prep-backup agent (串行 1 个): git stash push -- .trellis/
                             ▼
Phase B 并行写盘 (5 writer agent, 同批, disjoint 文件集)
   write-workflow  write-spec  write-hook  write-agent  write-finishcmd
                             ▼
Phase C 并行验证 (5 verify agent, 同批)
   verify-workflow  verify-hook  verify-spec  verify-agent  verify-finishcmd
        │
        ├─ 任一 ✗ → main 派对应 writer 重注 → 重验 (修复循环, ≤3 次)
        └─ 写盘/验证失败 → rollback agent (串行 1 个): git stash pop
```

**并发实现**: 同批 agent 在**一条消息内多个 Agent 工具调用** (无依赖才能并发)。阶段间串行 (B 依赖 Gate+备份, C 依赖 B 产物)。

## main 只做这两类 (其余全派 agent)

main **不执行任何 repo 操作** (不 Read/Edit/Write/Bash/git 改盘), 只做:

| main 亲做 | 为什么不派 agent |
| --- | --- |
| `AskUserQuestion` 审批门 | 全局硬规: agent 不得直接问用户; 这是**用户交互不是 repo 操作**, 唯一不可派 |
| 编排决策 (汇总 plan/渲染 diff、派发顺序、修复循环) | 跨 agent 聚合与调度是编排本身, 不是文件操作 |

**所有 repo 操作 (含 git) 一律派 agent**:

| 操作 | 谁执行 | 串/并 |
| --- | --- | --- |
| `git stash push` 备份 | `prep-backup` agent | 串行 (审批后、写盘前 1 个) |
| 写盘 (5 维) | 5 writer agent | 并行 (disjoint 文件集) |
| 验证 (5 维) | 5 verify agent | 并行 |
| `git stash pop` 回滚 | `rollback` agent | 串行 (失败时 1 个) |

> git 操作虽共享 index 顺序敏感, 但「顺序敏感」=单 agent 串行执行, **不等于 main 亲做**。main 派 prep-backup/rollback 单 agent 串行跑, 自己不碰 git。

## Phase A — 并行规划 (read-only, 同批 6 agent)

全部 **read-only** (禁写盘), 各自诊断本维度现状 + 算出最终注入文本/diff (**目标语言**), 返回结构化 plan。互不依赖 → 一批并发。

| agent | 目标产物 | 读 |
| --- | --- | --- |
| `plan-diagnose` | 模式 (首次/更新) + workflow-state 锚点块清单 + gitignore 状态 + **定目标语言** (综合 `$LANG`+CLAUDE.md+会话, 传给所有 writer) | `diagnose.md` |
| `plan-workflow` | workflow.md **全部 marker 注入块最终文本** (目标语言) + i18n 全文叙述翻译 + **删非 Claude Code 平台描述** (codex/cursor/gemini 等专属段整删) 的 diff | `workflow-injection.md` |
| `plan-spec` | spec/guides/trellisx-worktree.md 是否存在 → 新增内容 (目标语言; 存在则标「跳过」) | `spec-injection.md` |
| `plan-hook` | config.yaml hooks (after_start/after_finish/after_archive) + session_auto_commit:true + 五脚本拷贝清单 + gitignore + **packages discover** (跑 `trellisx-packages.py discover`) | `hook-injection.md` |
| `plan-agent` | trellis*.md background:true 改动清单 | `agent-injection.md` |
| `plan-finishcmd` | 目标 `.claude/commands/trellis/finish-work.md` 全链注入计划 (定位 archive 步骤前插点; 无文件则标「跳过, hook 路兜底」) | `finishcmd-injection.md` |

> 各 plan agent **自诊断本维度** (不阻塞等 plan-diagnose, 但目标语言以 plan-diagnose 为准); 全部注入产物语言 = plan-diagnose 定的目标语言。

## Phase B — 并行写盘 (5 writer agent, 同批, disjoint 文件集)

prep-backup agent 备份后派发。**每 writer 独占不相交文件集**, 并发无冲突。

| writer | 独占文件集 (sole owner) |
| --- | --- |
| `write-workflow` | `.trellis/workflow.md` |
| `write-spec` | `.trellis/spec/guides/trellisx-worktree.md` |
| `write-hook` | `.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish,trellisx-packages}.py` + `.trellis/config.yaml` (hooks + `session_auto_commit: true` + `packages:` 经 `trellisx-packages.py apply`) + `<git根>/.gitignore` |
| `write-agent` | `.claude/agents/trellis*.md` |
| `write-finishcmd` | `.claude/commands/trellis/finish-work.md` (全链注入, marker 幂等) |

**禁文件集重叠** —— 任两 writer 不得碰同一文件 (config.yaml 只归 write-hook; finish-work.md 只归 write-finishcmd)。用户选「仅 workflow.md」→ 只派 `write-workflow`。

## 串行单 agent: prep-backup / rollback (git 操作, main 不亲做)

| agent | 时机 | 动作 |
| --- | --- | --- |
| `prep-backup` | 审批后、Phase B 前 (串行 1 个) | `git stash push -- .trellis/` 备份; 失败 → 报告, 不进 B |
| `rollback` | writer/verify 失败时 (串行 1 个) | `git stash pop` 恢复 backup |

## Phase C — 并行验证 (5 verify agent, 同批)

| verify | 验证项 (对应 `apply-verify.md`) |
| --- | --- |
| `verify-workflow` | **行为闭环**: 标签配对 / 断言③ no_task 仍含建 task 路径 / 断言① 五维 marker / 断言② 闭环链 (各 status + planning→implement→check→finish) / Phase 1-3 在 / **i18n 语言一致 (注入块叙述同目标语言, 无中英混杂)** / **无残留非 Claude Code 平台描述** |
| `verify-hook` | 五脚本 `ast.parse` / worktree+finish 均 `import trellisx_wt` / config hooks 可解析且 after_start 含 worktree、after_finish 含 trellisx-finish / `session_auto_commit=true` / packages 写入则 `get_packages()` 可解析 / gitignore 含 .worktrees/ |
| `verify-spec` | spec 文件存在 |
| `verify-agent` | 每 trellis*.md frontmatter `background: true` 全 ✓ |
| `verify-finishcmd` | finish-work.md 含 `trellisx:start:finishcmd_fullchain` + 引用 `trellisx-finish.py` 全链 (无文件则跳过) |

main 汇总: 全 ✓ → 完成报告; 任一 ✗ → 派对应 writer 按算法重注 → 重验, 循环 ≤3 次, 仍 ✗ 则派 rollback agent 回滚报缺失环节。

## 6 字段 prompt 模板 (派任一 agent 必填)

派 plan/writer/verify agent 一律自包含, 缺字段不派:

```
目标: <本 agent 单一职责, 如「算 workflow.md marker 注入 diff, 不写盘」>
已知: <模式(首次/更新) + 目标语言 + 相关 plan 结果 (writer/verify 需传入对应 plan)>
工作目录与范围: <项目根; 本 agent 独占文件集, 列绝对路径; 禁碰他 agent 文件>
输出格式: <plan agent → 结构化 diff/plan 文本(不写盘); writer → 写盘后报改动文件+行数; verify → 每检查项 ✓/✗ + 失败定位>
验收标准: <plan → diff 完整可审; writer → 文件落盘且 marker 幂等(不堆叠); verify → 全项明确判定>
失败处理: <plan → 读不到目标标注「缺」; writer → 写失败报文件名禁留半截; verify → ✗ 给精确定位供 main 重注>
```

**read-only plan agent / verify agent** prompt 必含「**禁写盘 / 禁改动任何文件**」硬约束。

## 与两条铁律的关系

- 🎯 **结果导向, 行为闭环为准**: writer 可替换/重构原生 (no_task/Phase/finish) 以达预期; **verify-workflow 是唯一硬门** —— 断言 ① 五维生效 ② create→…→finish 闭环 ③ task 创建触发仍生效。任一 ✗ → main 派 writer 重做 (修复循环 ≤3)。不再断言"原生文本未动"。
- 🪶 **软约束 + finish 强制**: 注入内容不变; 编排改造只改「谁执行」(main→agent 并发), 不改「注入什么」。
