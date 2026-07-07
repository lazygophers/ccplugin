# trellisx

Trellis **增强改造工具**。跑一次 `trellisx-apply`, 把 trellisx 的预想 (强推 task / subtask 编排 / worktree 隔离 / plan→exec→check→finish 闭环 / task.md 看板) **内化进项目的 `.trellis/` 自身** —— 之后由 trellis 原生机制注入这些规则, 不靠 trellisx 运行时 hook。

## 定位

```
早期: trellisx = 外部一堆 command hook 持续拦截/注入 (复杂, 需 reload, 易冲突)
现在: trellisx = 改造工具, 跑一次写进 .trellis (规则内化, trellis 自身机制生效)
```

trellisx 插件本身**无运行时 hook**。自动化由 `trellisx-apply` 注入到 **trellis 原生 `.trellis/config.yaml` 生命周期 hook** (`after_create/start/archive/finish`) —— 不依赖 Claude Code 平台 hook, 跨平台生效。

## Skills (8) + 1 command

1. **`trellisx-apply`** (核心) — 用户主动跑一次, 改造当前项目 `.trellis/`:
   - `workflow.md`: 5 维度规则注入 (marker 幂等) + 全文 i18n 跟随设备语言 + 清理无效内容
   - `.trellis/spec/guides/trellisx-worktree.md`: worktree 约定 (仅新增, 不动现有 spec)
   - `.trellis/config.yaml`: 生命周期 hooks (after_create/start/archive)
   - `.trellis/scripts/trellisx-worktree.py` + `trellisx-taskmd.py` + `trellisx-finish.py` + 公共模块: 从插件 `scripts/` 复制
   - `.claude/commands/trellis/finish-work.md`: 全链收尾注入 (无则 hook 路兜底)
   - `<git根>/.gitignore`: 排除 `.worktrees/`
2. **`trellisx-add`** — 用户主动调 (`/trellisx-add <请求>`), **只规划不执行**: 判新旧/并入 → `task.py create` → planning (prd/design/implement), 停在 `task.py start` 之前, task 留 planning 态。**仅显式触发**。planning 逻辑单一真值源 (flow/go 均委托或消费)。无参阻塞交还控制, `--continue` 不停返回产物 (flow 内部借用)。
3. **`trellisx-flow`** — 用户主动调 (`/trellisx-flow <请求>`) **或 model 自动触发** (请求复杂/多步/跨文件), 强制以 task 闭环处理: 委托 add 完成 planning → exec→check→finish。**双模** (显式 + 自动)。
4. **`trellisx-orchestrate`** — planning 编排 PRD/design/implement/subtask 文件 + mermaid 调度图。
5. **`trellisx-workspace`** — 维护 `.trellis/task.md` 单表格任务看板 (经 `trellisx-taskmd.py` 脚本)。
6. **`trellisx-spec`** — spec 破坏式优化 (增量捕获走 trellis 原生 trellis-update-spec)。**main 直接执行, 非 fork subagent** (subagent 不能走 AskUserQuestion 审批门)。
7. **`trellisx-cleanup`** — 批量收尾**全部**已完成 task (completed ∪ merged): dry-run → AskUserQuestion → --apply 三段护栏。
8. **`trellisx-grill`** — 对抗式工件审查: 写盘/`task.py start`/spec 重构前, 逐分支 stress-test prd/design/implement/spec, 产弱点表不改写 (源于 grill-me)。路由到 orchestrate/spec 改盘。

**Command**: `/trellisx:go [task-id...]` — 批量执行所有 pending planning 态 task (消费 `/trellisx-add` 产物), 每个走 flow start→exec→check→finish 闭环; task 级 DAG 调度 (冲突串行/不冲突并行/并发上限 2 滚动); 空态提示"先 /trellisx-add", 不报错。

## 脚本 (插件 scripts/, 统一管理)

