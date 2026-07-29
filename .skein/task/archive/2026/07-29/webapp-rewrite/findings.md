# webapp-rewrite — 调研收敛

> 范围: `plugins/tools/skein/assets/webapp/` + `scripts/skein.py` serve 段 (L2075-2148, L3000-3267) + `docs/examples/index.html`。
> 重写决策 (grill 锁定, 不重问): htmx+原生 DOM 替 petite-vue, buildless, 后端 API+WS 也改, 双模主题, 6 页 IA 重设, 参 examples 海滩蓝金。

## 1. 前端架构现状

入口链 (全 file:line):
- `index.html:41` `<script type=module src="src/app.js">` → 引导。
- `src/app.js:13-19` 动态注入 `<script src="/vendor/petite-vue.js">` 挂全局 `window.PetiteVue` (IIFE 非 ESM, import 拿不到具名导出)。
- `src/app.js:194-202` boot 序: `loadPetiteVue → wireSearch → wireTheme → wireMotion → configModal.wire(api) → live.start() → router.start({api, md})`。
- `src/router.js:18-32` 6 route (`dashboard|board|queue|task|spec|archive`) + DEFAULT=`board`。**注意**: 路由用 **history API (pathname)** 不是 hash; `parse()` 解 `location.pathname` (单段) + `?id=` (task)。SPA 切页只换 `#view` 内容, 不整页刷。
- `src/router.js:67` 动态 `import(\`./pages/${name}.js\`)` → `mod.render(mount, params, ctx)`。未建页占位"该页开发中"不报错。

渲染范式 (混合, 重写关键风险):
- **board.js = 命令式 innerHTML** (注释 board.js:4-5 "沿用旧看板的命令式 innerHTML 渲染 + 忠实移植的像素级 dagHtml (Sugiyama), 不重写成 petite-vue 响应式")。无 PetiteVue。
- **dashboard / queue / task / spec / archive = petite-vue 响应式** (`window.PetiteVue.createApp(state).mount(mount)`), 但大量模板字符串内嵌 HTML (TPL 常量)。
- dagHtml (`src/dag.js`) 纯函数返回 HTML 字符串 (SVG Sugiyama 分层 + 并查集折叠已完成连通块, L38-53), 被 board/task 共用经 `setNodeMaps(varMap, clsMap)` 注入状态染色 (dag.js:8)。

状态管理:
- **无全局 store**。每页 render 闭包内自管局部 state。跨页通信用 history pathname + 顶栏全局搜索 (`app.js:22-81`, 防抖 200ms → `api.search` → 下拉, hit 跳 `/task?id=`)。
- 软刷模式 (core 规则 `frontend/soft-refresh-pattern`): `ctx.onLive(remountFn)` 订阅, router 切页自动退订 (router.js:62, cleanups[] L34-35)。

主题系统 (实际**仅 2 套**, 非 grill 所述"10 套"):
- `:root` (input.css:17-62) = skein-light "晨曦" 默认; `[data-theme="skein-dark"]` (input.css:66+) = "夜空金沙"。
- 令牌层: seed (`--h`, `--c-neutral`, `--c-accent`, `--h-accent`) + 明度锚点 (`--l-*`) → oklch 派生契约 (`--bg/--card/--fg/--head/--muted/--brd/--line/--accent/--accent2`), 状态色 `--st-pending/active/check/done/failed` 色相固定语义 (input.css:23-39)。
- 玻璃流沙层: `--skein-gold: #E8C264` + `--glass-bg/brd/brd-blue/inset-hi/shadow`, `--bar-track`, body 烘焙 radial-gradient 流沙底纹 (input.css:103-106 浅, 125-141 暗星点)。
- 切换: `app.js:87-95 applyTheme()` 写 `<html data-theme=...>`; localStorage `skein-theme` 持久化, 缺省系统跟随 (`prefers-color-scheme`)。
- `tailwind.config.js:14-37` Tailwind token = CSS 变量薄别名 (颜色/边框/圆角/字体), safelist 通用组件类免 purge (L11-13)。

