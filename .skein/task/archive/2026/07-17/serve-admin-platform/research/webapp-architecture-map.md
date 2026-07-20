# skein serve webapp 架构地图 (现状勘察, 只读)

调研目标: 为「skein serve 多页管理平台重设计」摸清现有 webapp 架构。
勘察范围: skein 插件源码仓 `/Users/luoxin/persons/lyxamour/ccplugin/plugins/tools/skein/`。

## 关键发现: 存在两套 webapp

- **旧看板 `assets/board/`** — vanilla JS (`board-render.js` 等), 单页 shell.html, petite-vue 未用。仍作**回落**保留 (serve 首页 `webapp/index.html` 不存在时才出旧 shell, skein.py:1871-1872)。marketplace 缓存版 (`~/.claude/plugins/marketplaces/.../skein/assets/board/`) 只有这套 = 旧快照。
- **新工程化 webapp `assets/webapp/`** — petite-vue + Tailwind, **7 页 hash-router SPA**, 已入库并 merge 进 master (commit 76f64cf3「重设计 skein serve 为工程化多页面管理平台」+ 24499f05 预构建入库 + a65067d7 Pill nav + b60737e4 暗色模式)。**重设计主体已落地**, 本 task 属继续打磨/扩展。

以下所有路径均指源码仓 `/Users/luoxin/persons/lyxamour/ccplugin/plugins/tools/skein/`。

---

## 段 1 · serve 后端 (FastAPI)

入口链:
- `serve` 子命令注册: scripts/skein.py:2023 (argparse) → dispatch skein.py:2080 → `serve()` skein.py:1658。`view()` skein.py:1651 同走 `_run_server`。
- `_run_server()` skein.py:1727 起 uvicorn (127.0.0.1, `uvicorn.run("skein:_serve_app_factory", factory=True, reload=...)`, 见 1617 附近); `.board-server.lock` 去重 (skein.py:1543), 同项目只跑一个。
- 依赖: fastapi/uvicorn, 缺失兜底 pip 装 (`_serve_deps_present` / `_install_serve_deps` skein.py:1530-1535); 近期 commit 已改为预构建入库精简。
- app 工厂: `_build_serve_app()` skein.py:1797 (核心, 全部路由在此)。tty 区分: 手动跑印 URL/开浏览器, monitor 管道静默 (skein.py:1668)。

HTTP 路由 (skein.py:1857-1963):
- `GET /` `GET /task.html` → `_page()` 1869: `webapp/index.html` 存在则出新前端 (`_webapp_html` skein.py:1457), 否则回落旧 `_board_html`。
- `GET /__skein__/dashboard` 1887 → `_dashboard()`
- `GET /__skein__/queue` 1891 → `_queue()`
- `GET /__skein__/task/{tid}` 1895 → `_task_detail()` (404 若无)
- `GET /__skein__/spec` 1900 → `_spec_tree()`
- `GET /__skein__/spec/file?path=` 1904 → 单 spec 原文 (realpath 越界 403)
- `POST /__skein__/spec/save` 1913 → 写 spec (仅 .md, 越界拒) ← **唯一 spec 写接口**
- `POST /__skein__/exec` 1928 → 白名单命令执行 (见下)
- `GET /__skein__/archive` 1945 → `_archive_list()`
- `GET /__skein__/search?q=` 1949 → `_search()`
- `GET /__skein__/data` 1865 → `_board_data()` (旧看板数据, WS "data" 软刷用)
- `GET /__skein__/rev` 1861 轮询兜底; `GET <LOCK_ID_PATH>` 1857 身份探测
- `WS /__skein__/live` 1874 → 热重载: `_watch_loop` (skein.py:1638 附近) 每 500ms 比 asset_rev / data_rev, 资产变推 "reload"(整页), 仅数据变推 "data"(软刷)。
- 静态挂载 (skein.py:1953-1963): `/board`→assets/board, `/webapp` `/src` `/dist` `/vendor`→assets/webapp 各子目录 (check_dir=False 容错), `/task`→`.skein/task/` (规划文档 md 直出)。

