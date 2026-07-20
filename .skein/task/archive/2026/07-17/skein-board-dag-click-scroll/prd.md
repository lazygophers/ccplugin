# board task DAG 点击卡片右侧滚到位置 — PRD

## 目标
board 左侧 task DAG 点击 task 卡片节点, 右侧自动平滑滚到该 task 卡片所在位置, 不再跳首页。

## 根因
- skein.py:1432 `links = {t["id"]: f'#task-{t["id"]}' for t in tasks}` — DAG 节点 href 是 `#task-<id>` hash 锚点
- board.js:489 task 卡片有 `id="task-<id>"` 锚点 (存在)
- webapp 已从 hash 路由改 history API (recall: hash-to-history-api-pitfalls-00), `#task-*` hash 被 router 当无效路由 → 跳首页
- hash 锚点原生 `scrollIntoView` 被 SPA router 吞掉

## 修法
board.js bindContent 内拦截 DAG `<a href^="#task-">` click:
- `e.preventDefault()` 阻止默认 hash 跳转 (不走 router)
- 取 href 的 hash → `document.getElementById(hash.slice(1))` 找 task 卡片
- `el.scrollIntoView({behavior:'smooth', block:'start'})` 平滑滚到位置
- 卡片顶部有 sticky topbar, scrollIntoView 会被遮 → 加 scroll-margin-top (board.js:32 已有 `scroll-margin-top:16px`, 调大到 topbar 高度 ~60px)

## 边界
**内**: board.js bindContent 加 click 拦截 (DAG `<a>` href^="#task-"); scroll-margin-top 微调
**外**: skein.py links 不改 (仍 #task-<id>, 前端拦截即可); router 不改; task 卡片 id 不改

## 验收标准
- [ ] DAG 点击 task 节点 → 右侧平滑滚到该 task 卡片 (不跳首页)
- [ ] 滚动后卡片不被 sticky topbar 遮挡 (scroll-margin-top 足够)
- [ ] 非.task hash (如纯 #) 不受影响
- [ ] node --check board.js pass
- [ ] 无 console error

## 索引
- 任务/子任务/调度: task.json (`skein.py subtask list skein-board-dag-click-scroll`)
- 关联 recall: hash-to-history-api-pitfalls-00 (SPA hash 路由改 history API 后 hash 锚点失效)
