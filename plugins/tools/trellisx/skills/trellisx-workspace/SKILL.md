---
name: trellisx-workspace
description: 维护 `.trellis/task.md` 任务看板 —— trellis 缺的跨任务总览。**一个表格, 一行一个任务**, 列为 id/名称/描述/状态/阶段/进度/worktree (状态/阶段中文显示)。在 task create/start/阶段切换/archive 后**及时更新**对应行; 并**自动清理超 7 天的已完成行**防膨胀。保持看板与 task.json 实时一致。
when_to_use: 维护 / 创建 / 更新 `.trellis/task.md` 任务看板时; task 生命周期任一节点 (create/start/阶段推进/archive) 之后同步看板时; 用户问"当前有哪些任务 / 任务进度 / 任务看板"时。被 trellisx-flow 与 trellisx-apply 注入的流程引用。
user-invocable: true
argument-hint: [show|update|sync|cleanup ...] [task id]
arguments: [操作 — show 查看看板 / update <tid> 改阶段·进度·worktree / sync <create|start|archive> 从 task.json 同步 (hook 用) / cleanup 清理超 7 天已完成] [任务 id]
---

# trellisx-workspace — `.trellis/task.md` 任务看板维护

trellis 原生有每任务 `task.json`, 但**无跨任务总览**。本 skill 维护 `.trellis/task.md` 作为人类可读的任务看板 —— **一个表格, 一行一个任务**, 并保证它随 task 生命周期**及时更新** (不是写一次就烂掉)。无活动详情块、无子任务树、无归档分区。

## 文件定位

- 路径: `.trellis/task.md` (仓库内, 随 git 版本化)
- 角色: 单表格任务看板, 每行一个 task (含已完成, 用状态列区分)
- 数据源: `task.py list` / 各 task 的 `task.json` —— task.md 是其**人类可读投影**, 冲突时以 task.json 为准
- **维护者 (按列分工, 不冲突)**:
  - ① **trellis 生命周期 hook** (`trellisx-taskmd.py`, 由 trellisx-apply 注入 config.yaml): 自动维护**确定性列** (ID/名称/描述/状态) + create/start/archive 时 upsert + archive 时**7 天清理**。这是硬保障, 不靠 AI 记。
  - ② **AI (本 skill)**: 维护**主观列** (阶段 实施↔检查 / 进度 / worktree 路径), 在阶段推进时更新。
  - hook upsert 时保留 AI 列, AI 更新时保留 hook 列 —— 同行不同列, 互不覆盖。
  - 项目未跑 apply (无 hook) 时, AI 全列维护 (含清理)。

## 维护时机 (及时更新, 不可滞后)

**一律经 `.trellis/scripts/trellisx-taskmd.py` 脚本操作, 禁直接编辑 task.md 文件** (保证格式一致 + hook/AI 列分工不打架)。

| 触发 | 命令 (脚本) | 谁执行 |
| --- | --- | --- |
| `task.py create` | `taskmd.py sync create` | hook (after_create) 自动 |
| `task.py start` | `taskmd.py sync start` | hook (after_start) 自动 |
| 阶段推进 (实施→检查→收尾) | `taskmd.py update <tid> --phase 检查 --progress 80%` | AI |
| worktree 建好 | `taskmd.py update <tid> --worktree <路径>` | AI |
| `task.py archive` | `taskmd.py sync archive` (含 7 天清理) | hook (after_archive) 自动 |
| 查看看板 / 某任务 | `taskmd.py show [tid]` | AI / 用户 |
| 手动清理 | `taskmd.py cleanup [--days N]` | AI |

> 原则: task.md 落后于 task.json = 看板失效。hook 自动管确定性列, AI 在阶段推进时 `update` 主观列。
> 无 hook 的项目 (未跑 apply): AI 用 `sync create/start/archive` 手动触发同步 + `cleanup` 清理。

## 用法

1. **查看** — `python3 .trellis/scripts/trellisx-taskmd.py show [tid]`。
2. **更新主观列** (阶段/进度/worktree) — `python3 .trellis/scripts/trellisx-taskmd.py update <tid> --phase <P> --progress <N> --worktree <W>`。
3. **确定性列 + 清理** — 由 hook 的 `sync` 自动 (apply 已注册 config.yaml hooks); 无 hook 时 AI 显式调 `sync` / `cleanup`。

> 脚本是 task.md 唯一写入口。脚本不存在 (项目未跑 apply 复制脚本) → 提示用户先 `/trellisx-apply`, 或按 `references/` 模板临时手维护。

## 参考集

| 文件 | 用途 |
| --- | --- |
| `references/task-md-template.md` | task.md 单表格模板 (一行一任务) |
| `references/dimensions.md` | 表格各列字段定义、取值、来源、更新时机 |
| `references/maintenance.md` | 幂等更新算法 (按 id 定位表行, 从 task.json 同步, 不堆叠) |

## 边界

- 只维护 `.trellis/task.md`, 不改 task.json / workflow.md / 源码
- 与 trellis 原生不冲突: task.json 是真值, task.md 是投影; 二者不一致时以 task.json 重建 task.md
- 语言跟随设备/项目语言 (同 trellisx-apply i18n 立场)
