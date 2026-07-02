# apply 注入异步等待清单规范 + skill 表述重设

## Goal

把「异步等待 MUST 输出任务清单表格」规范经 **trellisx-apply** 注入目标项目 `.trellis/workflow.md`, 让跑过 apply 的项目 AI 每轮被动看见此规范 (借 trellis 原生 inject-workflow-state 每轮注入)。同时把 trellisx skill 层 (flow / progress-communication) 表格重设为 4 列 + 状态本地化, 两文件一致化。

## Background

- 上一 task (07-02-async-wait-task-table) 把「异步等待清单」规范加进 flow SKILL.md + progress-communication.md (5 列: subtask/状态/摘要/阻塞)。
- 但该规范**只在 skill 层**, **未注入 workflow.md** → 跑过 apply 的项目 AI 读 workflow.md 看不到。
- apply 现有注入点 0-3 (no_task/planning/in_progress/finish), 无异步等待清单维度。
- 本项目 .trellis/workflow.md 仍全英文 + Codex 残留 (未跑 apply 清理), 不在本任务双写范围 (apply 自己管)。

## Requirements

### R1 表格规范重设 (4 列)
- **列**: `id` · `状态` · `摘要` · `进度%`
- **状态取值** (3 态, writer 按目标语言生成):
  - 中文: 进行中 / 等待中 / 阻塞
  - 英文: in_flight / pending / blocked
- 进度% 基于完成 subtask ratio (如 60%), 无数据填 `-`
- 去 ETA 列 (数据来源不靠谱), 去阻塞列 (合并进摘要)

### R2 注入点 (apply 注入到 workflow.md)
- **注入点 2 (in_progress 块末尾)**: 主注入, marker `trellisx:start/end:async-wait-in-progress`
- **注入点 3 (finish 段, 限定)**: 仅"等 notification 才输出"语境 (workflow 异步跑等回调时), marker `trellisx:start/end:async-wait-finish`
- 复用现有 marker 幂等机制 (块末尾追加 / 替换不堆叠)

### R3 apply 维度新增
apply SKILL.md 注入维度表新增一行「异步等待清单」, 落地位置 = workflow.md 注入点 2+3。

### R4 apply reference 同步
- `workflow-injection.md`: 加注入点 2 (in_progress) 异步等待清单算法 + 注入点 3 (finish) 限定算法
- `apply-verify.md`: 加**结构指纹断言** (marker key + 表格列头指纹, 不依赖自然语言词, 跨语言稳)

### R5 skill 表述一致化
- `flow SKILL.md`: 表格范例改 4 列 (id/状态/摘要/进度%), 状态本地化说明
- `progress-communication.md` §异步等待清单格式: 改 4 列 + 状态本地化 (主源)
- 两文件一致: progress-comm 为 single source, flow 引用 (不重复模板)

## Acceptance Criteria

- [ ] flow SKILL.md 表格改 4 列 (id/状态/摘要/进度%), 状态本地化
- [ ] progress-communication.md §异步等待清单格式 改 4 列 + 状态本地化 (主源)
- [ ] flow 引用 progress-comm (不重复表格模板)
- [ ] apply SKILL.md 注入维度表加「异步等待清单」行
- [ ] workflow-injection.md 加注入点 2 (in_progress) + 注入点 3 (finish 限定) 算法
- [ ] apply-verify.md 加结构指纹断言 (marker + 列头指纹, 跨语言稳)
- [ ] `claude -p` 验证: AI 读改后 skill + apply reference 能输出符合 4 列规范的表格
- [ ] `claude -p` 验证: AI 读注入算法能说出注入点 2+3 + marker key
- [ ] 幂等: 同 marker key 重复跑替换不堆叠 (复用现有机制)
- [ ] scope 仅限上述 5 文件, 无蔓延

## Constraints

- 仅文档变更 (5 .md), 不动脚本/逻辑/不加 hook
- 状态词本地化但内部 scheduling.md 保持英文术语 (用户面向 vs 内部 DAG)
- apply reference 注入算法复用现有 marker 机制 (块末尾追加 / 幂等替换)
- 表格列头指纹断言用 marker key (如 `trellisx:start:async-wait-in-progress`) + 列结构 (4 列), 不 grep 自然语言词
- 中文表述沿用周边风格
