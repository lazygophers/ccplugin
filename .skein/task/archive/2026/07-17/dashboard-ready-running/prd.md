# 概览页展示就绪/执行中列表 — PRD

## 目标
dashboard 概览页展示 4 类实时列表:
1. subtask 就绪 (pending + 依赖全 done, 可立即派)
2. subtask 进行中 (running)
3. task 就绪 (pending + 前置全 done, 可 start)
4. task 执行中 (active: 进行中/检查中)

## 现状
dashboard "队列·待处理项" section 只展示 pendingQueue 里 ready=true 的 subtask (就绪 subtask 前 6 个)。缺: subtask 进行中 / task 就绪 / task 执行中。

## 数据源
- 后端 `_dashboard()` (skein.py:1702) 当前返 pendingQueue (含 ready subtask), 不含 running subtask / ready task / active task
- `_queue()` 已有 readyTasks + readySubtasks 逻辑可复用
- 方案: `_dashboard()` 补 3 字段:
  - `runningSubs`: active task 内 SS_RUNNING subtask [{tid,sid,name,agent}]
  - `readyTasks`: pending + 前置全 done [{id,name,deps,spct}] (复用 _queue 逻辑)
  - `activeTasks`: status ACTIVE/CHECK task [{id,name,status,pct,subs:[done,run,pend,fail]}] (复用 _board_data cards)

## 范围
- 范围内: scripts/skein.py _dashboard() 补字段; src/pages/dashboard.js 加 3 section (subtask 进行中 / task 就绪 / task 执行中); dist 重建
- 范围外: _queue() / _board() / 其他 pages; KPI 指标墙不动
- 约束: 后端字段只加不删 (兼容); dashboard onLive 软刷覆盖新 section

## 验收
- [ ] dashboard 显示 4 区: 就绪 subtask (现有改造) / 进行中 subtask / 就绪 task / 执行中 task
- [ ] 后端 _dashboard 返 runningSubs + readyTasks + activeTasks
- [ ] 每项可点跳 /task?id=<tid>
- [ ] 空态: 各区无项时显示提示
- [ ] onLive 软刷含新 section
- [ ] ESM 过 / skein.py 语法过 / dist 重建

## 索引
- 任务: task.json