| 脚本 | 职责 | 调用 |
| --- | --- | --- |
| `trellisx-worktree.py` | 3 布局自适应 worktree 建/销 (同级 git / 微服务 sparse / 多子仓) | config.yaml `after_start/archive` |
| `trellisx-finish.py` | 收尾 **git 层** (确定性脚本): commit→merge --no-ff (子先主后)→销 worktree→archive; 冲突 abort+报清单。**收尾 AI 层 (脚本做不到): finish 前 TaskList 查悬挂 Workflow/agent 逐个 TaskStop 关; finish.py 只销 worktree, 不关 Workflow/Task** | config.yaml `after_finish` + 手动 CLI |
| `trellisx-taskmd.py` | task.md 看板唯一读写入口 (CLI: `sync`/`update`/`show`/`cleanup`/`map-*`/`lint`) | config.yaml `after_create/start/archive` + AI |
| `trellisx_wt.py` | worktree 路径/分支/命名单一真值模块 (worktree + finish 共用 import) | 被上述脚本 import |
| `trellisx-guard.py` | 平台 Stop hook: trellis 项目内两闸 block (未清理 worktree / 游离 worktree), 非 trellis 静默 | Claude Code 平台 hook |
| `trellisx-packages.py` | monorepo 包自动发现写 `config.yaml` `packages:` (apply 一次性, 非 hook) | apply 内调 |
| `trellisx-cleanup.py` | 批量收尾全部已完成 task (completed ∪ merged), 三段护栏 | 手动 CLI |

apply 把脚本从插件 `scripts/` **复制**到用户 `.trellis/scripts/`, 不内联抄写。

## 注入维度 (5; 纯增量追加, 绝不替换原生)

| 维度 | 内容 | 落点 |
| --- | --- | --- |
| 强推 task | no_task 块: 除极简外默认建 task; 边界模糊 MUST 问用户 (软约束) | workflow.md `no_task` |
| subtask 拆分 | 按 trellis 原生 parent/child 语义判定 (多个独立可验收交付才拆, 不看数量) | workflow.md `planning` |
| worktree 隔离 (task 级) | **执行载体 = subagent 编排 (默认), 默认 1 task 1 worktree** —— task exec 默认由 **main 调度** → 派各 `trellis-implement` 各执行 1 subtask (动态 DAG 并发上限 2 完成即派), subtask **共享 task worktree** (subtask 与 worktree 无绑定, 不传 `isolation:worktree`; trellis-implement 不调度不递归, Recursion Guard)。**Workflow 仅特别复杂 task (大规模 fan-out / 仓库级 / ≥5 同类文件 / 500+ 文件迁移) 用户显式同意才启**, 普通 task 不用。隔离单位 = **task** (防并发多 task 互相冲突): task.py start 自动建本 task 的 `<git根>/.worktrees/<name>`, archive 销毁。默认一 task 一 worktree; 多 worktree 属 opt-in (非自动, 非由 subtask 冲突触发, finish 合并各分支) | workflow.md `in_progress` + config.yaml hook |
| 闭环收尾 | plan→exec→check→finish 必走完整, 未 archive 禁宣告 Done (软约束) | workflow.md `in_progress` |
| task.md 看板 | hook 自动维护确定性列 + 7 天清理; AI 细化状态 + worktree | config.yaml hook + workflow marker |

**绝不替换原生文本**: no_task 原生分类+征同意 / Phase 流程 / check / finish / 前缀 — 仅末尾追加 trellisx 内容。

> 力度边界: 强推 task 与闭环是**纯 prompt 软约束** (AI 仍有裁量), 不装平台 enforcement hook。需硬强制者自配。

## 与 trellis 融合 (非取代)

| 能力 | 用谁 |
| --- | --- |
| task.py / add-subtask / implement / check / update-spec / jsonl / 生命周期 hook | trellis 原生 |
| worktree 隔离 + subtask 编排 + 闭环 + task.md 看板 + 破坏式 spec | trellisx (补 trellis 缺的) |

## 用法

- **改造项目**: 在 trellis 项目内运行 `/trellisx-apply` → 诊断 → 注入 plan → AskUserQuestion 审批 → 写盘 → 验证。幂等可重复跑。`trellis update` 覆盖 workflow 后重跑恢复。
- **只规划不执行**: `/trellisx-add <请求>` 纳入 planning 停在 start 前, 审完规划再执行。
- **强制走 task**: `/trellisx-flow <请求>` 把请求强制纳入 task 闭环 (显式; 复杂请求 model 亦自动触发)。
- **执行规划好的 pending**: `/trellisx:go` 批量执行所有 planning 态 task (add 攒下的)。
- **finish 清理 (收尾两层)**: 顺序 **先 AI 层后 git 层** —— ⓪ AI 层: 收尾前 TaskList 查本 task 名下悬挂 Workflow/后台 agent, 逐个 TaskStop 关; ① git 层: `trellisx-finish.py` 跑 commit→merge→销 worktree→archive。脚本只销 worktree (git), 关闭 Workflow/Task 是 AI 层职责, 脚本做不到。
- **查看任务**: `python3 .trellis/scripts/trellisx-taskmd.py show`。

## 安装

通过 ccplugin-market 安装。
