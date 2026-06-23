# Agent 编排模型 (Workflow 驱动优先, agent 流水线兜底)

trellisx-apply 的注入由 **main 编排 + 并行 subagent 执行**。优先用 **Workflow 脚本** (`apply.workflow.js`) 把扇出确定性编排成两次调用; 无 Workflow 工具的环境退回手写 agent 流水线。**main 不执行任何 repo 操作** (不 Read/Edit/Write/Bash/git 改盘), 只做 ① `AskUserQuestion` 审批门 (用户交互, 不可派) ② 编排决策 (汇总/派发/修复)。

> 维度已收敛为 **4 个** (workflow / spec / hook / finishcmd) —— 移除了 agent `background:true` 维度 (不再注入)。诊断 (diagnose) 作为 plan 阶段第 5 个 read-only agent。

## 方案 A (优先): Workflow 脚本驱动

脚本 = `skills/trellisx-apply/apply.workflow.js`, 一份脚本两种 `mode`。审批门必须在**两次 Workflow 调用之间**由 main 做 (Workflow 内 agent 不能问用户)。

```
1. main: Workflow({scriptPath: '<skill>/apply.workflow.js', args:{mode:'plan', lang}})
        → 并行跑 diagnose + 4 维 planner (read-only) → 返回 {plans:[{key,status,diff}]}
2. main: 汇总 plans → 展示统一 diff plan (含 packages 清单) → 🛑 AskUserQuestion 审批 (STOP)
3. 批准后 main: Workflow({scriptPath, args:{mode:'write', lang, plans:{workflow:diff, spec:diff, ...}}})
        → prep-backup (git stash) → 并行 4 维 writer (各自**写盘+自验**) → 任一失败自动 rollback
        → 返回 {ok, results} 或 {ok:false, failed, rolledBack:true}
4. main: ok=false → 据 failed 重跑 write (修复循环 ≤3) 或报告; ok=true → 完成报告
```

要点:
- **plan 与 write 分两次 Workflow 调用**, 因审批门夹在中间 (Workflow 不能 AskUserQuestion)。
- **writer 自验本维度** (语法 / marker 配对 / 行为闭环 / i18n), **无独立 verify 阶段** (原 Phase C 合并进 writer)。
- plan agent / writer agent 的详细职责见各 `references/*-injection.md`; 脚本 prompt 只引用 reference, 不重复正文。
- **轻量重跑快路径**: 已注入 (marker 全在) 且无结构变化 → writer 检测 marker 幂等跳过, 自然轻量, 不必额外编排。

## 方案 B (兜底): 手写 agent 流水线 (无 Workflow 工具时)

平台无 Workflow 工具 → main 手动按下表派 agent。**同批 agent 在一条消息内多个 Agent 工具调用** (无依赖才并发); 阶段间串行。

```
Phase A 并行规划 (5 read-only agent, 同批)
   plan-diagnose  plan-workflow  plan-spec  plan-hook  plan-finishcmd
                             ▼
Gate 审批 (main: 汇总 → 展示 diff → AskUserQuestion) → prep-backup agent (串行 git stash)
                             ▼
Phase B 并行写盘+自验 (4 writer agent, 同批, disjoint 文件集, 每 writer 写完自验)
   write-workflow  write-spec  write-hook  write-finishcmd
        └─ 任一 ✗ → main 派对应 writer 重注 (修复循环 ≤3) / 多次失败 → rollback agent (git stash pop)
```

### Phase A — 并行规划 (read-only, 5 agent)

全部 **read-only** (禁写盘), 各自诊断本维度 + 算注入 diff (目标语言), 返回结构化 plan。

