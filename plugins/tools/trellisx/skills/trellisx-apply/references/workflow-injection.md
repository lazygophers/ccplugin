# workflow.md 注入 (结果导向, 行为闭环为准)

把 **强推 task** + **subtask 拆分** + **worktree 隔离** + **闭环收尾** + **task.md 看板维护** 五个维度注入 `.trellis/workflow.md`。trellis 原生 `inject-workflow-state` hook 每轮读这些块, 注入内容随之生效。

## 核心原则: 约束 RESULT 非 HOW

✅ 允许任意注入方式: 在原生内容**之后追加** marker (默认, 最稳), 或为达预期**替换/重构原生文本** (no_task 措辞、Phase 流程、finish 段)。**不再禁替换。**

⛔ 唯一硬门 = writer 写盘自验的行为闭环验证 (见下方「验证: 行为闭环」):
- ① 五维 marker/规约生效
- ② create→planning→worktree→execute→check→finish 闭环无断点
- ③ **trellis 原生 task 创建触发仍生效** —— 改写 no_task 后产物 MUST 仍引导"建 task" (措辞可变, 创建路径不可断)

> 默认仍优先「块末尾追加」(改动面最小、最易幂等); 仅当达标必须重构原生时才改写。marker 包裹保幂等不变。

> 教训: 早期版本重写 no_task + Phase 流程, 导致 trellis 原生 task 创建不再触发。**真坑是功能失效 (建 task 路径断), 不是动了原生文本。** 所以验收看行为不看"是否动原生": 改写 no_task 措辞 OK, 改没了"建 task"路径 → ✗ 回滚。

### 失败处理: 行为闭环验证 ✗

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 行为断言③报「task 创建触发失效」(改写切断建 task 路径) | 修订 no_task 注入, 补回"建 task"引导措辞, 重验 | `git stash pop` 回滚全部 apply 变更, 0 改动退出并报告用户 |
| 行为断言②报「闭环断点」(某 status/环节缺) | 按注入算法补缺失环节 marker, 重验 | 同上回滚, 报「流程未闭环: <缺失环节>」 |
| workflow-state 标签起止数不配对 | 定位串位 marker, 删除重注 (按下方注入算法重跑) | 同上回滚, 报「注入破坏标签结构」 |
| task.py current 注入后报错 | diff 对比注入前后, 修复破坏 trellis 解析的改动 | 同上回滚, 报「注入破坏 trellis 解析」 |

## i18n: 全部注入产物统一目标语言 (含翻译原生)

**目标语言由 `plan-diagnose` 统一确定一次** (综合 `$LANG` locale + 项目 CLAUDE.md/README 主语言 + 会话语言), 传给所有 writer; 不各 writer 各判, 防分裂。apply 完成后**所有注入产物的叙述文本必须同为目标语言**, 不只 workflow.md:

| 产物 | 谁写 | 语言要求 |
| --- | --- | --- |
| workflow.md 全文叙述 (含原生) | write-workflow | 全译为目标语言 |
| spec/guides/trellisx-worktree.md | write-spec | 目标语言写 (frontmatter key 留英文) |
| config.yaml 的 trellisx 注释行 (`# [trellisx] ...`) | write-hook | 目标语言 |
| 注入 snippet (no_task/planning/in_progress/finish_force) | write-workflow | 目标语言 |
| finish-work.md 注入步骤说明 | write-finishcmd | 目标语言 |

**全文档翻译** (write-workflow 执行; workflow 主语言 ≠ 目标语言时):
1. `plan-diagnose` 已定目标语言 (trellis init 默认英文; 设备/项目中文 → 目标中文)
2. 逐段翻译 workflow.md 的**叙述/说明文本**为目标语言
3. **保留原样不译** (机器标识, 译了 trellis 解析会坏):
   - workflow-state 标签 `[workflow-state:no_task]` 等 / trellisx marker
   - `task.py create/start/...` 命令 + 参数 / 文件路径 / 代码块内容
   - frontmatter key / 平台名 **仅 `Claude Code`** (其他平台名不保留, 清理段整删)
   - **脚本源码** (`.trellis/scripts/*.py`) 沿用原语言 (工具产物, 不在 i18n 范围)