exec 白名单 (`_exec_argv` skein.py:1605-1649): 严格 enum→固定 argv, 绝不 shell 拼串。只读: list/ready/pop/current/doctor/status/contract(仅查)/subtask-list; 安全写: create/subtask-add。子进程 `subprocess.run(cwd=board.root, timeout=60)` skein.py:1939。

## 段 2 · 前端结构 (assets/webapp/)

多页 SPA, hash 路由。目录:
- `index.html` (1.8K) — 顶栏 (SKEIN logo + 7 nav tab + 全局搜索 + 明暗 toggle) + `<main id="view">` 挂载点 + `<script type=module src=src/app.js>`。nav 7 tab: 概览/看板/队列/任务/规范/命令/归档 (index.html:14-20)。
- `src/app.js` (9.1K) — 引导: 载 petite-vue (vendored IIFE→全局 `window.PetiteVue`, app.js:12-18) + 接线全局搜索下拉 (防抖 200ms, app.js:21-80) + 明暗主题切换 (localStorage `skein-theme` + 系统跟随, app.js:86-122) + 流沙动效 (数字递增/入场/视口暂停 IntersectionObserver, app.js:124-191) + `live.start()` + `router.start({api,md})`。
- `src/router.js` (4.2K) — hash 路由核心。`ROUTES=[dashboard,board,queue,task,spec,commands,archive]` (router.js:18), 默认 dashboard。页面**懒加载** `import(./pages/<name>.js)` (router.js:65), 契约: 每 page `export function render(mount, params, ctx)`, ctx={api, md, onLive} (router.js:3-12)。竞态守卫 navToken (router.js:45); nav 高亮 highlightNav (router.js:81); 切页 teardown 退订 live (router.js:33)。未建页→"该页开发中"占位不报错。
- `src/lib/api.js` (44 行) — fetch 封装 (ApiError, no-store) + 各 endpoint 便捷函数 (dashboard/queue/task/spec/specFile/specSave/archive/search/data/exec)。BASE=`/__skein__`。
- `src/lib/live.js` (26 行) — WS `/__skein__/live` 客户端: "reload"整页刷, "data"→通知 `subscribe(cb)` 订阅者软刷; onopen 重连整页刷; file:// 直接退出。
- `src/lib/md.js` (92 行) — markdown 渲染/sanitize/mount (doc 展示用)。
- `src/pages/*.js` — 7 页**全部已建** (行数: board.js 663 / spec.js 191 / dashboard.js 159 / commands.js 152 / task.js 148 / queue.js 120 / archive.js 82)。petite-vue `window.PetiteVue.createApp().mount()`。

数据注入方式: **无首屏内联 payload 依赖** (index.html 无 PAYLOAD; 虽 `_webapp_html` skein.py:1457-1467 会填 PROJ/PAYLOAD/VER token, 但 index.html 当前模板未含 PAYLOAD 占位)。各页 render 时经 `ctx.api.*` fetch `/__skein__/*` 拿 JSON。VER token 用于 `dist/app.css?v=VER` 缓存击穿 (skein.py:1467)。

## 段 3 · 样式体系 (Tailwind + oklch 令牌)