各页 render 契约签名 (统一 `async render(mount, params, ctx)`, ctx={api, md, onLive}; 6/6 一致, 符合 core `[arch] SPA page 模块统一契约`):
| page | render 定义 | 拉数据 | 渲染范式 | onLive |
|---|---|---|---|---|
| dashboard | dashboard.js:177 | `api.dashboard()` :183 | PetiteVue | :213 |
| board | board.js:590 | `ctx.api.data()` :613 | **命令式 innerHTML** | :621 |
| queue | queue.js:179 | `api.queue()` :187 | PetiteVue | :224 |
| task | task.js:372 | `api.task(id)` :398 / 无 id 用 `api.data()` :379 | PetiteVue | :499 |
| spec | spec.js:244 | `api.spec()` :248 / `api.specFile()` :345 / `api.specSave()` :426 | PetiteVue | (无, 编辑态保守不软刷) |
| archive | archive.js:78 | `api.archive()` :84 | PetiteVue | :126 |

## 2. 后端 serve 现状

入口: `skein.py:2075 serve()` → `_run_server` (L2149) → uvicorn + reload, factory `_build_serve_app` (L2219) / `_serve_app_factory` (L3270)。app 构造在 `build_app()` (L3042-3267)。

HTTP 端点清单 (15 个 API/SPA + 5 静态 mount):
| method | path | handler | 入参 | 出参 |
|---|---|---|---|---|
| GET | `/__skein__/id` | :3119 | — | proj_id (纯文本, .skein 绝对路径) |
| GET | `/__skein__/rev` | :3123 | — | `{data_rev}.{asset_rev}` 纯文本 (轮询兜底) |
| GET | `/__skein__/data` | :3127 | — | `_board_data()` 看板全 JSON (cards/overview/nodeVar/nodeCls) |
| GET | `/` | :3131 | — | HTML (webapp index 或回落 board shell) |
| GET | `/__skein__/dashboard` | :3148 | — | `_dashboard()` (taskCount/doneRate/activeCount/combinedPct/statusDist/subStatusDist/runningSubs/readySubs/readyTasks/toPlanTasks/activeTasks/checkTasks) |
| GET | `/__skein__/queue` | :3152 | — | `_queue()` (readyTasks/readySubtasks/pendingQueue) |
| GET | `/__skein__/task/{tid}` | :3156 | tid path | `_task_detail()` (task/docs/subtasks/contracts) / 404 |
| GET | `/__skein__/spec` | :3161 | — | `_spec_tree()` {core,recall}×{cat:[file]} |
| GET | `/__skein__/spec/file?path=` | :3165 | path query | {path, content} / 403 越界 / 404 |
| POST | `/__skein__/spec/save` | :3174 | {path, content} | {ok, path} / 403/400 |
| POST | `/__skein__/exec` | :3189 | {cmd, ...args} | {ok, cmd, exit, stdout, stderr} / 403 白名单外 |
| GET | `/__skein__/config` | :3206 | — | `config()` 全键 (含 ENV override) |
| POST | `/__skein__/config` | :3210 | 全量 10 键 | {ok, config} / 400 |
| GET | `/__skein__/archive` | :3229 | — | `_archive_list()` [{id,name,status,desc,finished,archivedAt,subs}] |
| GET | `/__skein__/search?q=` | :3233 | q query | {query, hits:[{kind,id,name,snippet}]} |
| GET | `/task` | :3243 | — | HTML (SPA fallback) |
| GET | `/board` | :3247 | — | HTML (SPA fallback) |
| GET | `/{full_path:path}` | :3264 | — | HTML (SPA 兜底) |

静态 mount (声明顺序硬约束 — core `[arch] 路由声明在 mount 之前`, skein.py:3239-3266 已遵守):
- `/board` → `assets/board/` (StaticFiles) :3252
- `/webapp` → `_NoCacheStatic(webapp/)` :3255
- `/src` → no-cache :3256 ; `/dist` :3257 ; `/vendor` :3258 ; `/task` → `.skein/task` (规划文档 prd/design/findings.md 直出) :3261