4. trellisx 注入 snippet 本身也用目标语言写

> 验证: `verify-workflow` 断言注入产物语言一致 —— trellisx marker 块内无与目标语言相反的大段文字 (目标 zh 时块内须含 CJK; 中英混杂 = ✗)。

> 注: 翻译会改 trellis 原生 workflow 文本。`trellis update` 用英文模板覆盖后, 重跑 apply 恢复翻译。这是 trellis 模板机制的固有取舍。

## 清理无效内容 (plan-workflow 一并做)

trellis workflow.md 含大量**模板内部说明注释** (给维护者看, 对 AI 执行无价值, 占 context), 如:
```
<!-- Per-turn breadcrumb: shown while status='in_progress' when codex.dispatch_mode=inline. ... -->
<!-- Codex-only opt-in alternate to [workflow-state:in_progress]. ... -->
```

apply 优化时移除这些无效注释:

```python
# 移除所有 HTML 注释, 但保留 trellisx 功能 marker
import re
s = read(".trellis/workflow.md")
def keep(m):
    return m.group(0) if "trellisx:start:" in m.group(0) or "trellisx:end:" in m.group(0) else ""
s = re.sub(r"<!--.*?-->", keep, s, flags=re.DOTALL)
# 清理移除后留下的多余空行 (连续 >2 空行压成 1)
s = re.sub(r"\n{3,}", "\n\n", s)
write(".trellis/workflow.md", s)
```

**保留**: `<!-- trellisx:start:X -->` / `<!-- trellisx:end:X -->` (功能 marker)。
**移除**: 其余所有 `<!-- ... -->` (trellis 模板说明)。

### ② 删除非 Claude Code 平台描述 (不只收敛枚举, 是删干净)

本插件**仅服务 Claude Code**。trellis workflow 为多平台通用, 含大量其他 agent (Codex / Cursor / Gemini / OpenCode / Kiro / Qoder / Copilot / Droid / Windsurf / Antigravity / Kilo / Pi) 的描述、专属调度段、平台枚举 —— 对 Claude Code 用户是噪音, 占 context, 且会误导。apply **MUST 整段删除**这些非 Claude Code 平台内容 (而非保留着"收敛"):

- **平台枚举** → 只留 `Claude Code`: `[Claude Code, Cursor, OpenCode, Codex, Kiro, Gemini, Qoder, ...]` → `Claude Code`
- **其他 agent 专属段整删**: 如 `Codex (dispatch behavior)` / `codex.dispatch_mode` / `class-2 Codex/Copilot/Gemini/Qoder` / `fork_turns` / codex inline 模式描述 / `[workflow-state:in_progress-inline]` 块 等 —— **整体删除**, 不保留。
- **跨平台限定语删除**: "applies to all platforms, including ..." → 删限定, 仅留 Claude Code sub-agent 规则。
- **仅保留** Claude Code 生态名 (Claude Code / sub-agent / Task / skill / hook) + trellis 通用机制名 (task.py / workflow-state / Phase)。

> 判定: 任何提到非 Claude Code agent/平台的描述 = 删。删后是一份**纯 Claude Code** 的 workflow。

> 注: 同 i18n 翻译, 清理改 trellis 原生 workflow。trellis update 还原后重跑 apply。

## 注入机制 (marker 幂等)

```
<!-- trellisx:start:<key> -->
<内容>
<!-- trellisx:end:<key> -->
```
重复跑: 同 key marker → 替换内容; 无 → 在锚点块**末尾**追加 (原生内容之后)。

## 注入点 0: `[workflow-state:no_task]` 注入强推 task

