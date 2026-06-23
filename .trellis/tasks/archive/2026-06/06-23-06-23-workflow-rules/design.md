# Design — trellisx workflow 执行规范

## 设计立场

trellisx = 改造工具, 规则内化进项目 `.trellis/`。本次不加新文件, 把 4 条规范内嵌进两个 canonical 落点:
1. **trellisx-flow 骨架** — AI 抄这段生成 workflow, 骨架自带 4 条 = 抄即合规 (最高杠杆)。
2. **workflow-injection.md 注入点** — apply 时落进项目规则, 约束运行期。

其余文件 (orchestrate refs / apply SKILL / README / finish.py docstring) 仅**对齐措辞**, 消除冲突。

## Canonical 共享文本 (所有 writer 逐字引用, 禁各自改写)

### C1 — 4 条 workflow 规范 (标准表述)

> **trellisx workflow 四规范** (有 task 且进入执行阶段时, 生成的 Workflow 必须满足):
> ① **phases 细致标类型** — `meta.phases` 逐项标 `title` + `detail`, 阶段类型取自 {research, design, implement, verify, finalize}, 用户一眼看出每 phase 干什么属什么类型。
> ② **允许并行** — 无依赖 phases / fan-out agent 用 `parallel()` 并发; 有前后序的用分层 `parallel()` 表达, 不留无谓串行。
> ③ **失败自动重试** — 单 step/agent 失败自动重试 ≤2 次, 不让整个 workflow 直接失败; 重试仍败才降级 (返回 null + 下游 `.filter(Boolean)` 跳过, 或转 manual Blocked)。
> ④ **收尾无残留** — finalize phase 强制 `task.py finish` (hook 触发 commit→merge→remove worktree→archive) + finish 前 AI 自查无悬挂 Workflow/agent (TaskList 查 / TaskStop 关)。worktree 未销 / Workflow 未关 = 未闭环, 禁宣告 Done。

### C2 — 作用域边界 (统一判定, 消除 flow vs orchestrate 冲突)

> **何时建 task (workflow 规范的触发前提)**:
>
> | 特征 | 判定 |
> | --- | --- |
> | 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task |
> | 单文件单处改, ≤20 行且位置已知 | 豁免 |
> | 跨 ≥2 文件 / 单文件多处 / 多步骤改 | **必建 task** |
> | 需外部调研 (库选型/方案对比) 或产出文档交付 | **必建 task** (调研为 research subtask) |
> | 边界模糊 | **MUST AskUserQuestion 由用户裁定** |
>
> **无 task → 不进 workflow → 四规范豁免**。Planning 阶段也不进 workflow: brainstorm 主线由 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research 并行, 但设计决策由 main 汇总裁定。

### C3 — retry 分工 (规范③落地)

> **两层重试, 各管一类失败**:
> - **workflow 脚本内自动重试** (瞬时错误: 网络抖动/工具超时/index.lock) — `agent_with_retry` 包装, 默认 2 次, 指数退避语义。
> - **main 重派** (逻辑失败: 自验 ✗/产物不达标) — 对齐 apply 修复循环, 同一 subtask 累计 ≤3 次, 第 4 次禁盲目重试, 回 planning 重拆。
> - 重试计数 per-agent; 全部重试耗尽 → 该 agent 返回 null, workflow 不崩, 收尾时该项标 Blocked 上报。

### C4 — 收尾 git 层 vs AI 层 (规范④界限, 四处对齐)

> **收尾两层, 责任不同**:
> - **git 层 (确定性脚本 trellisx-finish.py)**: commit → merge --no-ff 各子分支 (子先主后) → 销毁 worktree → archive。冲突则 abort + 报清单, 不强解。
> - **AI 层 (脚本做不到, 必须 AI 主动)**: finish 前用 TaskList 查本 task 名下悬挂 Workflow/后台 agent, 逐个 TaskStop 关闭。**finish.py 只销 worktree, 不关 Workflow/Task**。
> - 顺序: 先 AI 层清悬挂任务 (⓪) → 再 git 层 finish (①)。worktree 仍有进程在写时销毁 = 流程错误。

### C5 — 新 Workflow 骨架 (替换 flow 现 55-65 行, writer 逐字采用)

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

> 非 Claude Code (无 Workflow tool) 降级: 同骨架改用 subagent pipeline (Agent tool + isolation:worktree 串/并), 重试与收尾语义不变。

## 落点改动矩阵

| 文件 | 改什么 | 引用 canonical |
| --- | --- | --- |
| flow/SKILL.md | 替换骨架 (55-65) 为 C5; 硬规段加 C1 四规范 + C2 边界 | C1 C2 C5 |
| apply/references/workflow-injection.md | 注入点0 加 C2 判定表; 注入点2 in_progress 硬规编码 C1+C3; 注入点4 finish_force step⓪ 用 C4 | C1 C2 C3 C4 |
| apply/references/finishcmd-injection.md | step⓪ 措辞对齐 C4 | C4 |
| orchestrate/references/failure-recovery.md | retry 分工对齐 C3 | C3 |
| orchestrate/SKILL.md (L25 建task判定) | 改为引用 C2 判定表, 消除与 flow 冲突 | C2 |
| apply/SKILL.md (维度表) | 维度行措辞对齐 C1/C4 | C1 C4 |
| scripts/trellisx-finish.py (docstring) | 边界注释对齐 C4 | C4 |

## 兼容性 / 回滚

- 纯文档/骨架文本改动, 无脚本逻辑变更 (finish.py 仅改 docstring)。回滚 = `git revert` 对应 commit。
- 端到端验证不通过 → 回滚该 writer commit, 不影响其他互斥文件。
