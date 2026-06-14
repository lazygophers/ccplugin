# 开发工作流

---

## 核心原则

1. **先规划再编码** —— 动手前先想清楚要做什么
2. **规约靠注入而非记忆** —— 规范通过 hook/skill 注入, 不靠凭记忆回想
3. **一切持久化** —— 研究、决策、教训全部落文件; 对话会被压缩, 文件不会
4. **增量开发** —— 一次只做一个 task
5. **沉淀经验** —— 每个 task 结束后回顾, 把新知识写回 spec

---

## Trellis 系统

### 开发者身份

首次使用时初始化身份:

```bash
python3 ./.trellis/scripts/init_developer.py <your-name>
```

创建 `.trellis/.developer` (gitignored) + `.trellis/workspace/<your-name>/`。

### Spec 系统

`.trellis/spec/` 按 package 和 layer 组织编码规范。

- `.trellis/spec/<package>/<layer>/index.md` —— 入口, 含 **开发前检查清单** + **质量检查**。实际规范在它指向的 `.md` 文件里。
- `.trellis/spec/guides/index.md` —— 跨 package 的思考指南。

```bash
python3 ./.trellis/scripts/get_context.py --mode packages   # list packages / layers
```

**何时更新 spec**: 发现新模式/约定 · 需固化的 bug 修复预防 · 新技术决策。

### Task 系统

每个 task 在 `.trellis/tasks/{MM-DD-name}/` 下有独立目录, 包含 `task.json`、`prd.md`、可选 `design.md`、可选 `implement.md`、可选 `research/`, 以及给支持 sub-agent 平台用的上下文清单 (`implement.jsonl`、`check.jsonl`)。

```bash
# Task lifecycle
python3 ./.trellis/scripts/task.py create "<title>" [--slug <name>] [--parent <dir>]
python3 ./.trellis/scripts/task.py start <name>          # set active task (session-scoped when available)
python3 ./.trellis/scripts/task.py current --source      # show active task and source
python3 ./.trellis/scripts/task.py finish                # clear active task (triggers after_finish hooks)
python3 ./.trellis/scripts/task.py archive <name>        # move to archive/{year-month}/
python3 ./.trellis/scripts/task.py list [--mine] [--status <s>]
python3 ./.trellis/scripts/task.py list-archive

# Code-spec context (injected into implement/check agents via JSONL).
# `implement.jsonl` / `check.jsonl` are seeded on `task create` for sub-agent-capable
# platforms; the AI curates real spec + research entries during planning when needed.
python3 ./.trellis/scripts/task.py add-context <name> <action> <file> <reason>
python3 ./.trellis/scripts/task.py list-context <name> [action]
python3 ./.trellis/scripts/task.py validate <name>

# Task metadata
python3 ./.trellis/scripts/task.py set-branch <name> <branch>
python3 ./.trellis/scripts/task.py set-base-branch <name> <branch>    # PR target
python3 ./.trellis/scripts/task.py set-scope <name> <scope>

# Hierarchy (parent/child)
python3 ./.trellis/scripts/task.py add-subtask <parent> <child>
python3 ./.trellis/scripts/task.py remove-subtask <parent> <child>

# PR creation
python3 ./.trellis/scripts/task.py create-pr [name] [--dry-run]
```

> 运行 `python3 ./.trellis/scripts/task.py --help` 查看权威、最新的命令列表。

**当前 task 机制**: `task.py create` 创建 task 目录, 并在会话身份可用时自动设置每会话的活动 task 指针, 使 planning breadcrumb 立即触发。`task.py start` 写入同一指针 (若已设置则幂等), 并把 `task.json.status` 从 `planning` 翻为 `in_progress`。状态存储在 `.trellis/.runtime/sessions/` 下。若 hook 输入、`TRELLIS_CONTEXT_ID` 或平台原生会话环境变量均无法提供 context key, 则没有活动 task, `task.py start` 失败并给出会话身份提示。`task.py finish` 删除当前会话文件 (状态不变)。`task.py archive <task>` 写入 `status=completed`, 把目录移到 `archive/`, 并删除仍指向该归档 task 的所有 runtime 会话文件。