- **构建**: `build-css.sh` (Tailwind standalone 二进制, `~/.cache/skein` 不入库) `src/input.css`→`dist/app.css` (20.3K, 已入库预构建, buildless 运行态)。`tailwind.config.js` content=index.html+src/**。
- **令牌系统** (src/input.css @layer base, :root skein.py 无关): seed (`--h:265 色相` `--c-accent:.16` `--h-accent:250`) + 明度锚点 (`--l-bg/-card/-fg/...`) → **oklch 派生**完整契约 (`--bg --card --fg --head --muted --brd --line --accent --accent2`)。input.css:15-42。
- **双外观**: 浅=晨曦 (:root 默认), 暗=夜空金沙 (`[data-theme=skein-dark]` 重写明度锚点+金调玻璃层, input.css:60-88) + `@media prefers-color-scheme` 自动跟随。切换纯走 `<html data-theme>` 变量交换, 无 Tailwind dark class。
- **status 色相** (语义固定跨主题): pending 蓝/active 橙/check 青/done 绿/failed 红 (`--h-pending:245` 等, input.css:22; `--st-*` 派生)。
- **玻璃流沙风格**: `--glass-bg/-brd/-shadow` (color-mix), body 三段径向渐变底纹 (input.css:89-96), 暗态金沙星点 (input.css:98-110)。`--radius:16px` `--font: system`。`--skein-gold:#FFD98A`。
- **Tailwind token 别名** (tailwind.config.js): 语义色 bg/card/fg/head/muted/brd/line/accent/accent2 + st.{pending..failed} 全是 CSS 变量薄别名; borderRadius/fontFamily 同。布局走 Tailwind utilities, `@layer components` 只给「质感+动效」(.card 玻璃卡等)。
- **顶栏组件** (input.css:182-219): `.nav` = Pill 分段控件 (glass 背景+blur, `[data-nav].active` 填 accent 胶囊 `color:var(--bg);background:var(--accent)`)。`.theme-toggle` 两键分段 (.on 走蓝/金渐变)。`.search-dropdown` 全局搜索下拉 (app.js 内联兜底样式 app.js:27-31)。

## 段 4 · 数据源清单 (逐项来源)

| 面板/数据 | 后端方法 (skein.py) | 底层数据源 |
|---|---|---|
| 概览统计 dashboard | `_dashboard` 1543 | `_board_data` overview + `_render_tasks` subtask 状态聚合 → 完成率/活跃数/状态分布/combinedPct/pendingQueue |
| 待执行队列 queue | `_queue` 1560 | `_all()` pending 且 deps 就绪的 task + `_active()`/`_ready()` 就绪 subtask + `_pending_queue` |
| 任务详情 task | `_task_detail` 1503 | `.skein/task/<id>/task.json` 全文 + prd.md/design.md/findings.md 原文 + subtasks + contracts; 缺失回落 archive |
| 规范树 spec | `_spec_tree` 1477 | `.skein/spec/{core,recall}/<类目>/*.md` (跳 index.md) |
| 单 spec 原文 | `_spec_resolve` 1492 + endpoint 1904 | `.skein/spec/` 下 md (realpath 越界守卫) |
| spec 保存 | endpoint 1913 | 写 `.skein/spec/` (仅 .md) |
| 归档 archive | `_archive_list` 1525 | `.skein/task/archive/<年>/<月-日>/<id>/task.json` |
| 搜索 search | `_search` 1576 | 跨 task/subtask/prd.md/spec md 子串匹配 |
| 命令执行 exec | `_exec_argv` 1605 | 白名单 subprocess 调 skein.py 自身 (list/ready/pop/status/create/subtask-add…) |
| 规划文档原文 | `/task` StaticFiles 1963 | `.skein/task/<id>/<f>.md` 直出 (md.js 渲染) |
| 热重载 | `_watch_loop` + `_asset_rev`/`_data_rev` | asset mtime (board+webapp 目录) / task.json rev |

task.json 唯一写入口 `_board_task` skein.py:1209 (变更即同步)。看板**不落盘**, 每请求实时从 task.json 渲染。

---

## 重设计可复用什么 / 需新建什么

**已全部具备, 重设计=在既有骨架上扩展/打磨, 非从零**:
- 复用: FastAPI serve 骨架 + 9 数据 endpoint + exec 白名单 + WS 热重载 (软刷/整页刷分级) + hash-router SPA 契约 (render/params/ctx) + api.js/live.js/md.js 三 lib + oklch 令牌+双外观+玻璃流沙样式体系 + Pill nav + 7 页全建。
- 可能需新建: 若加新页 → 加 `ROUTES` (router.js:18) + `pages/<name>.js` + nav tab (index.html) + 对应后端 endpoint + api.js 便捷函数 + exec 白名单项 (若涉写命令)。首屏内联 PAYLOAD 通道 (`_webapp_html` 已备 token 但 index.html 未用) 若要提速可接。