**愿景: 除极简任务外一律走 Trellis task; 不确定就问用户。** 默认在 no_task 原生「分类 + 征得同意」之后追加 (最稳); 也可重构原生措辞, **但产物 MUST 仍保留"建 task"创建路径** (行为断言③)。把"可建可不建"调为"默认建, 除非极简"。

```
<!-- trellisx:start:no_task -->
trellisx 规约 (强化原生判定, 不切断建 task 路径): 本项目愿景 = 除极简任务外, 一律走 Trellis task 执行。

**作用域边界 — 何时建 task (workflow 四规范的触发前提)**:

| 特征 | 判定 |
| --- | --- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task |
| 单文件单处改, ≤20 行且位置已知 | 豁免 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤改 | **必建 task** |
| 需外部调研 (库选型/方案对比) 或产出文档交付 | **必建 task** (调研为 research subtask) |
| 边界模糊 | **MUST AskUserQuestion 由用户裁定** |

**无 task → 不进 workflow → 四规范豁免**。Planning 阶段也不进 workflow: brainstorm 主线由 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research 并行, 但设计决策由 main 汇总裁定。

- 表中"必建 task"的请求 → **默认创建 task** (不是"倾向建", 是默认就建; 仅用户明确拒绝才 inline)。建议直接用 AskUserQuestion 征得同意并进入 planning, 而非自行 inline。
- "边界模糊"行 → **MUST 主动用 AskUserQuestion 问用户** "本轮是否创建 Trellis task?", 禁默认跳过 / 禁自行替用户决定。
- 判断"新建 task"还是"并入现有 task"时, 读 `.trellis/task.md` 看板对照现有任务 (id/名称/描述/状态) 辅助判断。
原生的「先分类 + 征得同意才建」不变 — 但默认倾向从"可建可不建"上调为"默认建, 除非极简或用户拒绝"。
<!-- trellisx:end:no_task -->
```

## 注入点 1: `[workflow-state:planning]` 块末尾追加 subtask

**判定标准 = trellis 原生 parent/child 语义, 不看数量。** 启用拆分的开关是「本请求是否含**多个独立可验收交付** (independently verifiable deliverables)」—— 与 trellis workflow.md 原生 parent/child 判据一致, 不再用「subtask 数量 ≥2」一刀切。

```
<!-- trellisx:start:planning -->
trellisx 规划规约 (启用判定跟随 trellis 原生 parent/child 语义, 不看数量):

⚙️ **规划同步前台 (交互式, 禁自行凭空设计)**: planning 含 `trellis-brainstorm` **逐问用户**的交互, subagent 不能与用户对话, 故 **planning 由 main 同步前台执行**, 不派 subagent。分工: **`trellis-brainstorm` 为主导** (main 同步逐问用户做需求探索 + 方案设计 + 边界, 产出 prd/design); **`trellisx-orchestrate` 仅管执行层编排** (实际执行的 subagent 职责划分、并行/依赖、资源互斥, 产出 implement.md), **不用它做需求/方案设计**。产物评审 (`AskUserQuestion`) 由 main 亲做。注: exec/check 等非交互实质工作走 subagent 执行 (异步与否按需自定, 不强制)。

判定: 本请求是否含**多个独立可验收交付** (各自可独立 plan/implement/check/archive)?
- **是 (多交付)** → 拆为 parent + child tasks (trellis 原生 `task.py create --parent`)。每个 child 独立 worktree; PRD MUST 含 mermaid 调度图显式标并行组 + 依赖箭头; child 间依赖写进 child 自己的 prd.md/implement.md (非树位置隐含)。**执行统一由 `trellis-implement` 入口调度** (main 派 trellis-implement, 由其对各 subtask 派专用 subagent 并行执行), main 不直接派 subtask agent。
- **否 (单一交付)** → 轻量单 task inline, **不强制拆 subtask**。仍走单 worktree 隔离。

拆分目的 = 让独立可验收交付各自隔离 + 最大化并行, 缩短关键路径; 不是为凑数量。详见 trellisx-orchestrate skill。

task 创建后, 用 `trellisx-workspace` 及时更新 `.trellis/task.md` 看板表 (新增/更新该任务行)。
<!-- trellisx:end:planning -->
```

