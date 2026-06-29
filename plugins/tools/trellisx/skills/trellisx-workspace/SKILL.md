---
name: trellisx-workspace
description: '维护 `.trellis/task.md` 任务看板 —— trellis 缺的跨任务总览。**一个表格, 一行一个任务**, 列为 id/名称/描述/状态/worktree (5 列; 状态列承载生命周期阶段: 规划中/实施中/检查中/收尾/已完成/已归档)。在 task create/start/阶段切换/archive 后**及时更新**对应行; 并**自动清理超 7 天的已完成行**防膨胀。保持看板与 task.json 实时一致'
when_to_use: '维护 / 创建 / 更新 `.trellis/task.md` 任务看板时; task 生命周期任一节点 (create/start/阶段推进/archive) 之后同步看板时; 用户问"当前有哪些任务 / 任务进度 / 任务看板"时。被 trellisx-flow 与 trellisx-apply 注入的流程引用'
user-invocable: true
argument-hint: '[show|update|sync|cleanup ...] [task id]'
arguments: '[操作 — show 查看看板 / update <tid> 改状态 (阶段细化) ·worktree / sync <create|start|archive> 从 task.json 同步 (hook 用) / cleanup 清理超 7 天已完成] [任务 id]'
---

# trellisx-workspace — `.trellis/task.md` 任务看板维护

trellis 原生有每任务 `task.json`, 但**无跨任务总览**。本 skill 维护 `.trellis/task.md` 作为人类可读的任务看板 —— **一个表格, 一行一个任务** (5 列: ID/名称/描述/状态/worktree), 并保证它随 task 生命周期**及时更新** (不是写一次就烂掉)。无活动详情块、无子任务树、无归档分区。

## 文件定位

- 路径: `.trellis/task.md` (仓库内, 随 git 版本化)
- 角色: 单表格任务看板, 每行一个 task (含已完成, 用状态列区分) + **唯一额外 section** `## Worktree ↔ Task 映射` (一对多: 一行一 worktree, 同 task 可多行; 见 `references/dimensions.md`)
- 数据源: `task.py list` / 各 task 的 `task.json` —— task.md 是其**人类可读投影**, 冲突时以 task.json 为准
- **维护者 (按列分工, 不冲突)**:
  - ① **trellis 生命周期 hook** (`trellisx-taskmd.py`, 由 trellisx-apply 注入 config.yaml): 自动维护**确定性列** (ID/名称/描述/状态基础态) + create/start/archive 时 upsert + archive 时**7 天清理**。这是硬保障, 不靠 AI 记。
  - ② **AI (本 skill)**: 细化**状态列** (阶段: 实施中→检查中→收尾) + worktree 路径, 在阶段推进时更新。
  - hook upsert 时保留 AI 列, AI 更新时保留 hook 列 —— 同行不同列, 互不覆盖。**冲突规则**: 若 AI 已写细分 (实施中/检查中/收尾) 且 task 仍 in_progress, hook sync 不覆 AI 细分。
  - 项目未跑 apply (无 hook) 时, AI 全列维护 (含清理)。

## 维护时机 (及时更新, 不可滞后)

**一律经 `.trellis/scripts/trellisx-taskmd.py` 脚本操作, 禁直接编辑 task.md 文件** (保证格式一致 + hook/AI 列分工不打架)。

> 🔴 **CHECKPOINT (每个生命周期节点后)**: create / start / 阶段推进 / archive 任一发生 → 立即 `update` 或 `sync` 对应行, 才算节点完成。**task.md 落后于 task.json = 看板失效**, 视为流程缺陷, 不准放任滞后到下一步。
>
> 🛑 **STOP — 删行前 (AI 手动 cleanup)**: AI 手动 `cleanup` 会**永久删除看板行**, 属破坏性操作。执行前 **MUST 经 AskUserQuestion 工具确认**删除范围 (列出将删的 tid + 天数阈值), 用户批准后才删。禁默认静默删除, 禁用"建议清理"软措辞替代确认。(hook 触发的 archive 内 7 天清理是确定性流程, 不走此门。)