### Workspace 系统

记录每次 AI 会话以做跨会话追踪, 存于 `.trellis/workspace/<developer>/`。

- `journal-N.md` —— 会话日志。**每文件最多 2000 行**; 超出时自动创建新的 `journal-(N+1).md`。
- `index.md` —— 个人索引 (总会话数、最近活跃时间)。

```bash
python3 ./.trellis/scripts/add_session.py --title "Title" --commit "hash" --summary "Summary"
```

### 上下文脚本

```bash
python3 ./.trellis/scripts/get_context.py                            # full session runtime
python3 ./.trellis/scripts/get_context.py --mode packages            # available packages + spec layers
python3 ./.trellis/scripts/get_context.py --mode phase --step <X.Y>  # detailed guide for a workflow step
```

---

## Phase 索引

```
Phase 1: Plan    → 分类, 征得创建 task 同意, 然后写 planning 产物
Phase 2: Execute → 仅在 task status 为 in_progress 后实现
Phase 3: Finish  → 验证、更新 spec、提交、收尾
```

### 请求分流

- 简单对话或小任务: 仅询问本轮是否应创建 Trellis task。若用户说不, 本会话跳过 Trellis。
- 复杂任务: 询问是否可创建 Trellis task 并进入 planning。若用户说不, 不要做大范围 inline 实现, 而应解释、澄清范围或建议拆得更小。
- 用户批准创建 task 不等于批准开始实现。仍要先做 planning。

### Planning 产物

- `prd.md` —— 需求、约束、验收标准。不要在此放技术设计或执行清单。
- `design.md` —— 复杂任务的技术设计: 边界、契约、数据流、取舍、兼容性、上线/回滚形态。
- `implement.md` —— 复杂任务的执行计划: 有序清单、验证命令、评审关口、回滚点。
- `implement.jsonl` / `check.jsonl` —— 给 sub-agent 上下文用的 spec 与 research 清单。不替代 `implement.md`。
- 轻量任务可只有 PRD。复杂任务在 `task.py start` 前必须有 `prd.md`、`design.md` 和 `implement.md`。

### 父/子 Task 树

当一个用户请求包含多个可独立验收的交付时, 用 parent task。parent task 拥有源需求集、task 映射图、跨 child 的验收标准和最终集成评审; 通常不应作为实现目标, 除非它本身也有直接工作。

对于可独立 plan、implement、check、archive 的交付, 用 child task。父/子结构不是依赖系统: 若一个 child 须等另一个, 把该顺序写进 child 的 `prd.md` / `implement.md`, 并保持每个 child 的验收标准可测。

用 `task.py create "<title>" --slug <name> --parent <parent-dir>` 创建新 child。用 `task.py add-subtask <parent> <child>` 链接已有 task, 用 `task.py remove-subtask <parent> <child>` 解除误链。

[workflow-state:no_task]
当前无活动 task。先对本轮分类, 在创建任何 Trellis task 前征得创建同意。
简单对话 / 小任务: 仅询问本轮是否应创建 Trellis task。若用户说不, 本会话跳过 Trellis。
复杂任务: 询问用户是否可创建 Trellis task 并进入 planning 阶段。若用户说不, 则解释、澄清范围或建议拆得更小。
<!-- trellisx:start:no_task -->
trellisx 规约 (强化上方原生判定, 不替换): 本项目愿景 = 除极简任务外, 一律走 Trellis task 执行。
- 涉及代码改动 / 多步骤 / 跨文件 的请求 → **默认创建 task** (不是"倾向建", 是默认就建; 仅用户明确拒绝才 inline)。建议直接用 AskUserQuestion 征得同意并进入 planning, 而非自行 inline。
- 边界模糊 (拿不准该不该建, 或 simple 还是 complex) → **MUST 主动用 AskUserQuestion 问用户** "本轮是否创建 Trellis task?", 禁默认跳过 / 禁自行替用户决定。
- 仅极简任务 (纯问答 / 查询 / 单行琐改 / 纯解释说明) 可不建。
- 判断"新建 task"还是"并入现有 task"时, 读 `.trellis/task.md` 看板对照现有任务 (id/名称/描述/状态) 辅助判断。
原生的「先分类 + 征得同意才建」不变 — 但默认倾向从"可建可不建"上调为"默认建, 除非极简或用户拒绝"。
<!-- trellisx:end:no_task -->
[/workflow-state:no_task]