## 注入点 2: `[workflow-state:in_progress]` 块末尾追加 worktree

```
<!-- trellisx:start:in_progress -->
⛔ trellisx 执行硬规 (本 task 必守, 违反即流程错误):

0. **实质工作走 subagent 执行 (最高优先级)**: **概念分清** —— **task** = 任务记录 (`task.py create/start/finish/archive` 脚本), **main 同步跑**; **实质工作** (改源码、跑 check) **由 subagent 执行**。main **禁直接落地实质工作** —— 一律派 subagent (`Agent` 工具); main 只做编排 + task.py 脚本同步调用 + 用户交互决策 (`AskUserQuestion` subagent 不能做) + 完成即时回传 + 看板维护。是否 `run_in_background` 异步 / 并行 **按需自定, 不强制** (用户需要异步会自处理, 只需确保走 subagent)。每个 dispatch prompt 须 6 字段自包含 (目标/已知含 `Active task:`/范围/输出/验收/失败处理)。commit→merge→archive 由 `task.py finish` + `after_finish` hook 自动 (见 #4), 非派 agent。**🔴🛑 "派 agent" = 真实调用 `Agent` 工具, 不是叙述 (最易踩)**: 每个派 agent 动作 MUST 在**同一回复**产生真实 `Agent` tool_use; **严禁本回复无 `Agent` 工具调用就回传"已派出/agent 在做"** —— 宣称 ≠ 调用 = 幻觉跳步; 同理 "已建 task/看板已登记/worktree 已建" 必须是真实跑过 `task.py`/`trellisx-workspace`/hook 的结果。回传前自检本回复确有对应 tool_use, 无则先调用再回传。
1. **task 在 worktree 内执行 (task 级隔离, 目的 = 防并发多个 task 互相冲突)**: 隔离单位是 **task, 不是单次写盘**。`task.py start` 后 trellis hook 自动建本 task 的 worktree (`<git根>/.worktrees/<name>`); 本 task 的全部执行 (trellis-implement 及其 subagent) 都**在这个 worktree 内进行**, 主工作区保持干净。**默认一个 task 一个 worktree** (绝大多数场景); **仅当** task 内有**会互相冲突**的并行 subtask 时, 才给这些 subtask 各开子 worktree (少数场景) —— 此时收尾经 task↔worktree 映射把各子分支先合并回主分支再 archive (`trellisx-finish.py` 已支持多 worktree 合并)。
   - **执行载体 = 独立 Workflow 编排 (1 task : 1 workflow : N worktree)**: 本 task 的 exec(+check) 用 **Workflow 工具**编排成**一个独立 workflow** (Claude Code; 1 task → 1 workflow); workflow 内 fan-out 的 agent 各**worktree 隔离** (默认共享 task worktree = 1; 冲突型并行 subtask 各开子 worktree → N, finish 合并各子分支)。**runtime 退化**: 无 Workflow 平台 → 退回派 subagent 流水线 (`Agent` + `isolation:worktree`); 须显式标注当前载体 (**Claude Code Workflow** / **其他平台 agent 流水线**)。worktree 隔离规则两种载体下都不变。
   - **生成的 Workflow 必守 trellisx 四规范** (有 task 且进入执行阶段时): ① **phases 细致标类型** —— `meta.phases` 逐项标 `title` + `detail`, 阶段类型取自 {research, design, implement, verify, finalize}, 用户一眼看出每 phase 干什么属什么类型。② **允许并行** —— 无依赖 phases / fan-out agent 用 `parallel()` 并发; 有前后序的用分层 `parallel()` 表达, 不留无谓串行。③ **失败自动重试** —— 单 step/agent 失败自动重试 ≤2 次, 不让整个 workflow 直接失败; 重试仍败才降级 (返回 null + 下游 `.filter(Boolean)` 跳过, 或转 manual Blocked)。④ **收尾无残留** —— finalize phase 强制 `task.py finish` (hook 触发 commit→merge→remove worktree→archive) + finish 前 AI 自查无悬挂 Workflow/agent (TaskList 查 / TaskStop 关)。worktree 未销 / Workflow 未关 = 未闭环, 禁宣告 Done。
   - **retry 两层, 各管一类失败** (规范③落地): **workflow 脚本内自动重试** (瞬时错误: 网络抖动/工具超时/index.lock) —— `agent_with_retry` 包装, 默认 2 次, 指数退避语义。**main 重派** (逻辑失败: 自验 ✗/产物不达标) —— 对齐 apply 修复循环, 同一 subtask 累计 ≤3 次, 第 4 次禁盲目重试, 回 planning 重拆。重试计数 per-agent; 全部重试耗尽 → 该 agent 返回 null, workflow 不崩, 收尾时该项标 Blocked 上报。
2. **实施派发模型 (main → trellis-implement → subagent, 同在 task worktree 内)**: 进入实施, main **派一个 `trellis-implement` 子代理**执行实施阶段, **main 禁直接派 subtask agent、禁直接写源码** (只派 implement/check + 进度回传 + 合并)。`trellis-implement` 读 `implement.md`, 在**本 task 的 worktree 内**对各 subtask 派 subagent 执行 (**默认共享 task worktree**, 文件集不相交即可并行); **仅当并行 subtask 会互相冲突时**才给它们各开 `isolation:worktree` 子 worktree (finish 经映射合并各子分支)。严格按 implement.md / PRD 调度图依赖 + 并行组执行 (是否并行/异步按需自定)。trellis-implement 收拢全部 subtask 产物 → 交 `trellis-check`。循环: planning → trellis-implement → trellis-check → finish。
3. **轻量模式** (单 subtask): main 仍**派 `trellis-implement`**, 由其在 task worktree 内**内联直做** (无需再派 subagent), 保持 planning → implement → check → finish 循环一致。**main 不绕过 implement 自己写源码** (仍守第 1 条: task 在 worktree 内执行)。
4. **强制自动收尾 (check 通过后跑收尾, 全链自动, 不停在「提醒」)**: `trellis-check` 通过后, AI **强制收尾**, **两路任选其一, 都做全链** (commit→merge→del worktree→archive): ① `python3 .trellis/scripts/task.py finish` → `after_finish` hook 自动跑 `trellisx-finish.py`; ② `/trellis:finish-work` → apply 已注入它**先跑 `trellisx-finish.py` 全链再 journal** (修原生 archive-direct 绕 merge 丢提交)。不把收尾降级为"提醒用户" —— **合并与 worktree 删除是必须的, 非可选**:
   ① **worktree 内提交** —— `git add -A` + `git commit` (缺省消息 `chore(task): <tid> 收尾提交`), 落到 `trellisx-<name>` 分支。
   ② **合并回主分支** —— `git merge --no-ff trellisx-<name>`; **合并冲突 → 脚本自动 `merge --abort` + 报冲突文件清单 + 非 0 退出**。hook 失败仅 WARN, `task.py finish` 仍返 0 → AI **MUST 检 finish 输出有无 `trellisx-finish` 冲突告警**, 有则停下转手动, 禁强解 / 禁当成功。**未合并就 archive = 分支被销毁丢提交** (见 `trellisx-worktree.py` 教训, 故脚本先合并)。
   ③ **archive** —— 链内 `task.py archive <tid>` 归档 + 触发 `after_archive` 销毁**已合并**的 worktree + 删分支。
   - **commit 强制 (owner 授权)**: 本项目 owner 已显式要求 trellisx 流程**强制提交收尾**, 脚本直接 commit 不逐次等确认。此为 owner 对自有注入流程的设计授权, 覆盖默认「禁主动 commit」。
   - **check 未过** → 修复重检, 禁跑 finish; **未 archive (worktree 仍在) = 流程未闭环, 禁宣告 Done / 禁结束本轮**。
   - 手动兜底: 链路异常 → 直接跑 `trellisx-finish.py [--task <tid>]` (幂等可重入)。
5. **及时维护 task.md 看板**: start / 阶段推进 (exec→check→finish) / archive 后, MUST 用 `trellisx-workspace` 更新 `.trellis/task.md` 看板行 (状态/阶段/进度/worktree)。看板滞后于实际 = 流程缺陷。
6. 收每个 agent 返回立即回传用户进度; task `finish`/`archive` 时由 after_finish/after_archive hook 销毁干净的 worktree。(注: 平台 `trellisx-guard` 的 **Stop hook 不自动销毁** —— 仅对「已合并回主分支但未清理」的 worktree **提醒 + block 结束**, 让你手动 `git worktree remove` 或 `task.py finish`; 连续 ≥3 次后降级为 systemMessage 不再阻断。)
7. **任务中途修正路由 (执行中收到用户新指令)**: 本 task 已在跑 (agent/member 已派发) 时收到新指令, coordinator 先判归属:
   - **属当前任务** (修正 / 补充 / 细化已派交付) → ⛔ 禁 main 自己直接改源码、禁开新 task。按序: ① 先改对应**真值文档** (`prd.md` / `design.md` / `implement.md` 受影响条款, 标锚点) → ② 对**仍在跑**的目标 agent/member 用 `SendMessage` 下发修正 (引用改后 PRD 锚点, 令其就地纠偏, 不等跑完返工)。**先改文档再通知** (PRD 是真值, agent 复读以对齐)。
   - **独立新任务** (与当前交付无关) → 走 no_task 强推 task (新建 / 排队), 不打断当前 agent。
   - **判不准** → 🔴 用 AskUserQuestion 让用户裁定「并入当前任务 / 另起新任务」, 禁擅自二选一。
   兜底: 目标 agent 已完成 / workflow 模式无法中途 SendMessage → 改在 check 阶段按新 PRD 纠正, 或停掉重派一个修正 agent; inline 单交付 (无 running agent) → main 改 PRD 后就地调整执行, 跳过 SendMessage。
<!-- trellisx:end:in_progress -->
```