| 触发 | 命令 (脚本) | 谁执行 |
| --- | --- | --- |
| `task.py create` | `taskmd.py sync create` | hook (after_create) 自动 |
| `task.py start` | `taskmd.py sync start` | hook (after_start) 自动 |
| 阶段推进 (实施→检查→收尾) | `taskmd.py update <tid> --status 检查中` | AI |
| worktree 建好 (主表列) | `taskmd.py update <tid> --worktree <路径>` | AI |
| **worktree 创建** (subagent isolation / 手动 git worktree add) | `taskmd.py map-add <worktree> <tid> [创建源]` | WorktreeCreate hook 自动按**当前活动 task** 登记 (无活动 task → `?`, 由 UserPromptSubmit 提醒补登) |
| **worktree 销毁** | `taskmd.py map-remove <worktree>` | hook (WorktreeRemove / archive) 自动 |
| 查映射 / 查归属 | `taskmd.py map-list` / `map-get <worktree>` | AI / 用户 |
| `task.py archive` | `taskmd.py sync archive` (含 7 天清理 + 清该 task 映射) | hook (after_archive) 自动 |
| 查看看板 / 某任务 | `taskmd.py show [tid]` | AI / 用户 |
| 格式校验 | `taskmd.py lint` (主表 5 列 / 映射区 3 列 / 状态 / ID 不重复) | AI (FileChanged hook 自动提醒) |
| 手动清理 | `taskmd.py cleanup [--days N]` | AI |

> 原则: task.md 落后于 task.json = 看板失效。hook 自动管确定性列, AI 在阶段推进时 `update` 状态细分 + worktree。
> 无 hook 的项目 (未跑 apply): AI 用 `sync create/start/archive` 手动触发同步 + `cleanup` 清理。

## 用法

1. **查看** — `python3 .trellis/scripts/trellisx-taskmd.py show [tid]`。
2. **细化状态 + worktree** (阶段推进) — `python3 .trellis/scripts/trellisx-taskmd.py update <tid> --status <检查中|收尾|实施中> --worktree <W>`。
3. **确定性列 + 清理** — 由 hook 的 `sync` 自动 (apply 已注册 config.yaml hooks); 无 hook 时 AI 显式调 `sync` / `cleanup`。
4. **worktree↔task 映射 (一对多)** — `map-add <worktree> <tid> [创建源]` 登记 (按规范化 abspath upsert, 同 task 可多 worktree 各占一行) / `map-remove <worktree>` 移除 / `map-get <worktree>` 查 (命中→打印 tid 退 0, 无→退 1) / `map-list` 列全部。`WorktreeCreate` hook 创建时按**当前活动 task** 自动登记 (无活动 task → `?`), `UserPromptSubmit` hook 对 `?`/缺登记提醒补全, `WorktreeRemove`/archive 自动清。
5. **规范校验** — `lint` 校验 task.md 是否符合格式规范 (主表 5 列 / 映射区 3 列 / 状态值合法 / ID 不重复); `FileChanged` hook 在 task.md 变更时自动跑, 不合规 → 提醒修。手动: `python3 .trellis/scripts/trellisx-taskmd.py lint`。

> 脚本是 task.md 唯一写入口。脚本不存在 (项目未跑 apply 复制脚本) → 提示用户先 `/trellisx-apply`, 或按 `references/` 模板临时手维护。

## 参考集

| 文件 | 用途 |
| --- | --- |
| `references/task-md-template.md` | task.md 单表格模板 (一行一任务) |
| `references/dimensions.md` | 表格各列字段定义、取值、来源、更新时机 |
| `references/maintenance.md` | 幂等更新算法 (按 id 定位表行, 从 task.json 同步, 不堆叠) |

## 反例黑名单 (禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 手改 task.md 文件 (绕过脚本) | hook/AI 列分工被打乱 + 格式漂移 | 一律经 `trellisx-taskmd.py` (show/update/sync/cleanup) |
| 2 | 节点完成不同步看板 | task.md 落后 task.json = 看板失效 | 每个生命周期节点后立即 update/sync (见 🔴 CHECKPOINT) |
| 3 | 拿 task.md 当真值源改它再回填 task.json | 投影反向污染真值 | task.json 是真值, 冲突时以它重建 task.md |
| 4 | AI 覆盖 hook 维护的确定性列 (ID/名称/描述/状态基础态) | 同行列分工冲突, 互相覆盖 | AI 只细化状态 (阶段: 检查中/收尾) + worktree, 保留 hook 列 (ID/名称/描述/状态基础态) |
| 5 | 加活动详情块 / 子任务树 / 归档分区 (**worktree↔task 映射区除外**) | 偏离"一表一行一任务"单表设计 | 单表格 + **唯一例外**: `## Worktree ↔ Task 映射` 区 (经 map-add/map-remove 维护) |
| 6 | 脚本缺失时硬编看板格式 | 无脚本手维护易格式不一 | 提示用户先 `/trellisx-apply` 复制脚本, 或按 `references/` 模板临时维护 |

## 边界

- 只维护 `.trellis/task.md`, 不改 task.json / workflow.md / 源码
- 与 trellis 原生不冲突: task.json 是真值, task.md 是投影; 二者不一致时以 task.json 重建 task.md
- 语言跟随设备/项目语言 (同 trellisx-apply i18n 立场)
