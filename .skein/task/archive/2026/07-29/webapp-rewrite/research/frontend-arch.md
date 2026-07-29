# 前端架构勘察 (过程证据)

## 入口链
- `plugins/tools/skein/assets/webapp/index.html:41` `<script type=module src="src/app.js">` 引导。
- `index.html:38` `<main id="view">` SPA 挂载点; `:7` `<link rel=stylesheet href="dist/app.css">`。
- `src/app.js:13-19` loadPetiteVue() 注入 `<script src="/vendor/petite-vue.js">` 挂全局 window.PetiteVue (IIFE 非 ESM)。
- `src/app.js:194-202` boot: loadPetiteVue → wireSearch → wireTheme → wireMotion → configModal.wire → live.start → router.start({api, md})。

## 路由
- `src/router.js:18` ROUTES = ["dashboard","board","queue","task","spec","archive"], DEFAULT="board"。
- `src/router.js:22-32` parse() 解 **location.pathname** (history API 非 hash) + `?id=` (task); 单段路径。
- `src/router.js:67` 动态 `import(\`./pages/${name}.js\`)` → mod.render(mount, params, ctx)。
- `src/router.js:34-35` cleanups[] 存 onLive 退订句柄, teardown() 切页清理。
- `src/router.js:59-63` ctx = {api, md, onLive}; onLive 订阅经 live.subscribe 返回退订压 cleanups。
- `src/router.js:100-111` 拦截站内 a[href] click → pushState + navigate (不整页刷)。
- `src/router.js:117` go(path) 编程式导航。

## 渲染范式 (混合)
- board.js 命令式 innerHTML (无 PetiteVue) — `board.js:4-5` 注释明确"沿用旧看板的命令式 innerHTML 渲染 + 忠实移植 dagHtml, 不重写成 petite-vue 响应式"。
- dashboard/queue/task/spec/archive = PetiteVue 响应式 — 各页 `window.PetiteVue.createApp(state).mount(mount)`。
- dag.js Sugiyama 纯函数 dagHtml(nodes, tips, links, forceVertical) 返回 SVG HTML 字符串; setNodeMaps(varMap, clsMap) 注入状态染色 (dag.js:8); 被 board+task 共用。

## 状态管理
- 无全局 store; 每页 render 闭包内自管 state。
- 软刷: ctx.onLive(remountFn) 订阅, router 切页自动退订 (core `frontend/soft-refresh-pattern`)。
- 全局搜索: app.js:22-81, 防抖 200ms → api.search → 下拉, hit 跳 /task?id=。

## 主题 (实际仅 2 套)
- input.css:17-62 :root = skein-light "晨曦" 默认。
- input.css:66+ [data-theme="skein-dark"] = "夜空金沙"。
- grep `data-theme="` 唯一值 = skein-dark (:root 是浅, 共 2 套)。grill 所述"10 套"过时。
- 令牌: seed (--h, --c-neutral, --c-accent, --h-accent, :19) + 明度锚点 (--l-*, :21-22) → oklch 派生 (--bg/--card/--fg/--head/--muted/--brd/--line/--accent, :26-34)。
- 状态色 --st-pending/active/check/done/failed 色相固定语义 (:35-39, --h-pending 245/active 70/check 200/done 150/failed 25)。
- 玻璃流沙: --skein-gold #E8C264 (:43) + --glass-bg/brd/brd-blue/inset-hi/shadow (:50-57); body 烘焙 radial-gradient (:103-106 浅, 125-141 暗星点)。
- 切换: app.js:87-95 applyTheme 写 <html data-theme>; localStorage skein-theme; 缺省系统跟随 (prefers-color-scheme, app.js:96-111)。
- tailwind.config.js:14-37 Tailwind token = CSS 变量薄别名; safelist 通用组件类免 purge (L11-13)。

## 各页 render 签名 (统一 async render(mount, params, ctx), 6/6 一致)
- dashboard.js:177 render; :183 api.dashboard(); :213 onLive(mountApp)。
- board.js:590 render; :613 ctx.api.data(); :621 onLive 软刷 refresh。
- queue.js:179 render; :187 api.queue(); :224 onLive。
- task.js:372 render; :398 api.task(id); :379 无 id 用 api.data() 列表; :499 onLive。
- spec.js:244 render; :248 api.spec(); :345 api.specFile(); :426 api.specSave(); 无 onLive。
- archive.js:78 render; :84 api.archive(); :126 onLive。

## lib
- lib/api.js:5 BASE="/__skein__"; :11-26 req() fetch 封装抛 ApiError{status,message}; :34-46 各端点便捷函数。
- lib/live.js:6 subs Set; :9 subscribe 返回退订; :19-33 start 连 WS /__skein__/live, onmessage "reload"→location.reload / "data"→广播 subs; onclose 2s 重连, 5min GRACE 落遮罩。
- lib/md.js:46-65 render (GFM 子集); :68-83 sanitize; :86 mount; :90 renderSafe。无第三方依赖。
- lib/config-modal.js:8-16 SCHEMA 镜像 CONFIG_DEFAULTS (max_active/auto_commit/use_worktree/worktree_root/retain_days/web_serve/board_open); 表单+YAML 双 Tab debounce 400ms POST 全量。

## dist 编译
- build-css.sh: tailwindcss standalone binary (v3.4.17, 46MB ~/.cache/skein 不入库) -i src/input.css -o dist/app.css --minify。
- dist/app.css 39.9K 入库; vendor/petite-vue.js 16.5K 入库。
- 运行态零下载零构建 (skein.py:2132 注释)。
