# reconstruct 分型扫描 R3 — 前端 SPA + 样式/主题 约定候选

mode=bootstrap · task-id=reconstruct · 只读。扫描根: `plugins/tools/skein/assets/`。
两套前端并存: **board/** (vanilla IIFE 命令式看板, 老) + **webapp/** (petite-vue SPA, 工程化前端, 新)。
prototype/ 与 mockups/ 为设计原型 (A/B/C 方案), docs/examples/sample-skein/board/ 为示例产物 (10+ themes/palettes), 非运行源码 —— 约定以 assets/ 下运行源码为准。

路径均相对仓库根 `/Users/luoxin/persons/lyxamour/ccplugin`。

---

## 架构边界 / 数据流

### F-ARCH-1 · SPA page 模块统一契约
规则: 每个 SPA page MUST 导出 `async function render(mount, params, ctx)`, 由 router 动态 `import('./pages/<name>.js')` 懒加载调用; `ctx = { api, md, onLive }`。
证据:
- webapp/src/router.js:1-12 (契约注释), :67 (`import(\`./pages/${name}.js\`)`), :76 (`await mod.render(mount, params, ctx)`)
- 6/6 page 一致: webapp/src/pages/dashboard.js:162 / board.js:529 / queue.js:179 / task.js:306 / spec.js:244 / archive.js:78 均 `export async function render(mount, params, ctx)`
建议层: core (违反 = router 加载即炸, 全站白屏)
类目: arch

### F-ARCH-2 · page 不直连 API 层, 依赖经 ctx 注入
规则: page MUST 经 `ctx.api` / `ctx.md` / `ctx.onLive` 取依赖, 禁直接 `import` lib/api.js; deps 由 app.js 注入 router、router 组装 ctx 下传 (单向数据流)。
证据:
- webapp/src/app.js:201 `router.start({ api, md })` (顶层注入)
- webapp/src/router.js:46 `let deps = {}` + :59-63 组装 ctx
- 全 pages/ 内 `import ... lib/api` 匹配数 = 0 (grep 空); 各 page 首行 `const { api, onLive } = ctx` (dashboard.js:163 / queue.js:180 / task.js:307 / archive.js:79)
建议层: core (破坏注入边界 = 依赖失序 / 测试不可替身)
类目: arch

### F-ARCH-3 · petite-vue 先拉数据再 createApp
规则: 响应式 page MUST 先 `await` 拉全数据、再 `window.PetiteVue.createApp(初始态).mount(mount)`; 禁依赖 mounted 钩子 (vendored petite-vue 不支持, 且无对外实例句柄)。
证据 (同款注释 + 模式 5 处):
- webapp/src/pages/task.js:329 「先拉数据再 createApp (对齐 spec.js: petite-vue 无对外实例句柄, 初始态直接注入)」
- dashboard.js:165 / archive.js:81 同款注释; queue.js:205 引用; lib/config-modal.js:115 「vendored petite-vue 不支持 mounted — 改 createApp 前先 await getConfig」
建议层: recall (违反非必炸, 但会拿到空初始态 / 丢失响应)
类目: frontend

### F-ARCH-4 · onLive 软刷订阅, 切页自动退订
规则: page 末尾 MUST 用 `ctx.onLive(remountFn)` 订阅数据软刷 (WS "data" → 重挂当前视图, 不整页刷); router 切页在 teardown 自动退订, page 无需手工清理。
证据:
- webapp/src/lib/live.js:8 `subscribe` 返回退订; router.js:35 teardown, :62 `onLive: (cb)=>{ const u=live.subscribe(cb); cleanups.push(u); }`
- page 末尾一致: board.js:565 / task.js:405 / queue.js:224 / dashboard.js:198 / archive.js:126 均 `onLive(mountApp)`
建议层: recall
类目: frontend

### F-ARCH-5 · 后端算数据、前端只呈现
规则: 业务数字 / DAG 节点 / 边 / 状态染色映射 MUST 由 Python 后端算好经 JSON 下发; 前端渲染器只做呈现, 不重算业务。
证据:
- board/board-render.js:1-2 「消费 window.__SKEIN__ (Python _board_data() 出的结构化数据)… 业务数字/节点/边 Python 已算好, 此处只做呈现」
- webapp/src/dag.js:7-8 状态染色映射由上游 `setNodeMaps(varMap,clsMap)` 注入, 非前端定义
- scripts/skein.py:1711-1714 后端注入 css links + 数据
建议层: recall
类目: arch

---

## 命名 / 目录

### F-NAME-1 · SPA page 文件名 = route 名
规则: page 文件 MUST 命名 `pages/<name>.js`, `<name>` ∈ 路由白名单 (dashboard|board|queue|task|spec|archive)。
证据: webapp/src/router.js:18 `const ROUTES = [...]` + :67 按 name 拼路径; pages/ 目录 6 文件名与 ROUTES 一一对应。
建议层: core (名不符 = 动态 import 落 404 占位)
类目: frontend

### F-NAME-2 · localStorage key 统一 skein- 前缀
规则: 前端持久化 localStorage key MUST 以 `skein-` 前缀 (skein-theme / skein-dagview)。
证据: webapp/src/app.js:102,118 `skein-theme`; board/switcher.js:19,22 `skein-theme`, :129,134 `skein-dagview`。
建议层: recall
类目: style

---

## 错误处理

### F-ERR-1 · file:// 协议兜底降级
规则: 依赖 http 端点的能力 (fetch / WebSocket) MUST 检测 `location.protocol === 'file:'` (或 fetch reject) 并降级 (整页 reload / 直接退出 / 友好占位), 禁裸奔报错。
证据 (6 文件一致):
- webapp/src/lib/api.js:15-17 fetch reject → `ApiError(0, "无法连接 skein serve … file:// 直接打开不可用")`
- webapp/src/lib/live.js:14 `if (started || location.protocol === "file:") return`
- board/switcher.js:161 softRefresh `if(location.protocol==='file:'){location.reload();return;}`
- 另见 board/doc.js / board/live.js / webapp/src/prd-parse.js 同类兜底
建议层: recall
类目: frontend

### F-ERR-2 · 统一 ApiError + page 级 catch 占位
规则: API 层 MUST 抛 `ApiError{status,message}` (非 ok / 网络失败); page 渲染 MUST `.catch` 转错误占位, 禁让单页异常炸穿顶栏/其他页。
证据:
- webapp/src/lib/api.js:7-9 `class ApiError`, :16-23 抛
- router.js:73-79 page render 外层 try/catch → placeholder("加载失败: "+e)
- page 内 .catch 出占位: board.js (5 处) / spec.js (3) / task.js (3) / dashboard/queue/archive 各 1
建议层: recall
类目: frontend

### F-ERR-3 · 异步渲染竞态守卫 (token 序号)
规则: 快速切页 / 连续搜索的异步流程 MUST 用自增序号 (token/lastReq) 守卫, 只让最后一次生效、丢弃过期响应。
证据:
- webapp/src/router.js:47 `navToken`, :50 `++navToken`, :69/:72/:78 `token === navToken` 校验
- webapp/src/app.js:63 `lastReq`, :69 `++lastReq`, :71 `if (my !== lastReq) return` (丢弃过期搜索响应)
建议层: recall
类目: frontend

---

## 测试

无前端测试信号: `find assets -name '*.test.js' -o -name '*.spec.js'` 空; 无 jest/vitest 配置。前端质量门走仓库 CLAUDE.md 的 `claude -p` 人读校验, 非自动化断言。→ 本维度**不提候选** (无 ≥2 处约定, 禁硬凑)。

---

## 构建

### F-BUILD-1 · buildless 运行态: dist 入库, 零构建零下载
规则: webapp 产物 (dist/app.css) MUST 预构建入库, 运行态零下载零构建; 改样式后经 `build-css.sh` (standalone tailwind binary) 重建, tailwind 二进制走 ~/.cache 不入库。
证据:
- webapp/build-css.sh:1-4,21 (`-i src/input.css -o dist/app.css --minify`), binary 落 `$HOME/.cache/skein` 从不 commit
- webapp/tailwind.config.js:1 「standalone binary, buildless」
- scripts/skein.py:2047 「webapp 工程化前端: 静态目录 … 运行态零下载零构建」
建议层: recall
类目: build

### F-BUILD-2 · petite-vue vendored (非 npm), 全局挂载
规则: 响应式运行时 MUST 用 vendored `vendor/petite-vue.js` (IIFE 打包, 非 ESM), 经 `<script>` 挂 `window.PetiteVue`, 禁引入 npm 构建期依赖。
证据: webapp/src/app.js:11-19 loadPetiteVue 注 `<script src="/vendor/petite-vue.js">` 挂全局; 全 page 用 `window.PetiteVue.createApp`。
建议层: recall
类目: build

### F-BUILD-3 · Tailwind token = CSS 变量薄别名 (不烘焙配色)
规则: tailwind.config MUST 只把 CSS 变量暴露成 token (语义色/圆角/字型), 禁在 config 烘焙具体配色值; 主题切换纯走 `<html data-theme>` 变量交换, 不用 Tailwind dark class。
证据: webapp/tailwind.config.js:1-6 注释 + theme.extend 引 `var(--*)`; :12-15 safelist 保通用组件基类免 purge。
建议层: recall
类目: build

---

## 事件模式 (frontend 探针)

### F-EVT-1 · document 级 click 委托 + closest 收敛
规则: 站内导航拦截 / 浮层外收起 / 下拉关闭 MUST 走 `document.addEventListener('click', …)` 委托 + `closest()` 判定, 禁给每元素单独绑。
证据:
- webapp/src/router.js:100-111 拦截站内 `a[href]` → pushState (不整页刷)
- webapp/src/app.js:79 搜索下拉外点收起; board/switcher.js:39 fab 面板外点收起、:112 stat 筛选 click 委托
建议层: recall
类目: frontend

### F-EVT-2 · hover popover 状态机 (fixed 定位逃逸 overflow)
规则: DAG 节点悬浮浮层 MUST 用 `has-tip[data-tip]` ↔ `.dag-tip[data-for]` 配对, mouseenter/mouseleave 切显隐, tip 用 `position:fixed` + `getBoundingClientRect` 视口定位逃逸 `.dag-wrap` 的 overflow 裁剪, 下方放不下翻上方。
证据:
- board/switcher.js:138-155 (mouseenter 定位 / mouseleave 隐 / 翻转逻辑)
- webapp/src/pages/board.js:83-85 `.dag-tip{position:fixed;…}`; dag.js:205-208 生成 `.dag-tip[data-for]`
建议层: recall
类目: frontend

### F-EVT-3 · 三层替换渲染保滚动位
规则: 软刷新 (innerHTML swap) 前 MUST 记录滚动容器 scrollTop/Left + 窗口 pageYOffset, 换 DOM 后复原; 首屏无存位则居中到活跃节点。
证据: board/board-render.js:376-401 (savedScroll/savedWin → 复原 / 居中 .n-active)。webapp/src/pages/board.js 沿用 (同栏结构 .col-side .dag-view)。
建议层: recall (单主要实现 + 迁移副本, 弱约定)
类目: frontend

---

## XSS / 转义 (frontend 探针)

### F-XSS-1 · 命令式 innerHTML 渲染器自带 esc()
规则: 任何用 `innerHTML` 拼接用户/数据文本的模块 MUST 先经 `esc()` 转义 `& < >`, 禁裸插。
证据: `function esc` 定义于 6 文件 (board/board-render.js:8 / dag.js:13 / config-modal.js:50 / pages/board.js:167 / pages/task.js:95 / app.js:50); board-render 内 esc() 用 31 处、board.js 28 处。
建议层: core (违反 = 存储型 XSS)
类目: frontend

### F-XSS-2 · Markdown 渲染必经 sanitize
规则: md 渲染结果直插 DOM 前 MUST 经 `sanitize()` 剥 `<script>` / `on*` 事件属性 / `javascript:|vbscript:|data:` href; v-html 场景走 `renderSafe()`。
证据: webapp/src/lib/md.js:67-83 sanitize, :86 mount, :90-95 renderSafe; board/doc.js 同源实现。
建议层: core
类目: frontend

---

## 样式令牌 / 主题 (style 探针)

### F-STYLE-1 · oklch 双层令牌派生契约
规则: 配色 MUST 走两层 oklch 派生 —— seed (色相 --h / 中性染色 --c-neutral / accent 色相+染色) + 明度锚点 (--l-*) → 派生完整语义契约 (--bg/--card/--fg/--head/--muted/--brd/--line/--accent/--st-*); 组件只引派生名, 换肤只改 seed + 锚点。
证据 (两 app 同构):
- board/base.css:13-40 (:root seed + 锚点 + 派生)
- webapp/src/input.css:17-62 (:root 同套派生契约, 逐条对齐)
建议层: core (破坏派生链 = 主题体系崩)
类目: style

### F-STYLE-2 · 组件色一律 var(--token), 禁硬编码色值
规则: 组件/布局配色 MUST 引 `var(--*)` 令牌, 禁硬编码 hex/rgb; 唯一允许硬编码 = 彩底白字 `#fff` 与 body 底纹 surface-bg 锚点。
证据: `var(--` 引用 board/base.css 108 处、input.css 239 处、pages/board.js 90 处; board.js/dag.js 内非 `#fff` 硬编码 hex = 0 (grep 仅命中 #fff 白字)。
建议层: recall (硬底线是 status/语义色不得硬编码)
类目: style

### F-STYLE-3 · 主题双轨: 两套 CSS 同加载, data-theme 切换 + localStorage 持久化
规则: 浅/暗两套主题 CSS MUST 同时加载 (选择器 `[data-theme=...]` 互斥), 换肤 MUST 只切 `<html data-theme>` + 写 localStorage `skein-theme`, 优先级 localStorage 手选 > `prefers-color-scheme` 系统跟随。
证据:
- scripts/skein.py:1711-1714 后端同时 link skein.css + skein-dark.css + base.css
- webapp/src/input.css:66 `[data-theme="skein-dark"]` 重写锚点 + :81-96 `@media(prefers-color-scheme:dark) :root:not([data-theme])` 系统跟随
- webapp/src/app.js:87-123 applyTheme (手选优先) / board/switcher.js:16-28 切 data-theme + 记忆
建议层: recall
类目: style

### F-STYLE-4 · glass 令牌派生 + backdrop-filter
规则: 玻璃质感 MUST 走 `--glass-bg/--glass-brd/--glass-brd-blue/--glass-inset-hi/--glass-shadow` 派生令牌 (跨外观自动换: 浅=蓝白玻璃 / 暗=金辉), 面板配 `backdrop-filter: blur() saturate()` (含 -webkit- 前缀)。
证据: webapp/src/input.css:50-57 (浅 glass 令牌) / :70-77 (暗金调覆盖); backdrop-filter 在 input.css 出现 11 处 (topbar/card/nav/theme-toggle)。注: board/base.css 无 glass 层 (0 处), 系 webapp 专属 A 皮 —— 约定限 webapp。
建议层: recall
类目: style

### F-STYLE-5 · status 色相语义固定, 跨主题不变
规则: 状态色相 `--h-pending/active/check/done/failed` MUST 全局语义固定 (待处理蓝 / 进行中橙 / 检查青 / 完成绿 / 失败红), 换肤只变 surface 染色与明度, 不动状态色相。
证据: board/base.css:19-20 + webapp/src/input.css:24 同套 `--h-pending:245;--h-active:70;--h-check:200;--h-done:150;--h-failed:25`; tailwind.config.js:5 复述语义固定。
建议层: recall
类目: style

---

## 动效 (style 探针)

### F-MOTION-1 · 动效必尊重 prefers-reduced-motion (CSS+JS 双降级)
规则: 所有动画 MUST 提供 `@media(prefers-reduced-motion:reduce)` 降级; JS 侧动效 MUST 先 `matchMedia('(prefers-reduced-motion: reduce)')` 守卫跳过。
证据:
- CSS: input.css / board/base.css / pages/board.js 各 2 处 reduced-motion query
- JS: webapp/src/app.js:132 `reducedMotion` + :135/:161/:173 三处守卫 (runCounters/wireViewportPause/replayMotion)
建议层: recall
类目: style

### F-MOTION-2 · 视口外暂停动画 (IntersectionObserver 门控)
规则: 带动画的卡/进度条 MUST 用 IntersectionObserver 门控, 离开视口加暂停类 (webapp `.paused` / board `.voff`) 停 animation, 省 GPU。
证据: webapp/src/app.js:160-170 wireViewportPause (`.paused`, rootMargin 60px); board/switcher.js:97-100,157 io (`.voff`, rootMargin 120px)。
建议层: recall
类目: style

### F-MOTION-3 · 数字入场递增 (easeOutCubic, reduced-motion 跳过)
规则: KPI/统计数字入场 MUST easeOutCubic 递增动画 (data-count 或 .stat-n 文本), dataset 标记防重复, reduced-motion 跳过。
证据: webapp/src/app.js:134-156 runCounters (`el.dataset.countDone` 幂等, easeOutCubic)。
建议层: drop (单一实现, 仅 webapp app.js 一处, 无 ≥2 一致证据 → 不成约定)
类目: style

---

## 特效签名 (style 探针, 弱约定 / 多为单点艺术签名)

- **quicksand-shimmer 流沙微光**: input.css:120-133 body::after 双色软光带缓动 (单点, 无第二处) → drop。
- **radial-gradient 底纹烘焙**: input.css:100-159 浅蓝金斑 / 暗金沙星点 (单点艺术签名) → drop。
- **conic-gradient hover 流光描边**: input.css:238-248 card::after (单点) → drop。
- 说明: 特效多为 webapp A 皮的一次性艺术表达, 单处出现, 按「≥2 处才算约定」一律 drop, 不硬凑成规则。仅上面 F-MOTION-1/2 (跨文件复现) 成立。

---

## 汇总

- 成立候选 **21 条** (drop 特效签名 3 + 数字递增 1 + 测试维度 0)。
- 分层: **core 6** (F-ARCH-1/2, F-NAME-1, F-XSS-1/2, F-STYLE-1) · **recall 15** · **drop 4**。
- 类目: frontend 11 / style 7 / arch 1(F-ARCH-5) / build 3。
- 两 app 差异: glass 层 (F-STYLE-4) 与 buildless (F-BUILD-*) 仅 webapp; oklch 令牌 / status 色相 / XSS / file 兜底 / DAG 渲染 两 app 共有。