### Phase 1: Plan
- 1.0 创建 task `[required · once]` (仅在征得创建同意后)
- 1.1 需求探索 `[required · repeatable]` (`prd.md`; 复杂任务还需 `design.md` + `implement.md`)
- 1.2 研究 `[optional · repeatable]`
- 1.3 配置上下文 `[conditional · once]` — Claude Code
- 1.4 激活 task `[required · once]` (评审关口, 然后 `task.py start`; status → in_progress)
- 1.5 完成标准

[workflow-state:planning]
加载 `trellis-brainstorm`; 停留在 planning。
轻量: `prd.md` 即可。复杂: 完成 `prd.md`、`design.md` 和 `implement.md`; 在 `task.py start` 前请求评审。
多交付范围: 考虑 parent task 加可独立验收的 child tasks; 依赖必须写进 child 产物, 不靠树位置隐含。
Sub-agent 模式: start 前把 `implement.jsonl` 和 `check.jsonl` 整理为 spec/research 清单。
<!-- trellisx:start:planning -->
trellisx 规划规约 (启用判定跟随 trellis 原生 parent/child 语义, 不看数量):

判定: 本请求是否含**多个独立可验收交付** (各自可独立 plan/implement/check/archive)?
- **是 (多交付)** → 拆为 parent + child tasks (trellis 原生 `task.py create --parent`)。每个 child 独立 worktree; 无依赖的 child MUST 并行执行 (同一回复一次性派多 agent)。PRD MUST 含 mermaid 调度图显式标并行组 + 依赖箭头。child 间依赖写进 child 自己的 prd.md/implement.md (非树位置隐含)。
- **否 (单一交付)** → 轻量单 task inline, **不强制拆 subtask**。仍走单 worktree 隔离。

拆分目的 = 让独立可验收交付各自隔离 + 最大化并行, 缩短关键路径; 不是为凑数量。详见 trellisx-orchestrate skill。

task 创建后, 用 `trellisx-workspace` 及时更新 `.trellis/task.md` 看板表 (新增/更新该任务行)。
<!-- trellisx:end:planning -->
[/workflow-state:planning]

[workflow-state:planning-inline]
加载 `trellis-brainstorm`; 停留在 planning。
轻量: `prd.md` 即可。复杂: 完成 `prd.md`、`design.md` 和 `implement.md`; 在 `task.py start` 前请求评审。
多交付范围: 考虑 parent task 加可独立验收的 child tasks; 依赖必须写进 child 产物, 不靠树位置隐含。
Inline 模式: 跳过 jsonl 整理; Phase 2 经 `trellis-before-dev` 读产物/spec。
[/workflow-state:planning-inline]

### Phase 2: Execute
- 2.1 实现 `[required · repeatable]`
- 2.2 质量检查 `[required · repeatable]`
- 2.3 回滚 `[on demand]`

Sub-agent 派发协议: 每个派发 prompt 在角色专属指令之前, 以 `Active task: <task path from task.py current>` 开头。

[workflow-state:in_progress]
流程: `trellis-implement` -> `trellis-check` -> `trellis-update-spec` -> 提交 (Phase 3.4) -> `/trellis:finish-work`。
主会话默认: 派发 implement/check sub-agent。Sub-agent 自豁免: 若已作为 `trellis-implement` 运行, 不要再派 `trellis-implement` 或 `trellis-check`; 若已作为 `trellis-check` 运行, 不要再派 `trellis-check` 或 `trellis-implement`。派发仅限主会话。
派发 prompt 以 `Active task: <task path from task.py current>` 开头。读上下文: jsonl 条目 -> `prd.md` -> `design.md if present` -> `implement.md if present`。
<!-- trellisx:start:in_progress -->
⛔ trellisx 执行硬规 (本 task 必守, 违反即流程错误):

