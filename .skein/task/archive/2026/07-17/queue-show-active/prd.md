# /queue 展示进行中 — PRD

## 目标
/queue 页加"进行中"区段: 展示 active task (进行中/检查中) + running subtask。

## 背景
_queue (skein.py L1797-1817) 只返回 pendingQueue + readyTasks + readySubtasks。无 active/running 数据。_dashboard (L1784) 已有 activeTasks + runningSubs 数据结构可复用。

## 设计

### backend (_queue)
return dict 加:
- `activeTasks`: `[{"id","name","status","pct","sdone","stotal","elapsed"}]` (复用 _dashboard L1784-1787 逻辑, 从 data["cards"] 取 S_ACTIVE+S_CHECK)
- `runningSubs`: `[{"tid","sid","name","agent","elapsed"}]` (复用 _dashboard L1759-1770 逻辑)

### frontend (queue.js)
- 加进行中区段 (放 readyTasks 前, 进行中优先级最高)
- activeTasks: task 卡片 (id/名/状态 badge/pct 进度条/sdone/stotal/elapsed)
- runningSubs: subtask 列表 (tid/sid/名/agent/elapsed)
- 跳转: task → /task?id=, subtask → /task?id=<tid>

## 边界
- 范围内: _queue 加 activeTasks+runningSubs; queue.js 加区段
- 范围外: _dashboard (已有, 不动); pendingQueue/readyTasks/readySubtasks (不动)
- 约束: 复用 _dashboard 数据结构

## 验收
- [ ] _queue 返回 activeTasks + runningSubs
- [ ] queue.js 显示进行中区段
- [ ] 无 active 时区段隐藏或不报错
- [ ] ast.parse 过 + ESM 过
