# 6 页数据流矩阵 (过程证据)

## 矩阵
| 页 | mount 拉数据 | WS 订阅 | 用户操作 → API |
|---|---|---|---|
| dashboard | GET /__skein__/dashboard (dashboard.js:183) | onLive → 重拉 dashboard (:213) | 无 (纯只读 KPI 墙) |
| board | GET /__skein__/data (board.js:613, board 全量 cards/overview/nodeVar/nodeCls) | onLive → refresh 重拉 data (:621) | 文档弹层 api.getJSON("/"+doc) 拉原始 md (board.js:545) |
| queue | GET /__skein__/queue (queue.js:187) | onLive → 重拉 queue (:224) | 无 (只读 readyTasks/readySubtasks/pendingQueue) |
| task | 有 id: GET /__skein__/task/{id} (task.js:398); 无 id: GET /__skein__/data 取 cards (:379) | onLive → 重拉 task/列表 (:499) | POST /__skein__/exec {cmd, id} runRead (task.js:475); copyId 前端 clipboard |
| spec | GET /__skein__/spec 树 (spec.js:248) | 无 (编辑态保守, spec.js 不挂 onLive) | GET /__skein__/spec/file?path= (:345); POST /__skein__/spec/save 经 diff 确认 (:426) |
| archive | GET /__skein__/archive (archive.js:84) | onLive → 重拉 archive (:126) | 无 (只读归档列表) |

## 顶栏全局
- 全局搜索: GET /__skein__/search?q= (app.js:70, 防抖 200ms), hit 跳 /task?id= (task/subtask), /spec, /dashboard。
- 配置模态: GET/POST /__skein__/config (config-modal.js, debounce 400ms 全量 10 键), 表单+YAML 双 Tab。
- 主题切换: app.js:87-123, localStorage skein-theme 持久化。

## dashboard 数据字段 (来自 _view_dashboard, skein.py:2857+)
- proj, taskCount, doneRate, activeCount, combinedPct, statusDist (task 级), subStatusDist (subtask 级)
- runningSubs, readySubs (subtask)
- readyTasks, toPlanTasks, activeTasks, checkTasks (task)

## queue 数据字段 (来自 _view_queue, skein.py:2923+)
- readyTasks, readySubtasks, pendingQueue

## task 详情字段 (来自 _view_task_detail, skein.py:2809+)
- task (task.json 全文), docs (prd/design/findings 原文), subtasks, contracts

## archive 字段 (来自 _view_archive_list, skein.py:2838+)
- [{id, name, status, desc, finished, archivedAt, subs}]

## search 字段 (来自 _view_search, skein.py:2979+)
- {query, hits: [{kind: task|subtask|spec|命令, id, name, snippet}]}