1. **强制 worktree** (两种模式都守): 本 task 全部源码改动 MUST 落在 worktree (git 根/子仓 .worktrees/<worktree>, trellis 生命周期 hook 已自动建)。**禁在主工作区写源码** — 写盘 file_path 必须是 worktree 路径。
2. **多交付并行模式** (本请求拆了 parent + child tasks): 每个 child MUST 派 sub-agent (isolation:worktree) 或 agent-team 成员执行, **main 禁直接写源码** (只拆分/派发/收集/合并/协调)。无依赖的 child MUST 在同一条回复里一次性发起多个 agent 调用 (真并行), 禁逐个串行派。严格按 PRD 调度图依赖 + 并行组执行, 禁跳步。
3. **单一交付轻量模式** (单 task 未拆 child): main 可在 worktree 内直接 edit 实施, 无需派 agent。仍守第 1 条 (写盘路径在 worktree)。
4. **自动闭环收尾 (check 通过后全自动推进, 不停在「提醒」)**: `trellis-check` 通过后, AI **自动执行整条收尾序列**, 不把收尾降级为"提醒用户运行 /finish-work" —— 收尾是 AI 的动作, 不是给用户的 TODO。自动序列: **Phase 3.4 提交** (保留原生「批量提交一次性确认」门: AI 出批量提交计划→用户一次确认→提交; 被拒退手动, 不绕过此门) → **`/trellis:finish-work`** (归档 task + 记录会话) → **`task.py archive`**。**禁只提醒不执行**; check 未过 → 修复重检, 禁跳 finish; 未 archive = 流程未闭环, 禁宣告 Done / 禁结束本轮。
   > 注: 收尾序列 AI 自动跑, 仅 3.4 提交保留用户一次确认 (尊重「禁主动 commit 等明确指令」)。其余步骤 (finish-work / archive / journal) 零额外询问, 自动完成。
5. **及时维护 task.md 看板**: start / 阶段推进 (exec→check→finish) / archive 后, MUST 用 `trellisx-workspace` 更新 `.trellis/task.md` 看板行 (状态/阶段/进度/worktree)。看板滞后于实际 = 流程缺陷。
6. 收每个 agent 返回立即回传用户进度; task archive 时 worktree 干净则自动销毁。
<!-- trellisx:end:in_progress -->
[/workflow-state:in_progress]

[workflow-state:in_progress-inline]
流程: `trellis-before-dev` -> 编辑 -> `trellis-check` -> 验证 -> `trellis-update-spec` -> 提交 (Phase 3.4) -> `/trellis:finish-work`。
inline 模式下不要派发 implement/check sub-agent。
读上下文: `prd.md` -> `design.md if present` -> `implement.md if present`, 加 skill 加载的相关 spec/research。
<!-- trellisx:start:in_progress_inline -->
trellisx (增量): inline 模式 main 直接 edit, 但源码目标路径必须在 worktree (.worktrees/<worktree>) 内。
<!-- trellisx:end:in_progress_inline -->
[/workflow-state:in_progress-inline]

### Phase 3: Finish
- 3.1 质量验证 `[required · repeatable]`
- 3.2 调试复盘 `[on demand]`
- 3.3 spec 更新 `[required · once]`
- 3.4 提交变更 `[required · once]`
- 3.5 收尾提醒

[workflow-state:completed]
代码已提交。运行 `/trellis:finish-work`; 若工作树脏, 先回到 Phase 3.4。
[/workflow-state:completed]

### 规则

1. 先确认你在哪个 Phase, 然后从该 Phase 的下一步继续
2. 每个 Phase 内按顺序执行步骤; `[required]` 步骤不可跳过
3. Phase 可回滚 (例如 Execute 暴露出 prd 缺陷 → 回到 Plan 修复, 再重新进入 Execute)
4. 标记 `[once]` 的步骤若产物已存在则跳过; 不要重跑
5. 产物存在与否决定下一步; 缺 `design.md` / `implement.md` 对轻量任务是合法的, 对复杂任务则是 planning 未完成

### 活动 Task 路由