## 注入点 4: finish 段强制化 (改写原生收尾提醒段)

> 定位 Phase 3 的**收尾提醒段** (原生 "收尾提醒" / 含 `/finish-work` 提醒的段落), **改写**为: 收尾触发 = 跑 `task.py finish`, **after_finish hook 自动**完成 commit→merge→archive→销 worktree。把「提醒用户可运行 /finish-work」升级为「跑 finish, hook 自动收尾」。改写原生在结果导向下本就允许; 此处特别提示是因 finish 段定位易误命中 (见反例: 用 `re.finditer` 取末个)。

定位原生收尾提醒段 (含 `finish-work` 的 `#### 3.x` 段), 用 marker 包裹**替换其正文** (幂等):

```
<!-- trellisx:start:finish_force -->
⛔ **强制自动收尾 (不是提醒)**: check 通过后, AI **必须**运行
`python3 .trellis/scripts/task.py finish` (或 `/trellis:finish-work`)。
`after_finish` hook **自动**执行: 提交 worktree → 合并 --no-ff 回主分支 → archive → 销毁 worktree。
**worktree 删除与合并是必须的, 非可选, 非「提醒用户去做」。**
- **收尾两层, 责任不同 (step⓪ AI 层先于 ① git 层)**:
  - **⓪ AI 层 (脚本做不到, 必须 AI 主动)**: 跑收尾脚本前, 先确认本 task 的 **Workflow / 后台 agent 任务已全部终止** —— 用 `TaskList` 查有无悬挂的后台 Workflow/agent (Claude Code Workflow 或退化的 agent 流水线), 有残留则 `TaskStop` 逐个关闭, 再跑 finish。**`trellisx-finish.py` 只销 worktree, 不关 Workflow/Task** —— 关闭悬挂任务是 AI 层职责, 脚本不代劳。
  - **① git 层 (确定性脚本 `trellisx-finish.py`)**: commit → merge --no-ff 各子分支 (子先主后) → 销毁 worktree → archive。冲突则 abort + 报清单, 不强解。
  - 顺序: 先 ⓪ AI 层清悬挂任务 → 再 ① git 层 finish。悬挂任务未清就收尾 = worktree 被合并/销毁时仍有进程在写 = 流程错误。
- 合并冲突 → 收尾脚本 abort + 报冲突 + 非 0 退出 (hook 失败仅 WARN, `task.py finish` 仍返 0)。
  AI **MUST 检 finish 输出有无 `trellisx-finish` 冲突告警**, 有则转手动解决, 禁强解 / 禁当成功。
- check 未过禁跑 finish; 未 archive (worktree 仍在) = 流程未闭环, 禁宣告 Done。
- commit 为 owner 授权的强制动作 (脚本直接提交); 需会话 journal 时用 `/trellis:finish-work` 入口。
- 手动兜底: 链路异常时可直接跑 `python3 .trellis/scripts/trellisx-finish.py [--task <tid>]` (幂等可重入)。
<!-- trellisx:end:finish_force -->
```