| agent | 目标产物 | 读 |
| --- | --- | --- |
| `plan-diagnose` | 模式 (首次/更新) + workflow-state 锚点块清单 + gitignore 状态 + **定目标语言** (综合 `$LANG`+CLAUDE.md+会话, 传给所有 writer) | `diagnose.md` |
| `plan-workflow` | workflow.md 全部 marker 注入块最终文本 (目标语言) + i18n 全文叙述翻译 + **删非 Claude Code 平台描述** 的 diff | `workflow-injection.md` |
| `plan-spec` | spec/guides/trellisx-worktree.md 是否存在 → 新增内容 (存在则标「跳过」) | `spec-injection.md` |
| `plan-hook` | config.yaml hooks (after_create/start/finish/archive) + session_auto_commit:true + **五脚本**拷贝清单 + gitignore + packages discover | `hook-injection.md` |
| `plan-finishcmd` | 目标 `.claude/commands/trellis/finish-work.md` 全链注入计划 (无文件则标「跳过, hook 路兜底」) | `finishcmd-injection.md` |

### Phase B — 并行写盘 + 自验 (4 writer agent, disjoint 文件集)

prep-backup agent (`git stash push -- .trellis/`) 备份后派发。**每 writer 独占不相交文件集**, 写完**自验本维度**后返回。

| writer | 独占文件集 (sole owner) | 自验 |
| --- | --- | --- |
| `write-workflow` | `.trellis/workflow.md` | 标签配对 / 断言③ no_task 仍含建 task 路径 / 五维 marker / 闭环链 / Phase 1-3 / i18n 语言一致 / 无残留非 Claude Code 平台描述 |
| `write-spec` | `.trellis/spec/guides/trellisx-worktree.md` | 文件存在 |
| `write-hook` | `.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish,trellisx-packages}.py` + `.trellis/config.yaml` + `<git根>/.gitignore` | 五脚本 `ast.parse` / worktree+finish 均 `import trellisx_wt` / config hooks 可解析 (after_start 含 worktree, after_finish 含 trellisx-finish) / `session_auto_commit=true` / packages 可解析 / gitignore 含 .worktrees/ |
| `write-finishcmd` | `.claude/commands/trellis/finish-work.md` | 含 `trellisx:start:finishcmd_fullchain` + 引用 `trellisx-finish.py` 全链 (无文件则跳过) |

**禁文件集重叠** —— config.yaml 只归 write-hook; finish-work.md 只归 write-finishcmd。用户选「仅 workflow.md」→ 只派 `write-workflow`。

### 串行单 agent: prep-backup / rollback (git 操作, main 不亲做)

| agent | 时机 | 动作 |
| --- | --- | --- |
| `prep-backup` | 审批后、Phase B 前 (串行 1 个) | `git stash push -- .trellis/`; 失败 → 报告, 不进 B |
| `rollback` | writer 自验失败且修复循环耗尽时 (串行 1 个) | `git stash pop` 恢复 backup |

## 6 字段 prompt 模板 (派任一 agent 必填)

```
目标: <本 agent 单一职责, 如「算 workflow.md marker 注入 diff, 不写盘」>
已知: <模式(首次/更新) + 目标语言 + 相关 plan 结果 (writer 需传入对应 plan)>
工作目录与范围: <项目根; 本 agent 独占文件集, 列绝对路径; 禁碰他 agent 文件>
输出格式: <plan agent → 结构化 diff/plan (不写盘); writer → 写盘+自验, 报改动文件+自验结果>
验收标准: <plan → diff 完整可审; writer → 文件落盘且 marker 幂等 + 自验全过>
失败处理: <plan → 读不到目标标「缺」; writer → 写/验失败报精确定位, 禁留半截>
```

**read-only plan agent** prompt 必含「**禁写盘 / 禁改动任何文件**」硬约束。

## 与两条铁律的关系

- 🎯 **结果导向, 行为闭环为准**: writer 可替换/重构原生 (no_task/Phase/finish) 以达预期; **writer 自验是硬门** —— 断言 ① 五维生效 ② create→…→finish 闭环 ③ task 创建触发仍生效。任一 ✗ → main 派 writer 重做 (修复循环 ≤3)。
- 🪶 **软约束 + finish 强制**: 注入内容不变; 编排改造只改「谁执行/怎么扇出」(Workflow 脚本 / agent 流水线), 不改「注入什么」。