当用户请求在活动 task 内匹配以下意图之一时, 先路由, 需要时再加载详细的 phase 步骤。

- 规划或需求不清 -> `trellis-brainstorm`。
- `in_progress` 实现/检查 -> 派发 `trellis-implement` / `trellis-check`。
- 反复调试 -> `trellis-break-loop`; spec 更新 -> `trellis-update-spec`。

### 护栏

- 批准创建 task 不等于批准实现; 实现要等产物评审后的 `task.py start`。
- 轻量任务 PRD-only 合法; 复杂任务需 `design.md` + `implement.md`。
- planning 必须持久化到 task 产物; 检查必须在报告完成前运行。

### 加载步骤详情

每一步运行此命令获取详细指导:

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
# e.g. python3 ./.trellis/scripts/get_context.py --mode phase --step 1.1
```

---

## Phase 1: Plan

目标: 对请求分类, 在需要 task 时征得创建同意, 并产出实现前所需的 planning 产物。

#### 1.0 创建 task `[required · once]`

仅在征得创建同意后再创建 task 目录。该命令将 status 设为 `planning`, 写入 `task.json`, 创建默认 `prd.md`, 并在会话身份可用时自动把新 task 设为目标:

```bash
python3 ./.trellis/scripts/task.py create "<task title>" --slug <name>
```

`--slug` 仅是人类可读名称。**不要**包含 `MM-DD-` 日期前缀; `task.py create` 会自动加该前缀。

对于 task 树, 先创建 parent task, 再用 `--parent <parent-dir>` 创建每个 child。不要因为有 child 就启动 parent; 启动拥有下一个可独立验收交付的那个 child。

此命令成功后, 每轮 breadcrumb 自动切换到 `[workflow-state:planning]`, 提示 AI 停留在 planning。

这里只运行 `create` —— 不要同时运行 `start`。`start` 会把 status 翻为 `in_progress`, 在 planning 产物评审前就把 breadcrumb 切到实现阶段。把 `start` 留到步骤 1.4。

当 `python3 ./.trellis/scripts/task.py current --source` 已指向某个 task 时跳过。

#### 1.1 需求探索 `[required · repeatable]`

加载 `trellis-brainstorm` skill, 按该 skill 指导与用户交互式探索需求。

brainstorm skill 会引导你:
- 一次只问一个问题
- 优先研究而非问用户
- 优先给出选项而非开放式提问
- 用户每次回答后立即更新 `prd.md`
- 当交付可独立验收时, 把大范围拆为 parent task 加 child tasks
- 让 `prd.md` 聚焦于需求与验收标准
- 对复杂任务, 在实现开始前产出 `design.md` 和 `implement.md`

考虑父/子拆分时:
- 当一个请求含多个可独立验收的交付时, 用 parent task。
- parent task 拥有源需求、child-task 映射、跨 child 验收标准和最终集成评审。
- child task 拥有可独立 plan、implement、check、archive 的实际交付。
- 父/子结构不是依赖系统。若 child B 依赖 child A, 把该顺序写进 child B 的 `prd.md` / `implement.md`。
- 启动拥有下一个交付的 child task。除非 parent 本身有直接实现工作, 否则不要启动 parent。

需求变化时随时回到此步骤, 修订相关产物。

#### 1.2 研究 `[optional · repeatable]`

研究可在需求探索期间任意时刻进行。它不局限于本地代码 —— 你可以用任何可用工具 (MCP servers、skills、web search 等) 查外部信息, 包括第三方库文档、行业实践、API 参考等。

派发 research sub-agent:

- **Agent type**: `trellis-research`
- **Task description**: Research <specific question>
- **Key requirement**: Research output MUST be persisted to `{TASK_DIR}/research/`

**研究产物约定**:
- 每个研究主题一个文件 (例如 `research/auth-library-comparison.md`)
- 把第三方库用法示例、API 参考、版本约束记入文件
- 记下你发现的相关 spec 文件路径以备后用

brainstorm 与研究可自由交错 —— 暂停去研究一个技术问题, 再回来与用户交谈。

**关键原则**: 研究产出必须写入文件, 不能只留在对话里。对话会被压缩; 文件不会。

#### 1.3 配置上下文 `[required · once]`

整理 `implement.jsonl` 和 `check.jsonl`, 让 Phase 2 的 sub-agent 拿到正确的 spec/research 上下文。这些文件在 `task create` 时已种入一行自描述的 `_example`; 你这里的任务是填入真实条目。

**位置**: `{TASK_DIR}/implement.jsonl` 和 `{TASK_DIR}/check.jsonl` (已存在)。

**格式**: 每行一个 JSON 对象 —— `{"file": "<path>", "reason": "<why>"}`。路径相对仓库根。

**应放入**:
- **Spec 文件** —— 与本 task 相关的 `.trellis/spec/<package>/<layer>/index.md` 及任何具体规范文件 (`error-handling.md`、`conventions.md` 等)
- **Research 文件** —— sub-agent 需要查阅的 `{TASK_DIR}/research/*.md`

**不应放入**:
- 代码文件 (`src/**`、`packages/**/*.ts` 等) —— 这些在实现时由 sub-agent 读取, 不在此预注册
- 你即将修改的文件 —— 同理

**两个文件的分工**:
- `implement.jsonl` → implement sub-agent 正确写代码所需的 spec + research
- `check.jsonl` → check sub-agent 所需的 spec (质量规范、检查约定, 需要时同样的 research)

这些清单不替代 `implement.md`。`implement.md` 是复杂任务的人类可读执行计划; jsonl 文件只列出要注入或加载的上下文文件。

**如何发现相关 spec**:

```bash
python3 ./.trellis/scripts/get_context.py --mode packages
```

列出每个 package 及其 spec layer 与路径。挑选匹配本 task 领域的条目。

**如何追加条目**:

直接在编辑器中编辑 jsonl 文件, 或使用:

```bash
python3 ./.trellis/scripts/task.py add-context "$TASK_DIR" implement "<path>" "<reason>"
python3 ./.trellis/scripts/task.py add-context "$TASK_DIR" check "<path>" "<reason>"
```

有真实条目后删除种子 `_example` 行 (可选 —— 消费方会自动跳过它)。

跳过条件: `implement.jsonl` 和 `check.jsonl` 已有 agent 整理的条目 (仅种子行不算)。

#### 1.4 激活 task `[required · once]`

产物评审后, 把 task status 翻为 `in_progress`:

```bash
python3 ./.trellis/scripts/task.py start <task-dir>
```

轻量任务有 `prd.md` 即可。复杂任务在 start 前必须存在并已评审 `prd.md`、`design.md` 和 `implement.md`。在支持 sub-agent 的平台上, 需要额外 spec 或 research 上下文时整理 jsonl 清单; 仅有种子的清单消费方可容忍。

此命令成功后, breadcrumb 自动切换到 `[workflow-state:in_progress]`, 随后进入 Phase 2 / 3。

若 `task.py start` 报会话身份错误 (hook 输入、`TRELLIS_CONTEXT_ID` 或平台原生会话环境均无 context key), 按错误提示设置会话身份后重试。

#### 1.5 完成标准

| 条件 | 必需 |
|------|:---:|
| `prd.md` 存在 | ✅ |
| 用户确认 task 应进入实现 | ✅ |
| 已运行 `task.py start` (status = in_progress) | ✅ |
| `research/` 有产物 (复杂任务) | 推荐 |
| `design.md` 存在 (复杂任务) | ✅ |
| `implement.md` 存在 (复杂任务) | ✅ |
| 需额外 spec 或 research 上下文时整理 `implement.jsonl` / `check.jsonl` | 推荐 |

---

## Phase 2: Execute

目标: 把已评审的 planning 产物转化为能通过质量检查的代码。

#### 2.1 实现 `[required · repeatable]`

派发 implement sub-agent:

- **Agent type**: `trellis-implement`
- **Task description**: Implement the reviewed task artifacts, consulting materials under `{TASK_DIR}/research/`; finish by running project lint and type-check
- **Dispatch prompt guard**: Tell the spawned agent it is already the `trellis-implement` sub-agent and must implement directly, not spawn another `trellis-implement` / `trellis-check`.

平台 hook/plugin 自动处理:
- 读取 `implement.jsonl`, 把引用的 spec/research 文件注入 agent prompt
- 注入 `prd.md`、`design.md` (若存在) 和 `implement.md` (若存在)

#### 2.2 质量检查 `[required · repeatable]`

派发 check sub-agent:

- **Agent type**: `trellis-check`
- **Task description**: Review all code changes against specs and task artifacts; fix any findings directly; ensure lint and type-check pass
- **Dispatch prompt guard**: Tell the spawned agent it is already the `trellis-check` sub-agent and must review/fix directly, not spawn another `trellis-check` / `trellis-implement`.

check agent 的职责:
- 对照 spec 审查代码变更
- 对照 `prd.md`、`design.md` (若存在) 和 `implement.md` (若存在) 审查代码变更
- 自动修复发现的问题
- 运行 lint 和 typecheck 验证

#### 2.3 回滚 `[on demand]`

- `check` 暴露出 prd 缺陷 → 回到 Phase 1, 修 `prd.md`, 然后重做 2.1
- 实现做错了 → 回退代码, 重做 2.1
- 需要更多研究 → 研究 (同 Phase 1.2), 把发现写入 `research/`

---

## Phase 3: Finish

目标: 确保代码质量、沉淀教训、记录工作。

#### 3.1 质量验证 `[required · repeatable]`

加载 `trellis-check` skill 做最终验证:
- spec 合规
- lint / type-check / tests
- 跨层一致性 (当变更跨层时)

若发现问题 → 修复 → 重新检查, 直到全绿。

#### 3.2 调试复盘 `[on demand]`

若本 task 涉及反复调试 (同一问题被多次修复), 加载 `trellis-break-loop` skill 以:
- 归类根因
- 解释早先修复为何失败
- 提出预防措施

目的是沉淀调试教训, 让同类问题不再复发。

#### 3.3 spec 更新 `[required · once]`

加载 `trellis-update-spec` skill, 评审本 task 是否产生了值得记录的新知识:
- 新发现的模式或约定
- 你踩过的坑
- 新技术决策

据此更新 `.trellis/spec/` 下的文档。即便结论是"无需更新", 也要走一遍判断。

#### 3.4 提交变更 `[required · once]`

AI 驱动对本 task 代码变更做批量提交, 使 `/finish-work` 之后能干净运行。目标: 先产出工作提交, 再让记账 (archive + journal) 提交落在其后 —— 绝不交错。

**逐步操作**:

1. **检查脏状态**:
   ```bash
   git status --porcelain
   ```
   快照每个脏路径。若工作树干净, 跳到 3.5。

2. **学习提交风格**, 从最近历史 (使草拟的消息融入风格):
   ```bash
   git log --oneline -5
   ```
   记下前缀约定 (`feat:` / `fix:` / `chore:` / `docs:` ...)、语言 (中文/English) 和长度风格。

3. **把脏文件分两组**:
   - **本会话 AI 编辑过** —— 你在本会话通过 Edit/Write/Bash 工具调用写/改过的文件。你清楚改了什么、为什么。
   - **不可识别** —— 本会话你没碰过的脏文件 (可能是用户手改、上次会话遗留的 WIP, 或无关工作)。不要悄悄纳入。

4. **草拟提交计划**。把 AI 编辑过的文件分组成逻辑提交 (每个连贯变更单元 1 个提交, 而非每文件 1 个提交)。每条: `<commit message>` + 文件列表。把不可识别文件单列在底部。

5. **一次性呈现计划, 请求一次性确认**。格式:
   ```
   Proposed commits (in order):
     1. <message>
        - <file>
        - <file>
     2. <message>
        - <file>

   Unrecognized dirty files (NOT in any commit — confirm include/exclude):
     - <file>
     - <file>

   Reply 'ok' / '行' to execute. Reply with edits, or '我自己来' / 'manual' to abort.
   ```

6. **确认后**: 按顺序对每批运行 `git add <files>` + `git commit -m "<msg>"`。不要 amend。不要 push。

7. **被拒时** (用户回复 "不行" / "我自己来" / "manual" / 任何对计划的反对): 停止。不要尝试第二套计划。用户会手动提交; 待其确认后跳到 3.5。

**规则**:
- 任何地方都不用 `git commit --amend` —— 三阶段三提交流程 (工作提交 → archive 提交 → journal 提交)。
- 此步骤绝不 push 到远端。
- 若用户想要不同的消息措辞但接受文件分组, 改消息并重新确认一次 —— 但若他们拒绝分组, 退出到手动模式。
- 批量计划是一次提示; 不要逐个提交地提示。

#### 3.5 收尾提醒

完成以上后, 提醒用户可运行 `/finish-work` 收尾 (归档 task、记录会话)。

---

## 定制 Trellis (面向 fork)

本节面向想修改 Trellis 工作流本身的开发者。所有定制都通过编辑本文件完成; 脚本只是解析器。

### 改变某步骤的含义

编辑上面 Phase 1 / 2 / 3 各节中对应步骤的 walkthrough 正文。关键不变量:
- 无活动 task 时必须先分流, 在创建 Trellis task 前征得创建同意。
- planning 必须区分轻量 PRD-only 任务与需要 `prd.md`、`design.md`、`implement.md` 才能 start 的复杂任务。
- 每条 required 执行路径都必须让 Phase 3.4 提交提醒在 `/trellis:finish-work` 之前可达。

所有 tag 块都在上面的 `## Phase 索引` 节, 紧跟在每个 phase 摘要之后:

| 范围 | 对应 tag |
|---|---|
| 无活动 task (Phase 1 之前) | `[workflow-state:no_task]` (在 Phase 索引 ASCII 图之后) |
| 整个 Phase 1 (task 已创建 → 准备实现) | `[workflow-state:planning]` (在 Phase 1 摘要之后) |
| inline Phase 1 (非 Claude Code 默认) | `[workflow-state:planning-inline]` |
| Phase 2 + Phase 3.1–3.4 (实现 + 检查 + 收尾) | `[workflow-state:in_progress]` (在 Phase 2 摘要之后) |
| inline Phase 2 + Phase 3.1–3.4 (非 Claude Code 默认) | `[workflow-state:in_progress-inline]` |
| Phase 3.5 之后 (已归档) | `[workflow-state:completed]` (在 Phase 3 摘要之后; **当前为 DEAD**) |

### 改变每轮提示文本

直接编辑对应 `[workflow-state:STATUS]` 块的正文。编辑后, 运行 `trellis update` (若你是模板维护者) 或重启你的 AI 会话 (若你在定制自己的项目) —— 无需改脚本。

### 添加自定义 status

添加一个新块:

```
[workflow-state:my-status]
your per-turn prompt text
[/workflow-state:my-status]
```

约束:
- STATUS 字符集: `[A-Za-z0-9_-]+` (允许下划线和连字符, 例如 `in-review`、`blocked-by-team`)
- 必须有一个生命周期 hook 把 `task.json.status` 写为你的自定义值, 否则该 tag 永不被读取
- 生命周期 hook 位于 `task.json.hooks.after_*`, 绑定到 `after_create / after_start / after_finish / after_archive` 之一

### 添加生命周期 hook

在你的 `task.json` 中加一个 `hooks` 字段:

```json
{
  "hooks": {
    "after_finish": [
      "your-script-or-command-here"
    ]
  }
}
```

支持的事件: `after_create / after_start / after_finish / after_archive`。注意 `after_finish` ≠ 状态变更 (它只清除活动 task 指针); "task 完成"通知用 `after_archive`。

### 完整契约

工作流状态机的运行时契约、所有 status writer 的位置、伪 status (`no_task` / `stale_<source_type>`)、hook 可达性矩阵及其他深层细节, 见:

- `.trellis/spec/cli/backend/workflow-state-contract.md` —— 运行时契约 + writer 表 + 测试不变量
- `.trellis/scripts/inject-workflow-state.py` —— 实际解析器 (只读 workflow.md, 无内嵌文本)