注入算法 (定位 + 幂等替换, 失败兜底):

```python
s = read(".trellis/workflow.md")
START, END = "<!-- trellisx:start:finish_force -->", "<!-- trellisx:end:finish_force -->"
block = f"{START}\n{finish_force_snippet}\n{END}"
if START in s:                                   # 已注入 → 替换 marker 内
    s = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, s, flags=re.DOTALL)
else:
    # 定位原生收尾段: 含 finish-work 的 #### 标题段 (i18n 无关, 匹配命令字串)
    # ⚠️ 必须取**最后一个**含 finish-work 的 #### 段, 不是第一个:
    #    Phase 3 里「提交段 (3.4)」正文常提及 `/finish-work` (如 "使 /finish-work 之后能干净运行"),
    #    排在「收尾段 (3.5)」之前。用 re.search 取首个会**误命中提交段** → 改坏提交步骤且收尾段没改。
    #    收尾段是 Phase 3 末尾步骤, finditer 左到右的最后一个匹配即收尾段。
    matches = list(re.finditer(
        r"(####[^\n]*\n(?:(?!\n####).)*?/?(?:trellis:)?finish-work(?:(?!\n####).)*)",
        s, re.DOTALL))
    m = matches[-1] if matches else None
    if m:                                        # 用 marker 块取代该段正文 (保留标题行)
        title = m.group(1).split("\n", 1)[0]
        s = s[:m.start(1)] + f"{title}\n\n{block}\n" + s[m.end(1):]
    # 定位不到 → 不强改 (in_progress 硬规 #4 已是权威覆盖), 跳过
write(".trellis/workflow.md", s)
```

