# trellisx Skills 参考

7 个 skill。`trellisx-apply` 是核心改造入口, 其余是日常/编排/收尾工具。

| skill | 类型 | 一句话 |
| --- | --- | --- |
| [trellisx-apply](#trellisx-apply) | 改造 (主动, 一次性) | 把 5 维度规则注入项目 `.trellis/` |
| [trellisx-flow](#trellisx-flow) | 执行 (主动) | 强制以 task 闭环处理请求 |
| [trellisx-orchestrate](#trellisx-orchestrate) | 编排 (自动) | 编排 prd/design/implement/subtask |
| [trellisx-workspace](#trellisx-workspace) | 维护 (自动+主动) | 维护 task.md 看板 |
| [trellisx-spec](#trellisx-spec) | spec (主动) | 破坏式优化 .trellis/spec/ |
| [trellisx-cleanup](#trellisx-cleanup) | 收尾 (主动) | 批量清理全部已完成 task |
| [trellisx-grill](#trellisx-grill) | 审查 (主动) | 对抗式 stress-test 工件 |

---

## trellisx-apply

**核心改造 skill**。用户主动跑一次, 改造当前项目 `.trellis/`。

- **触发**: 用户说"改造/注入/apply trellisx"或在 trellis 项目想启用 trellisx 规则。
- **输入**: 当前 trellis 项目 (cwd 或 git 根含 `.trellis/`)。`arguments: '[范围 (目录 glob / 文件路径 / all), 缺省 = all]'`
- **流程**: 诊断 → 注入 plan → AskUserQuestion 审批 → 写盘 → 验证。幂等可重复跑。
- **注入 5 维度**: 强推 task / subtask 拆分 / worktree 隔离 (task 级) / 闭环收尾 / task.md 看板。详见 [architecture.md §apply 注入模型](architecture.md)。
- **写盘**: workflow.md (marker 幂等) + config.yaml hook + scripts/ (复制) + spec guide + finish-work command + .gitignore。
- **边界**: 绝不替换 trellis 原生文本, 仅末尾追加。`trellis update` 覆盖 workflow 后重跑恢复。
- **references**: `workflow-injection.md` (注入源, 28K) / `spec-injection.md` / `hook-injection.md` / `finishcmd-injection.md` / `agent-orchestration.md` / `diagnose.md` / `apply-verify.md`。

## trellisx-flow

**强制 task 闭环**。用户主动调, 把请求强制纳入 plan→exec→check→finish。

- **触发**: `/trellisx-flow <请求>`。**禁自动触发** (user-invocable)。
- **行为**: 自判新建 task / 并入现有 task → planning → exec (**main 调度**, 动态 DAG 派各 trellis-implement 各执行 1 subtask, 并发上限 2 完成即派) → check (派 trellis-check) → finish (AI 层 + git 层)。
- **入参**: `--no-worktree` (subagent 改主工作区, main 仍禁亲改) / 其他流程开关。
- **边界**: 是入口路由, 不直接写源码; 实质工作派 subagent。

## trellisx-orchestrate

**planning 编排**。自动触发 (planning 阶段)。

- **职责**: 6 步流程编排 PRD / design / implement / subtask 文件 + mermaid 调度图 + parent/child 拆分 + jsonl curate; subtask 文件 frontmatter 声明 `write-files` + `exec-scope`。
- **调度规则**: **main 是调度器** (动态 DAG 调度, 并发上限 2, 完成即派); trellis-implement 不调度不递归 (Recursion Guard)。详见 `scheduling.md`。
- **references**: `task-tree.md` (parent/child) / `layer-selection.md` (执行载体) / `task-lifecycle.md` / `subtask-file.md` / `prd-orchestration.md` / `design-orchestration.md` / `implement-orchestration.md` / `scheduling.md` (动态 DAG 调度) / `failure-recovery.md` / `progress-communication.md` / `five-elements.md` / `jsonl-curation.md` / `selfcheck.md` / `shared-resources.md`。
- **examples/**: 完整 OAuth2 登录场景 (prd/design/implement/subtask) 贯穿范例。

## trellisx-workspace

**task.md 看板维护**。

- **触发**: task 生命周期任一节点 (create/start/阶段推进/archive) 之后; 用户问"当前有哪些任务/进度"。
- **arguments**: `[show|update|sync|cleanup ...] [task id]`
  - `show` 查看看板 / `update <tid>` 改状态 (阶段细化) ·worktree / `sync <create|start|archive>` 从 task.json 同步 (hook 用) / `cleanup` 清理超 7 天已完成。
- **5 列看板**: ID / 名称 / 描述 / 状态 / worktree。状态列承载生命周期阶段 (规划中/实施中/检查中/收尾/已完成/已归档); hook sync 写基础态, AI update 细化阶段, 冲突时 hook 不覆 AI 细分。
- **铁规**: 一律经 `trellisx-taskmd.py`, 禁直接编辑 task.md。hook 维护确定性列, AI 细化状态 + worktree。
- **references**: `dimensions.md` (看板列 + Worktree↔Task 映射) / `maintenance.md` / `task-md-template.md`。

## trellisx-spec

**破坏式 spec 优化**。

- **触发**: 用户提 spec 初始化/优化/重写/收紧, 抱怨 spec 弱/不可执行, 任务收尾沉淀, 或"记不住/老忘/反复犯错"。
- **arguments**: `[scope]`
- **模式**: init (无 spec) / optimize (现有 spec 破坏式重构) / sediment (任务收尾沉淀增量)。
- **流程**: 诊断 (init 跳过) → 提案 → AskUserQuestion 强制审批 → 执行 + 同步 task manifest 引用清单。
- **铁规**: main 直接执行 (非 fork subagent, 因 subagent 不能走 AskUserQuestion)。严禁未确认改写。推荐前置 `/trellisx-grill` 审一轮。
- **references**: `diagnose.md` / `propose.md` / `approve.md` / `execute.md` / `sediment-mode.md` / `rewrite-style.md` / `init-mode.md` / `selfcheck.md`。

## trellisx-cleanup

**批量收尾全部已完成 task**。

- **触发**: 用户要"批量清理/一次性归档/收尾所有已完成任务/清理所有 worktree/清空看板已完成行"。单个 task 收尾用 finish。
- **arguments**: `[--apply] [--days N]` (缺省 dry-run; --apply 执行; --days N 看板清理阈值默认 0 全删)
- **三件事**: ① 清理所有已合并 worktree ② 归档所有已完成任务 ③ 清理 task.md 已完成行。
- **完成判定**: `completed ∪ merged` (并集)。当前 active task **永不纳入**。
- **护栏**: 强制 dry-run → AskUserQuestion → --apply 三段, 不可跳。worktree 销毁沿用安全判据 (脏/未合并自动保留, 禁丢提交)。

## trellisx-grill

**对抗式工件审查**。

- **触发**: 用户要"grill/审一下/stress-test/对抗审查/挑刺/红队"某 prd/design/implement/spec/subtask; planning→start 前最后一遍校对; spec 重构前先 grill。
- **arguments**: `[被审工件路径, 缺省 = active task 全部 planning 工件]`
- **立场**: 对抗非审批 (找不到盲点 ≠ 通过, 是 grill 失败); 只批注不改写 (改盘交 orchestrate/spec); 一次一问; codebase 优先 (能查的不问用户)。
- **骨架**: blindspots 9 轴 + 五要素浓缩 (token 生命周期 / 触发准确性 / 自举矛盾 / 诚实边界摘樱桃 等)。
- **源于**: grill-me (relentless interview) + 项目盲点实证。

## 调用决策树

```
想启用 trellisx 规则        → trellisx-apply (一次性)
请求想强制走 task 闭环      → /trellisx-flow <请求>
planning 阶段编排           → trellisx-orchestrate (自动)
task 生命周期同步看板       → trellisx-workspace (自动 + show)
spec 弱/不可执行/记不住     → trellisx-spec
多 task 完成堆积想统一收口  → trellisx-cleanup (--apply)
start 前想挑刺/红队         → trellisx-grill
```