WS 协议 (`/__skein__/live`, skein.py:3135-3145):
- 服务端 push, 客户端不发 (`ws.receive_text()` 阻塞保活)。
- **仅 2 个事件类型** (`_watch_loop` skein.py:3070-3088, 500ms 轮询 rev):
  - `"reload"` — 资产 rev 变 (`_asset_rev` = board 静态 + webapp 源 + dist/css mtime, L2109-2113) → 整页 `location.reload()`。
  - `"data"` — 数据 rev 变 (`_data_rev` = task.json 顶层 + 各 task task.json mtime, L2105-2107) → 广播给 `subs` (live.js:6), 各页 onLive 回调软刷。
- onopen: 已 seen 过则 reload (服务重启) (live.js:25); onclose 2s 重连, 5min 失败落遮罩 (live.js:30, GRACE)。

数据源方法 (DataSource Protocol, skein.py:3013-3039): `_board_data/_dashboard/_queue/_task_detail/_archive_list/_search/_spec_tree/_spec_resolve/_exec_argv/config` — 全走 `_snapshot()` (L1903) 单一读面, serve 仅包装成 JSON 响应。**这些方法与 CLI/spec/task.json 解耦** — view 函数 `_view_*` (L2606-3005) 纯读 snap, 重写后端不动它们。

exec 白名单 (`_exec_argv` skein.py:2009-2066, core `[ops/subprocess-safety]` argv 列表 shell=False): `list / ready / current / doctor / status / contract / subtask-list / create / subtask-add / prd(read|write|add|check|uncheck)`。前端实际仅 task 页用 `api.exec(cmd, {id})` (task.js:475) 跑只读命令 (status/contract/subtask-list 等, runRead)。

## 3. 6 页数据流矩阵

| 页 | mount 拉数据 | WS 订阅 (软刷) | 用户操作 → API |
|---|---|---|---|
| dashboard | `GET /__skein__/dashboard` | onLive → 重拉 dashboard | 无 (纯只读 KPI 墙) |
| board | `GET /__skein__/data` (board 全量) | onLive → 重拉 data | 文档弹层: `api.getJSON("/"+doc)` 拉原始 md (board.js:545) |
| queue | `GET /__skein__/queue` | onLive → 重拉 queue | 无 (纯只读队列视图, queue.js 仅展示 readyTasks/readySubtasks/pendingQueue) |
| task | 有 id: `GET /__skein__/task/{id}` (task.js:398); 无 id: `GET /__skein__/data` 取 cards 做列表 (:379) | onLive → 重拉 task / 列表 | `POST /__skein__/exec {cmd, id}` 跑只读命令 (runRead, task.js:475); copyId 仅前端 clipboard |
| spec | `GET /__skein__/spec` (树) | 无 (编辑态保守, spec.js 不挂 onLive) | 选文件: `GET /__skein__/spec/file?path=` (:345); 保存: `POST /__skein__/spec/save` 经 diff 确认 (:426) |
| archive | `GET /__skein__/archive` | onLive → 重拉 archive | 无 (只读归档列表) |

顶栏全局: 搜索 `GET /__skein__/search?q=` (app.js:70, 防抖 200ms); 配置模态 `GET/POST /__skein__/config` (config-modal.js, debounce 400ms 全量 10 键)。

## 4. 重写影响面

