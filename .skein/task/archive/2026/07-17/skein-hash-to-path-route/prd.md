# webapp hash 路由改 path 路由 — PRD

## 目标
`#/dashboard` `#/task/:id` 等 hash 路由 → `/dashboard` `/task?id=:id` 等 path (history API) 路由。URL 无 `#`, 可直链/刷新/前进后退。

## 边界
**内**: router.js 路由核心改 path+query; app.js/index.html/各页 href 同步; serve 加 SPA fallback
**外**: 页面内部逻辑不动; API 端点不动; 静态文档 `/task/<id>/prd.md` fetch 不动
**约束**: task id 用 query 参数 (`/task?id=`) 避路径段冲突; `/task` 裸路径与 StaticFiles mount 同路径靠 route 优先 + catch-all 兜底

## 验收标准
- [ ] 直访 `/dashboard` 出概览页 (非 404)
- [ ] 直访 `/task?id=<id>` 出该 task 详情
- [ ] 刷新任一路由页不 404 (SPA fallback 生效)
- [ ] 浏览器前进/后退按钮切页正常
- [ ] nav 高亮跟随当前 path
- [ ] `/task/<id>/prd.md` 静态文档仍可 fetch (doc.js 不破)
- [ ] grep webapp/src + index.html 无残留 `#/` href
- [ ] go() 编程式导航走 pushState (无 `#`)

## 方案

### webapp 层 (hash → path + query)
- `router.js`:
  - `parse()`: `location.hash` → `location.pathname` (首段 name) + `URLSearchParams(location.search).get("id")` (task id)
  - `hashchange` → `popstate`
  - `go()`: `location.hash = ...` → `history.pushState({}, "", path)`
  - 首屏: 空 pathname 落 DEFAULT (replaceState)
- `app.js:45-47`: `"#/task/"+enc(id)` → `"/task?id="+enc(id)`; `"#/spec"`→`"/spec"`; `"#/dashboard"`→`"/dashboard"`
- `index.html:15-20`: nav `href="#/dashboard"` → `href="/dashboard"` (6 个)
- pages href (8 处):
  - `queue.js:34,57,76`: `'#/task/'+enc(id)` → `'/task?id='+enc(id)`
  - `dashboard.js:126`(`#/queue`→`/queue`), `:131`(`#/task/`→`/task?id=`)
  - `task.js:43`(`#/`→`/`), `:154`(`#/task/`→`/task?id=`)
  - `archive.js:62`(`#/task/`→`/task?id=`)

### serve 层 (skein.py)
- SPA fallback: catch-all `@app.get("/{full_path:path}")` 回 index.html
- `/task` 裸路径优先 StaticFiles: 显式 `@app.get("/task")` + `@app.get("/task/")` 回 index (声明在 mount 前), 或测 catch-all 顺序 — 执行 agent 实测哪种生效

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (`skein.py subtask list skein-hash-to-path-route`)
