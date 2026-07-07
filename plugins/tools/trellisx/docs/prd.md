# trellisx 产品需求文档 (PRD)

> 版本: 1.0 · 2026-06 · status: active

## 1. 背景

Trellis 是一套任务编排框架 (task.py / prd / design / implement / check / jsonl / 生命周期 hook)。它解决了"任务拆分 + 产物落地", 但在实战中暴露五类缺口:

1. **不强制建 task** —— 简单请求 AI 直接 inline 做, 改动散落无追踪。
2. **无 subtask 编排** —— 多独立单元只能堆在一个 implement 里, 并行调度靠 AI 即兴。
3. **无 worktree 隔离** —— 多 task 并发改源码互相脏写, 主工作区污染。
4. **闭环不强制** —— plan/exec 后跳过 check/finish, 未 archive 就宣告 Done。
5. **无跨任务看板** —— 只有每任务 task.json, 缺人类可读的总览。

## 2. 问题陈述

早期 trellisx 用**外部 command hook 持续拦截/注入**补这五类缺口 —— 复杂、需 reload、易与其他 hook 冲突。需要一个**改造型**而非**运行时型**的方案: 跑一次把规则写进 `.trellis/` 自身, 让 trellis 原生机制接管。

## 3. 目标

### 3.1 核心目标

| # | 目标 | 衡量 |
| --- | --- | --- |
| G1 | 五维度规则内化进 `.trellis/` | apply 后 workflow.md / config.yaml / scripts / spec guides / commands 全部落盘且幂等可重跑 |
| G2 | 不依赖平台 hook 即跨平台生效 | 注入走 trellis 原生生命周期 hook, 非 Claude Code 专属 |
| G3 | 绝不替换 trellis 原生文本 | 仅末尾追加 (marker 幂等), 原生 no_task/Phase/check/finish/前缀不动 |
| G4 | 执行载体闭环可强制 | guard hook 在 trellis 项目内 block 未清理 worktree / 游离 worktree (两闸) |
| G5 | 概念正交清晰 | parent/child (任务级动态调度, 各 child 各 worktree) ≠ subtask (任务内动态调度, 共享 worktree); worktree 隔离单位 = task |

### 3.2 非目标

- **不取代 trellis**: task.py / add-subtask / implement / check / update-spec / jsonl / 生命周期 hook 全用 trellis 原生。
- **不硬强制建 task**: 强推 task 是 prompt 软约束, AI 仍有裁量; 不装 enforcement hook。
- **不内置运行时注入 hook**: trellisx 插件本身不在每个会话注入规则; 规则靠 apply 内化。
- **不支持非 trellis 项目**: guard 静默退出; apply 无 `.trellis/` 报错退出。

## 4. 目标用户

| 用户 | 场景 |
| --- | --- |
| Trellis 项目维护者 | 想给项目补 worktree 隔离 / subtask 编排 / 闭环 / 看板, 不想手写 hook |
| 多 task 并行开发者 | 受并发脏写 / 主工作区污染困扰, 需 task 级 worktree 隔离 |
| 团队技术负责人 | 想强制"未 archive 禁 Done / 完成即清理"的团队规约 |

## 5. 功能需求

### 5.1 trellisx-apply (核心改造)

**输入**: 当前 trellis 项目 (cwd 或 git 根含 `.trellis/`)。
**流程**: 诊断 → 注入 plan → AskUserQuestion 审批 → 写盘 → 验证。幂等可重复跑。

**注入五维度** (纯增量追加, 绝不替换原生):

| 维度 | 内容 | 落点 |
| --- | --- | --- |
| 强推 task | no_task 块: 除极简外默认建 task; 边界模糊 MUST 问用户 (软约束) | workflow.md `no_task` |
| subtask 拆分 | 按 trellis 原生 parent/child 语义判定 (多个独立可验收交付才拆, 不看数量) | workflow.md `planning` |
| worktree 隔离 (task 级) | 默认 1 task 1 worktree, subtask 共享 (无绑定), 多 worktree opt-in | workflow.md `in_progress` + config.yaml hook |
| 闭环收尾 | plan→exec→check→finish 必走完整, 未 archive 禁 Done (软约束) | workflow.md `in_progress` |
| task.md 看板 | hook 自动维护确定性列 + 7 天清理; AI 细化状态 + worktree | config.yaml hook + workflow marker |

**写盘清单**:
- `workflow.md`: 5 维度规则 (marker 幂等) + i18n 跟随设备语言 + 清理无效内容
- `.trellis/spec/guides/trellisx-worktree.md`: worktree 约定 (仅新增)
- `.trellis/config.yaml`: 生命周期 hooks (after_create/start/archive/finish)
- `.trellis/scripts/trellisx-*.py`: 从插件 `scripts/` 复制 (不内联抄写)
- `.claude/commands/trellis/finish-work.md`: 全链收尾注入 (无则 hook 路兜底)
- `<git根>/.gitignore`: 排除 `.worktrees/`

### 5.2 trellisx-add (只规划不执行)