**确定动**:
- `assets/webapp/` 全量 (index.html / src/*.js / src/pages/*.js / src/lib/*.js / src/input.css / tailwind.config.js / dist/app.css / vendor/petite-vue.js 删除)。
- `skein.py:1951-1965 _webapp_html()` (token 替换 + index.html 读盘) — 配合新 IA/入口调整。
- `skein.py:3042-3267 build_app()` 内 WS `_watch_loop` 协议 (如改 htmx 可能改 WS 事件粒度, e.g. 细化"data"成 per-resource 推送) + 可能拆 `/__skein__/data` 为更细端点 (现 board 全量 + 各页各自端点已分, htmx 可按片段端点更细)。
- 静态 mount 调整: 删 `/vendor/petite-vue.js`, 视新方案加 htmx.org vendored (buildless CDN-less)。

**确定不动** (验证):
- **task.json schema** — view 函数 `_view_*` (skein.py:2606-3005) 纯读 `_snapshot()`, 重写仅换 API 表述/schema 字段名, 盘上结构不动。`_data_rev` 仍盯 task.json mtime (L2105-2107)。
- **CLI 核心命令** (create/start/claim/confirm/check/finish/archive/...) — skein.py:3278+ `main()` 与 subparser 完全独立于 serve; exec 白名单 (`_exec_argv` L2009-2066) 是 serve 调 CLI 的桥, CLI 本体不动。
- **spec 系统** (`_spec_root/_spec_tree/_spec_resolve` skein.py:1968-1995) — 盘上 `.skein/spec/{core,recall}/<cat>/*.md` 结构不动, 仅 spec 页前端重写 + specFile/specSave 端点表述可保留。
- DataSource Protocol (skein.py:3013-3039) — serve 数据面 seam, 真实 Skein 满足, 测试假源亦然; 重写后端**应继续满足此契约** (否则破坏 TestClient 单测面)。
- `_LOCK_ID_PATH/_REV_PATH/_LIVE_PATH` 常量 (skein.py:2093-2095) — 多 session 去重 + 轮询兜底, 保留。
- 旧 board (`assets/board/`, `_board_html/_board_data`) — `_webapp_html` 缺 index.html 时回落 (`/` 端点 :3133, `_spa()` :3240-3241), 非 webapp 重写范围, 但需确认重写期不破坏回落。

**灰区待定**:
- `_watch_loop` 推送粒度: 现 reload/data 二分, htmx 重写后是否细化 (e.g. 按 task id 推 data-task-changed 让单页片段 swap)? 决策由 child task 定。
- `/__skein__/data` 端点: 现 board 全量返回 cards/overview/DAG nodeVar/nodeCls, htmx 片段渲染可能拆成 `/board/fragment` 类细端点; 但 dashboard/queue/task 已各自分端点, 拆分收益有限。
- 路由模式: 现 history pathname (非 hash), 重写若 htmx 需考虑 htmx hx-push-url vs 现状 SPA history 拦截 (router.js:100-111 click 拦截 a[href])。
- build-css 流程: 现 `tailwindcss` standalone binary (`build-css.sh`, 46MB 存 `~/.cache/skein`, 不入库) → dist/app.css (39.9K)。重写若彻底 buildless 走 CDN tailwind 或纯 CSS 变量, 决定 build-css.sh 去留。

dist/app.css 编译流程: `build-css.sh` 跑 `tailwindcss -i src/input.css -o dist/app.css --minify`, 产物入库 (dist/app.css 39.9K)。运行态零下载零构建 (注释 skein.py:2132)。重写若保留 Tailwind 则保留流程; 若纯 CSS 变量则删 tailwind 依赖。

## 5. examples 设计参考提取

文件: `docs/examples/index.html` (172K, 2218 行) — 海滩蓝金 antd 范式 demo。

**配色 token** (tailwind config 内联 examples:14-46, 4 族):
- `ocean` 5 阶 (foam `#e8f4fa` / shallow `#74b9e8` / mid `#429cd1` / deep `#237bb8` / abyss `#0f4d75`) :16-22
- `whiteSand` 3 色 (pearl `#fffefb` / shell `#fdf6e8` / cream `#f8f0dc`) :24-28
- `goldSand` 4 色 (light `#f0d9a0` / mid `#e6c88b` / deep `#d4b066` / sunset `#c89548`) :30-35
- `night` 3 阶 (base `#0f2033` / mid `#162c42` / deep `#091420`) :37-41
- 语义 success `#48bb78` / warning `#ed8936` / danger `#e53e3e` :43-45
- font: Inter / system-ui :47-49

**antd 组件范式** (6 tab 分类, examples:460-466 tab-btn):
- colors / components / charts / motion / timeline / dag 6 区。
- 组件清单 (按 antd 6 大类映射, h4 标题行号):
  - General: Button :798, Icon :821, Grid (24 列) :869, Layout :895
  - Layout/Layout续: Menu 水平 :949 / 垂直含子菜单 :960, Breadcrumb :1004, Pagination :991
  - Navigation: Steps :1017
  - DataEntry: Input :1057, Select :1077, DatePicker :1087, Checkbox :1098, Radio :1105, Switch :1115
  - DataDisplay: Table :1143, Tag :1229, Badge :1240, Avatar :1258, Tooltip :1273, Card :1289, Skeleton :1410
  - Feedback: Modal (原生 dialog) :1347, Alert :1324, Message :1366, Spin :1377, Progress :1384
- 状态标签 Badge (彩色 demo) :754, 按钮类型/尺寸/状态 :798。

**布局视觉原语**:
- `.glass` 玻璃卡 (圆角 + 边框 + 半透) examples:439-451 多处用。
- `.bg-fluid-light` / `.bg-fluid-dark` (linear-gradient 白沙→奶油→浪花 / night 渐变, examples:57-66) 流体背景。
- `.bg-wave` 浪花→近海渐变 :68-70。
- `.hover-float` :136-141 (translateY + shadow 上浮)。
- tab 切换: `.tab-btn` + `.tab-btn.active` :167-184, `data-tab-target` 属性 + JS 切 active class + 区显示。
- `.text-gradient-ocean` :129 渐变文字标题。
- `.tl-dot` Timeline 时间轴点 (cur 态 `tlPulse` 动画) :207-214; 纵向/横向 Timeline (examples:1905 横向)。
- DAG 节点态: `.dag-node` 待执行 (ocean.shallow 边 + whiteSand.pearl 填) :304; 进行中 (ocean.deep 填 + `dagPulse` 透明度脉冲) :325-331; 已完成/失败态配色。
- `.antd-spin` 旋转 :246; `.antd-shimmer` 骨架闪动 (background-position 400% 动画) :249-255。

**动效语言** (keyframes, examples:144-214):
- `waveShift` 6s 海浪水平偏移 :144-148 (用于 `.animate-wave` 浅海/近海色块)。
- `staggerIn` 0.6s cubic-bezier(0.22,1,0.36,1) 级联入场 :150-157 (`.animate-stagger-in` 错峰)。
- `pulseDot` 1.6s 通用脉冲 :159-165 (`.pulse-dot`)。
- `tlPulse` 时间轴当前点脉冲 :207-214 (尊重 `prefers-reduced-motion` 直接 animation:none)。
- `dagPulse` 1.6s DAG 进行中节点 opacity 脉冲 :325-331。
- `antdSpin` / `antdShimmer` 上述。
- `.hover-float` 悬浮位移 :136-141。
- `drop-shadow(0 4px 8px rgba(0,0,0,.15))` 海滩主题阴影 :339。

**重写可复用清单** (按 token / 组件 / 原语 / 动效分类, 各带 examples 行号):
- token (16 色 + 字体): ocean×5 / whiteSand×3 / goldSand×4 / night×3 / 语义×3 → 替代现 oklch 派生体系 (或两者并存: oklch 派生骨架保留, ocean/goldSand 作 accent 替换 `--skein-gold`)。
- 组件 (≥20): Button/Icon/Grid/Layout/Menu/Breadcrumb/Pagination/Steps/Input/Select/DatePicker/Checkbox/Radio/Switch/Table/Tag/Badge/Avatar/Tooltip/Card/Skeleton/Modal/Alert/Message/Spin/Progress — 现 webapp 用到的 (stat-row/queue-item/dag-node/doc-tree/cfg-switch) 多可对应映射。
- 原语 (≥8): glass / bg-fluid / bg-wave / hover-float / text-gradient / tab-btn 切换 / tl-dot Timeline / dag-node 状态态。
- 动效 (≥7): waveShift / staggerIn / pulseDot / tlPulse / dagPulse / antdSpin / antdShimmer。

## 6. child task DAG 建议 (供 main 决策)

**候选拆分维度** → 建议 7 个 child task:

1. **T1 设计系统落地** (token + 原语 + 动效) — input.css 重写: ocean/whiteSand/goldSand/night 16 色令牌替换 (或并 oklch), 玻璃卡/bg-fluid/hover-float/text-gradient/tab-btn/tl-dot/dag-node 原语 CSS, waveShift/staggerIn/pulseDot/dagPulse keyframes。**无依赖, 先行**。
2. **T2 前端架构基建** (htmx + 原生 DOM 入口/router/lib 重建) — 删 petite-vue, 引 htmx (vendored), 重写 app.js boot / router (保留 history pathname 或换 hx-push-url) / lib/{api,md,live}.js (api 改 htmx 触发; md 保留; live WS 适配新事件)。**依赖 T1** (CSS 命名约定)。
3. **T3 后端 API + WS 协议重构** — build_app 内端点表述调整 (htmx 片段端点?), `_watch_loop` WS 事件粒度细化 (灰区决策), `_webapp_html` token 调整, 删 `/vendor` mount 加 htmx 资产。**依赖 T2** (端点形状跟前端契约)。
4. **T4 board 页重写** — 现 board.js 命令式 innerHTML + dagHtml, 重写为 htmx 片段 + DAG (保留 dag.js Sugiyama 纯函数, 仅换渲染入口)。**依赖 T2+T3**。
5. **T5 dashboard + queue + archive 页重写** — 三只读页, 模板高度相似 (PetiteVue → htmx 片段), 可合并一 task。**依赖 T2+T3**。
6. **T6 task + spec 页重写** — task (列表/详情/DAG/exec) + spec (树/编辑/diff 确认/保存) 两复杂页。**依赖 T2+T3**; spec 的 diff 确认交互复杂, 可独立拆 subtask。
7. **T7 集成联调 + 旧码清理** — 端到端跑 `skein serve` 验 6 页 + WS 软刷 + 主题切换 + 全局搜索 + 配置模态; 删 vendor/petite-vue.js, 清理 board.js 命令式残留; 确认旧 board (`assets/board/`) 回落非回归。**依赖 T4-T6 全完成**。

**DAG 序**:
```
T1 (设计系统) ─┐
               ├→ T2 (架构基建) ─→ T3 (后端 API+WS) ─┬→ T4 (board)         ┐
                                                       ├→ T5 (dashboard/queue/archive) ├→ T7 (联调+清理)
                                                       └→ T6 (task/spec)    ┘
```
T4/T5/T6 并行 (依赖 T2+T3 完成后); T1 可与 T2 部分并行 (CSS 命名约定先对齐)。

**风险点** (前 3):
1. **数据契约断裂** — 6 页 fetch 端点 + onLive 软刷依赖现 `_board_data/_dashboard/_queue/_task_detail/_archive_list/_search` schema。改前端时若同步改后端 schema 字段名, 旧 → 新迁移期易破。建议: 后端 schema 保持向后兼容 (字段只加不删), 或一 child task 内前后端同步改并加迁移。DataSource Protocol (skein.py:3013-3039) 是 seam, 勿破。
2. **WS 协议兼容** — 现 reload/data 二分简单可靠; htmx 重写若细化事件粒度需前后端同步 (`_watch_loop` skein.py:3070-3088 推 + live.js:26-29 收), 否则软刷失效 (页 stale)。live.js 重连 + GRACE 5min 遮罩逻辑需保留。
3. **6 页功能完整性回归** — 现 board 命令式 innerHTML 与 PetiteVue 5 页混合, dagHtml (dag.js) 被 board+task 共用; 重写时 dag.js Sugiyama 纯函数应**保留不重造** (board.js:4-5 注释明确警告 "把已验证的纯函数渲染器整段重造, 收益仅换范式")。spec 页 diff 确认 + task 页 exec runRead + 顶栏全局搜索 + 配置模态双 Tab 都是易漏功能点。

**未决项 / 待 main 拍板**:
- WS 事件粒度 (现二分 vs htmx 细化 per-resource) — 影响 T3 范围。
- `/__skein__/data` 是否拆片段端点 — 影响 T3+T4。
- 路由 history pathname vs hx-push-url — 影响 T2。
- Tailwind 去留 (build-css.sh) — 影响 T1+T2 是否保留 standalone binary。
- oklch 派生体系 vs examples 16 色直接 token — 影响 T1 (并存 / 替换 / 混合)。