> 兜底: 定位不到原生收尾段 (措辞被大改 / 已 i18n 到无 `finish-work` 字串) → **跳过本注入点**, 不强行改写。此时收尾仍由 config.yaml `after_finish` hook 自动保证 (跑 `task.py finish` 即触发), 且 in_progress 块硬规 #4 文字层亦覆盖, finish 行为仍强制。

## 注入点 5: 复制 `trellisx-finish.py` + `trellisx_wt.py` 公共模块

apply 执行时把插件 `scripts/trellisx-finish.py` **及其依赖** `scripts/trellisx_wt.py` 复制到目标项目 `.trellis/scripts/` (与 `trellisx-worktree.py` / `trellisx-taskmd.py` 同目录, 见 `hook-injection.md`)。`chmod +x` 脚本。`trellisx_wt.py` 是 worktree 路径/分支/命名单一真值, `trellisx-finish.py` 与 `trellisx-worktree.py` 都 `import trellisx_wt` —— **漏拷它两脚本 ImportError**。

## 注入算法

```python
content = read(".trellis/workflow.md")
INJECT = {  # 默认末尾追加 (最稳); 达标需要时可改写原生, 但产物须过行为闭环验证
    "no_task": no_task_snippet,
    "planning": planning_snippet,
    "in_progress": in_progress_snippet,
}
for tag, snippet in INJECT.items():
    key = tag.replace("-", "_")
    start, end = f"<!-- trellisx:start:{key} -->", f"<!-- trellisx:end:{key} -->"
    if start in content:                          # 已注入 -> 替换 marker 内
        content = re.sub(f"{start}.*?{end}", f"{start}\n{snippet}\n{end}", content, flags=re.DOTALL)
    else:                                          # 未注入 -> 在该 workflow-state 块原生内容之后插入
        m = re.search(rf"(\[workflow-state:{tag}\].*?)(\n\[/workflow-state:{tag}\])", content, re.DOTALL)
        if m:
            content = content[:m.end(1)] + f"\n{start}\n{snippet}\n{end}" + content[m.end(1):]
        # 块不存在 -> 跳过 (不强行创建, 不破坏原生)
write(".trellis/workflow.md", content)
```

