# Workflow 升级参考 (仅特别复杂 task)

> 本文件内容**仅当 task 特别复杂、用户显式同意升级为 Claude Code Workflow 时**才用。普通 task 走 subagent 编排 (Agent tool 共享 task worktree 串/并), **不读本文件**。
>
> 从 `trellisx-flow` SKILL.md 主文迁出, 减 token + 防 AI 被骨架诱导误升级 Workflow。

## 升级门槛 (不达则禁升级)

特别复杂 task (满足任一, 且用户显式同意):
- 大规模 fan-out (≥5 同类文件批量 / 500+ 文件迁移)
- 仓库级审计
- 多阶段重度并行

普通 task (跨几文件 / 单模块) → subagent 编排足够, 禁升级。

## Workflow 骨架 (Claude Code Workflow tool, 四规范内嵌)

```js
// trellisx exec workflow 骨架 — Claude Code Workflow tool
// 四规范内嵌: ①meta.phases标类型 ②parallel分层 ③agent_with_retry ④finalize收尾
export const meta = {
  name: 'task-exec',
  description: '<task title> 执行',
  phases: [                                    // ① 逐 phase 标类型, 用户一眼看懂
    { title: 'research',  detail: '采集 spec/依赖 (无则跳)', type: 'research' },
    { title: 'implement', detail: 'fan-out 写盘, 每 agent 一 worktree', type: 'implement' },
    { title: 'verify',    detail: 'check agent 跑测试/自验', type: 'verify' },
    { title: 'finalize',  detail: 'finish+commit+merge+销 worktree', type: 'finalize' },
  ],
}

// ③ 失败自动重试包装: 瞬时错误重试 ≤2, 仍败返 null (不崩 workflow)
async function agent_with_retry(prompt, opts, max = 2) {
  for (let i = 0; i <= max; i++) {
    try { return await agent(prompt, opts) }
    catch (e) { if (i === max) { log(`agent 重试耗尽: ${e}`); return null } }
  }
}

phase('implement')
// ② 无依赖 fan-out → parallel 并发; 每 writer 一 worktree 隔离
const writers = SUBTASKS.map(s => () =>
  agent_with_retry(s.prompt, { isolation: 'worktree', schema: WRITE_SCHEMA }))
const written = (await parallel(writers)).filter(Boolean)   // null 自动跳过

phase('verify')                                 // ② 有依赖 → 分层: verify 在 implement 后
const checked = (await parallel(
  written.map(w => () => agent_with_retry(checkPrompt(w), { schema: CHECK_SCHEMA })))).filter(Boolean)

phase('finalize')
// ④ 收尾: 先 AI 层清悬挂 (TaskList/TaskStop, 在 main 侧做), 再 git 层 finish
// task.py finish 经 hook 触发 commit→merge 子分支→销毁全部 worktree→archive
return { written, checked, finalize: 'run task.py finish after TaskStop sweep' }
```

> 默认载体 (subagent 编排) 即用同骨架的 subagent pipeline 形态 (Agent tool, subagent **共享 task worktree**, 不传 isolation:worktree), 重试与收尾语义不变。本文件下方骨架里的 `isolation: 'worktree'` 属 Workflow 升级路径 (opt-in 多 worktree), 仅在用户显式同意升级后才用。

> ⛔ **Workflow 是异步的, 禁 `sleep`/轮询阻塞 main 等待**: `Workflow` 工具调用即返回 task ID, 干完自动回 `<task-notification>`。**严禁 `Bash(sleep N && ...)` 或任何轮询循环占住 main 等 workflow 跑完** —— 调用 workflow 后**直接结束本回合**, notification 回来再继续 finish 清理。sleep 等待 = 既阻塞 main 又对不齐真实时长 = 反模式。

## workflow 四规范 (升级时生成的 Workflow 必须满足)

> 默认 subagent 编排的普通 task **不适用**本四规范 (其收尾由 flow 主文「其他必做」的 finish 闭环保证)。仅当 task 特别复杂、用户显式同意升级为 Workflow 时, 生成的 Workflow 须满足下列四条:

① **phases 细致标类型** — `meta.phases` 逐项标 `title` + `detail`, 阶段类型取自 {research, design, implement, verify, finalize}, 用户一眼看出每 phase 干什么属什么类型。

② **允许并行** — 无依赖 phases / fan-out agent 用 `parallel()` 并发; 有前后序的用分层 `parallel()` 表达, 不留无谓串行。

③ **失败自动重试** — 单 step/agent 失败自动重试 ≤2 次, 不让整个 workflow 直接失败; 重试仍败才降级 (返回 null + 下游 `.filter(Boolean)` 跳过, 或转 manual Blocked)。

④ **收尾无残留** — finalize phase 强制 `task.py finish` (hook 触发 commit→merge→remove worktree→archive) + finish 前 AI 自查无悬挂 Workflow/agent (TaskList 查 / TaskStop 关)。worktree 未销 / Workflow 未关 = 未闭环, 禁宣告 Done。
