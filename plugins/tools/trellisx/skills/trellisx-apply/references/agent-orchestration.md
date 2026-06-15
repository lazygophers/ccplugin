# Agent 编排模型 (main 编排 + 并行流水线)

trellisx-apply 不再由 main 串行手做, 而是 **main 编排 + subagent 并发执行**。本文件定义 agent 清单、并发分组、文件集分区与 6 字段 prompt 模板。

## 总览

```
Phase A 并行规划 (5 read-only agent, 同批)
   plan-diagnose  plan-workflow  plan-spec  plan-hook  plan-agent
        │              │           │          │          │
        └──────────────┴─────┬─────┴──────────┴──────────┘
                             ▼
Gate 审批 (main 串行, 不可派 agent)
   汇总 5 plan → 展示 diff plan → AskUserQuestion → git stash 备份
                             ▼
Phase B 并行写盘 (4 writer agent, 同批, disjoint 文件集)
   write-workflow   write-spec   write-hook   write-agent
                             ▼
Phase C 并行验证 (4 verify agent, 同批)
   verify-workflow  verify-hook  verify-spec  verify-agent
        │
        └─ 任一 ✗ → main 派对应 writer 重注 → 重验 (修复循环, ≤3 次)
```

**并发实现**: 同批 agent 在**一条消息内多个 Agent 工具调用** (无依赖才能并发)。阶段间串行 (B 依赖 Gate 批准, C 依赖 B 产物)。

## 不可委派的串行节点 (MUST main 自己做)

| 节点 | 为什么不可派 |
| --- | --- |
| `AskUserQuestion` 审批门 | 全局硬规: agent 不得直接向用户提问; 审批只能 main 走工具 |
| `git stash` 备份 / `git stash pop` 回滚 | 共享 git index, 并发 stash 撕裂状态; 顺序敏感 |
| 汇总各阶段 agent 结果 + 渲染 diff plan | 跨 agent 聚合是编排职责 |
| 修复循环调度 (verify ✗ → 重派 writer) | 编排决策 |

## Phase A — 并行规划 (read-only, 同批 5 agent)

全部 **read-only** (禁写盘), 各自诊断本维度现状 + 算出最终注入文本/diff, 返回结构化 plan。互不依赖 → 一批并发。

| agent | 目标产物 | 读 |
| --- | --- | --- |
| `plan-diagnose` | 模式 (首次/更新 apply, 据 trellisx marker 数) + workflow-state 锚点块清单 + gitignore worktrees 状态 + **目标语言** (综合 `$LANG`+CLAUDE.md+会话) | `diagnose.md` |
| `plan-workflow` | workflow.md **全部 marker 注入块最终文本** + i18n 全文叙述翻译 + 清理 (维护者注释/跨平台枚举) 的 diff | `workflow-injection.md` |
| `plan-spec` | spec/guides/trellisx-worktree.md 是否存在 → 新增内容 (存在则标「跳过」) | `spec-injection.md` |
| `plan-hook` | config.yaml hooks 注入块 + 四脚本拷贝清单 (trellisx_wt/worktree/taskmd/finish) + gitignore 追加 | `hook-injection.md` |
| `plan-agent` | trellis*.md background:true 改动清单 (每文件: 已 true 跳过 / 非 true 改 / 缺则加) | `agent-injection.md` |

> 各 plan agent **自诊断本维度** (不阻塞等 plan-diagnose); plan-diagnose 仅产总览报告供 main 汇总。

## Phase B — 并行写盘 (4 writer agent, 同批, disjoint 文件集)

审批 + git stash 后派发。**每 writer 独占不相交文件集**, 并发无冲突。

| writer | 独占文件集 (sole owner) |
| --- | --- |
| `write-workflow` | `.trellis/workflow.md` |
| `write-spec` | `.trellis/spec/guides/trellisx-worktree.md` |
| `write-hook` | `.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish}.py` + `.trellis/config.yaml` + `<git根>/.gitignore` |
| `write-agent` | `.claude/agents/trellis*.md` |

**禁文件集重叠** —— 任两 writer 不得碰同一文件 (尤其 config.yaml 只归 write-hook)。用户选「仅 workflow.md」→ 只派 `write-workflow`。

## Phase C — 并行验证 (4 verify agent, 同批)

| verify | 验证项 (对应 `apply-verify.md`) |
| --- | --- |
| `verify-workflow` | marker 数 = 注入数 / marker 在对应块内不串位 / no_task 原生正文非空 (>40 字符) / Phase 1-3 在 / 闭环链 (subtask→worktree→check→finish) |
| `verify-hook` | 四脚本 `ast.parse` 合法 / worktree+finish 均 `import trellisx_wt` / config hooks 可解析 / finish 段含 `trellisx-finish.py` / gitignore 含 .worktrees/ |
| `verify-spec` | spec 文件存在 |
| `verify-agent` | 每 trellis*.md frontmatter `background: true` 全 ✓ |

main 汇总: 全 ✓ → 完成报告; 任一 ✗ → 派对应 writer 按算法重注 → 重验, 循环 ≤3 次, 仍 ✗ 则回滚报缺失环节。

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

- 🔒 **纯增量追加**: 由 writer agent 执行注入算法保证 (marker 包裹幂等替换), verify-workflow 强制断言 no_task 原生正文非空。
- 🪶 **软约束 + finish 强制**: 注入内容不变; 编排改造只改「谁执行」(main→agent 并发), 不改「注入什么」。