用户主动调 (`/trellisx-add <请求>`), 把请求纳入 planning: 判新旧/并入 → `task.py create` → prd/design/implement, **停在 `task.py start` 之前** (task 留 planning 态, 禁 exec/check/finish)。**仅显式触发** (禁 model 自动)。planning 逻辑单一真值源 —— flow 与 go 均委托本 skill 或消费其产物, 不复制正文。参数: 无参 = 跑完 planning 阻塞交还控制; `--continue`/`--exec` = 不停返回产物路径 (flow 内部借 planning 用)。

### 5.2b trellisx-flow (强制 task 闭环)

用户主动调 (`/trellisx-flow <请求>`) **或 model 自动触发** (请求复杂/多步/跨文件), 强制以 task 闭环处理: 委托 `/trellisx-add --continue` 完成 planning → exec→check→finish。**双模触发** (显式 + 自动)。

### 5.2c /trellisx:go (command, 执行 pending)

批量执行所有 pending planning 态 task (消费 `/trellisx-add` 攒下的产物), 每个走 flow start→exec→check→finish 闭环。task 级 DAG 调度 (write-files/exec-scope 相交串行, 不相交并行, 并发上限 2 滚动)。空态提示"先 /trellisx-add", 不报错。`go` 禁做 planning。命名空间 slash 名 `/trellisx:go`。

### 5.3 trellisx-orchestrate (planning 编排)

编排 PRD/design/implement/subtask 文件 + mermaid 调度图; parent/child 拆分 (任务级动态调度, parent 是 child 级调度器, 各 child 各 worktree); jsonl curate。subtask 文件声明 `write-files` + `exec-scope`; **main 自动冲突检测** (写盘 glob 相交 + 执行作用域相交 + 显式依赖 → 依赖边) + **动态 DAG 调度** (并发上限 2, 完成即派, 见 `scheduling.md`); trellis-implement 不调度不递归 (Recursion Guard)。

### 5.4 trellisx-workspace (看板)

维护 `.trellis/task.md` 单表格任务看板 (hook 维护确定性列 + AI 细化状态/worktree, 经 `trellisx-taskmd.py` 唯一入口)。

### 5.5 trellisx-spec (破坏式 spec 优化, 主动化)

初始化/优化/重写 `.trellis/spec/`, 允许破坏式变更; 描述性条款 → 可机器验证的命令式契约 (MUST/禁/严禁)。main 直接执行 (非 fork subagent, 因 subagent 不能走 AskUserQuestion)。**spec 主动化 (软约束)**: planning 时自动加载相关 guide 注入上下文; finish 前自动判 sediment 需求 (有增量才沉淀, 无则跳过)。sediment ≠ cortex。

### 5.6 trellisx-cleanup (批量收尾)

一次清理/归档/收尾**全部**已完成 task (completed ∪ merged)。三段护栏: dry-run → AskUserQuestion → --apply。

### 5.7 trellisx-grill (对抗式审查, 贯穿 plan 前/中/后)

贯穿 plan 前/中/后全程的对抗式 stress-test prd/design/implement/spec/subtask, 帮用户确认/审查/拆解需求 (plan 前审方向, planning 中审拆解, start 前最后校对), 产弱点表不改写 (源于 grill-me)。

## 6. 约束

- **跨平台**: 注入走 trellis 原生 hook, 不绑 Claude Code; guard 仅 Claude Code 平台 hook。
- **幂等**: apply 可重跑, marker 定位追加块; `trellis update` 覆盖 workflow 后重跑恢复。
- **安全**: cleanup/finish 破坏性操作必走 dry-run + AskUserQuestion; worktree 销毁沿用 `merge-base --is-ancestor` 安全判据, 脏/未合并自动保留。
- **不丢提交**: finish 走 commit→merge --no-ff (子先主后)→销 worktree→archive; 冲突 abort + 报清单, 不强合。

## 7. 验收标准

| # | 验收 |
| --- | --- |
| AC1 | apply 在干净 trellis 项目跑一次, 五维度全部落盘, 重跑零 diff |
| AC2 | apply 后 workflow.md 原生文本零改动 (git diff 仅追加块) |
| AC3 | task.py start 后 worktree 自动建, archive 后自动销, 主工作区零改动 |
| AC4 | **main 动态 DAG 调度** subtask (并发上限 2, 完成即派下一个), 冲突 (写盘 glob 相交 / 执行作用域相交 / 显式依赖) 自动串行; 并行 trellis-implement 共享 task worktree 改不相交文件集无脏写 |
| AC5 | finish 走全链 (commit→merge→销→archive), 未 archive 禁 Done |
| AC6 | guard 在 trellis 项目 block 未清理 worktree / 游离 worktree (两闸); 非 trellis 项目静默退出 |
| AC7 | cleanup dry-run 报告准确, --apply 仅清 completed ∪ merged, active task 永不纳入 |
| AC8 | task.md 看板随生命周期及时更新, 落后于 task.json 视为缺陷 |

## 8. 演进方向

- packages 自动发现 (monorepo `trellisx-packages.py` discover/apply) —— 已实现, 待文档化推广。
- grill 集成轮 (darwin 实证: grill 出弱点喂优化器) —— 进行中。
- 多 worktree opt-in 的显式 CLI (当前靠 finish 映射合并各分支)。