## 验证: 行为闭环 (不看是否动原生, 看结果是否达标)

```bash
# 标签配对 (起始 = 结束数, 注入未破坏标签结构)
grep -c "\[workflow-state:" .trellis/workflow.md
grep -c "\[/workflow-state:" .trellis/workflow.md
# 断言③ trellis 原生 task 创建触发仍生效: no_task 块仍含"建 task"引导路径。
# 语言无关 (i18n 后变中文, 不死匹配英文): no_task 块含 task 创建语义 (task / 创建 / create / 建 任一关键词命中)
python3 - <<'EOF'
import re
s=open(".trellis/workflow.md").read()
m=re.search(r"\[workflow-state:no_task\](.*?)\[/workflow-state:no_task\]", s, re.DOTALL)
body=(m.group(1) if m else "").lower()
# 建 task 路径关键词 (中英 + trellis 命令), 命中 = 创建触发未被改写切断
hit = any(k in body for k in ["task", "创建", "建任务", "create"])
print(f"{'✓' if hit else '✗ 危险: no_task 不再引导建 task, 创建触发疑失效'} 断言③ task 创建路径在")
EOF
# 断言③补: task.py 创建流程脚本未坏
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "✓ task.py 解析 OK"
# 断言② 闭环链: 各 status + subtask→worktree→check→finish 环节都在 (详见 apply-verify.md §4b)
for st in no_task planning in_progress; do
  grep -q "\[workflow-state:$st\]" .trellis/workflow.md && echo "✓ $st" || echo "✗ $st 缺"
done
grep -q "worktree" .trellis/workflow.md && grep -qE "check" .trellis/workflow.md && grep -qE "finish|archive" .trellis/workflow.md && echo "✓ 闭环链 worktree→check→finish"
```

🔴 CHECKPOINT — 行为断言任一 ✗ (task 创建路径失效 / 闭环断点), 立即停止, 走「失败处理: 行为闭环验证 ✗」表回滚, 禁带病写盘。

## 行为闭环优先于文本保护

- **不再要求**原生文本一字不改: 为达预期可重构 no_task/Phase/finish 措辞与结构
- 唯一硬约束: 产物过行为闭环 —— 改写 no_task 后仍引导建 task (断言③), 五维生效 (断言①), create→…→finish 无断点 (断言②)
- workflow.md 被 trellis update 覆盖后, 重跑 apply 恢复注入 (幂等)
