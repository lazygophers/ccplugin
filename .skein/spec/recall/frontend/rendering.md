---
title: rendering
layer: recall
category: frontend
keywords: [frontend,htm,petite-vue,buildless,tailwind,cdn,page契约,ctx,render,onLive,ws,per-resource,dag,sugiyama,base-href,跨树import,async,data,fetch,dom,state,extract,soft-refresh,scroll,refresh,doc,tab,渲染,分支,dict,v-if]
status: active
---

## webapp 重写范式 (petite-vue → htm 原生 DOM + Tailwind CDN buildless)

### 触发场景

 Skein webapp 大规模 UI 重写: 把 petite-vue (vDOM/diff) 换 htm + 原生 DOM, 配 Tailwind CDN 去 build 步; 6 个 page 一致契约 + 后端 WS per-resource + 跨树 import 整理。

### 陷阱-正解

**陷阱**: 每个 page 自己写一套渲染入口 / 自己接 WS / 自己造 DAG 布局 / 物理路径与 URL 路径错位致 MIME 错。

**正解**: 固定四件套契约 + 双轨 WS + 跨树 import 纪律 + 入口 base 注入。

### 规则

### page 契约 (6/6 一致)

- MUST：每 page 导出 `async function render(mount, params, ctx)`, 6 个 page (dashboard/board/queue/task/spec/archive) 全一致。
- MUST：`ctx = { api, md, h, onLive, navigate }` 依赖容器 (app.js:216 注入, 切页自动退订)。
- MUST：简单 DOM 用 `ctx.h(tag, attrs, ...children)` 极简 h() 转 DOM; 复杂结构用 `ctx.htm` (loadHtm 异步加载, 本地 vendor → CDN 兜底) tagged template。

### WS per-resource 双轨订阅 (live.js)

- MUST：`subscribe(cb, opts)` 双轨: 无 opts 入全局 `subs` Set; `opts.taskId` 入 `taskSubs Map<taskId, Set<cb>>` 精准 swap。
- MUST：`_watch_loop` 推 JSON 三型: `{type:"task-changed",id}` / `{type:"spec-changed",path}` / `{type:"reload"}` / `{type:"data"}` (兜底全订阅)。
- MUST：page 末尾 `onLive(mountApp)` 订阅 (订阅软刷), router 切页自动退订, page 无需清理 (core/frontend-soft-refresh-pattern 同源)。
- 编辑态保守: spec 页 `onLive` 订阅 spec-changed, 但编辑中保草稿不软刷 (spec.js:677-680)。

### 跨树 import 纪律

- MUST：src/new/ 子树自包含 (md.js 物理迁入), 仅 dag.js + prd-parse.js 留原位 (体量大 / 有状态, 不复制)。
- MUST：DAG 渲染复用 dag.js Sugiyama 纯函数 (`import { dagHtml, setNodeMaps } from "../../dag.js"`), 禁重造 (board.js:12 + task.js:12 共用)。

### 入口 base href 注入

- MUST：入口从 `/` 出但 index.html 物理在 `/src/new/` → `_webapp_html` 注入 `<base href="/src/new/">` 让相对引 (`./app.js` + `../tokens.css`) 解析到 `/src/new/*` 而非 `/` (否则命中 SPA fallback 返 text/html → ES module MIME 错)。
- MUST：base 不影响绝对 URL (CDN 路径仍正常); token 缺席则 replace 无副作用, 与 index.html 松耦合。

### 案例

webapp-rewrite task (commits 7e76104c1 → ec0005d8b, 2026-07):
- 入口 base 注入: skein.py:1951-1958 (`_webapp_html` replace `<head>` 注 base)。
- page 契约: pages/dashboard.js:198 `export async function render(mount, params, ctx)`; 注释 line 5 列契约。
- ctx 依赖容器: app.js:214-222 `{ api, md, h, onLive, navigate }`。
- WS 双轨: live.js:13-25 (subs Set + taskSubs Map) + dispatch line 45-60 三型 JSON。
- 跨树 import: pages/board.js:12 + pages/task.js:12 共用 dag.js; pages/task.js:13 共用 prd-parse.js。
- 编辑态保守: pages/spec.js:677-680 onLive 订阅但编辑态跳过保草稿。

### 关联

- core/frontend-soft-refresh-pattern (ctx.onLive + router 自动退订同源)
- recall/frontend/reconstruct-57 (SPA page 文件名 = 路由白名单名 — 6 page 命名规则)
- recall/build/reconstruct-44 (webapp buildless 运行态 — 预构建 dist 的另一面, 本规则是开发态 buildless)

## petite-vue 先 await 拉数据，再 createApp

### 触发场景
编写响应式 page（需要绑定数据到 petite-vue）。

### 陷阱-正解
**陷阱**：依赖 petite-vue mounted 钩子拉数据。
**正解**：render() 内 await 拉全数据，再 createApp(初始态).mount()；vendored petite-vue 无对外钩子。

### 规则
响应式 page 必须先数据后 createApp。

### 案例
task.js:329 / dashboard.js / archive.js 同注释说明。

### 关联
frontend/async-render-data-fetch

## petite-vue 无实例句柄读状态 → DOM 抽模式

### 触发场景
软刷新 (innerHTML swap) petite-vue 响应式组件，需保存 tab/滚动状态。

### 陷阱-正解
**陷阱**：依赖 petite-vue 实例句柄读状态 (如 app.$data.tab)，但 vendored petite-vue 无对外钩子。
**正解**：重挂前从旧 DOM 抽取 data-cur-tab 属性 + window.scrollY，重挂后回填。

### 规则
- MUST：软刷新保状态用 DOM 抽取，不依赖 petite-vue 实例句柄
- MUST：重挂前从 mount.querySelector("[data-cur-tab]") 抽当前 tab
- MUST：重挂前保存 window.scrollY
- MUST：createApp() 时注入 savedTab 作为初始 tab
- MUST：重挂后 requestAnimationFrame(() => window.scrollTo(0, savedScroll))

### 反例表
| 禁 | 改为 |
|---|---|
| 依赖 app.$data.tab 读状态 | 从 DOM 抽 data-cur-tab 属性 |
| 软刷新不保存滚动位 | 保存 window.scrollY 并重挂后回填 |
| 直接 createApp() 无初参 | 注入 savedTab 作为初始 tab |
| 不等 DOM 布局完成就 scrollTo | 用 requestAnimationFrame 等 DOM 完成 |

### 案例
task.js:359-435 (保 tab/滚动)，board-render.js:376-401 (保滚动位)。

### 关联
- petite-vue 先 await 拉数据，再 createApp (frontend/reconstruct-05.md)
- innerHTML 软刷新保滚动位 (frontend/reconstruct-49.md)

## innerHTML 软刷新保滚动位（三层替换 + 居中）

### 触发场景
软刷新 (innerHTML swap)。

### 陷阱-正解
**陷阱**：滚动位置丢。
**正解**：记录 scrollTop/Left + pageYOffset，换 DOM 后复原；首屏无存位则居中活跃节点。

### 规则
board/board-render.js:376-401；webapp 沿用。

## doc tab 非单篇 md 渲染分支顺序

### 触发场景

在 task 详情页 DOC_TABS 新加 research tab 时，数据源从 `docs[tab]` 单篇 md 改为 `research` dict（filename→content 多篇），遇到渲染分支被「暂无内容」兜底分支吞掉的问题。

### 陷阱-正解

当 tab 数据形态是 **dict/列表**（非单篇 md），模板渲染独立分支必须放在 `v-if="!docs[tab]"` 兜底分支**之前**，否则被吞掉。

**反例**（放错顺序会被吞）：
```js
// v-if="!docs[tab]" 在前 → dict 数据源的独立分支永远不可见
<div v-if="!docs[tab]">暂无内容</div>
<div v-if="tab === 'research' && researchHtml">
  <div v-html="researchHtml"></div>
</div>
```

**正解**（独立分支在前）：
```js
// research 渲染分支放最前，dict 数据源优先处理
<div v-if="tab === 'research' && researchHtml">
  <div v-html="researchHtml"></div>
</div>
<div v-if="!docs[tab]">暂无内容</div>
```

### 反例

| 禁 | 改为 |
|---|---|
| 兜底分支在 dict 渲染分支之前 | dict 渲染分支放最前 |
| `v-if="!docs[tab]"` 在前 | 专属渲染分支 `v-if="tab === 'research'"` 在前 |
| 期望 dict 数据源能穿过兜底分支 | 兜底分支只在单篇 md 场景生效 |

### 案例

task.js DOC_TABS 加 research tab：`research` 是 `{filename: content}` dict，research 渲染分支（`v-if="tab === 'research'"`）必须放 `v-if="!docs[tab]"` 之前，否则多篇笔记被「暂无内容」吞掉。

### 适用

- 任何 tab/板块渲染涉及 **dict/列表数据源**（非单篇 md）
- 模板有兜底「暂无内容」分支
- Vue v-if 渲染顺序依赖的场景

### 关联

- `[frontend] Markdown 渲染必须 sanitize`（内容安全，不涉及分支顺序）
- `[arch] SPA page 模块统一契约`（模块依赖，不涉及模板渲染）
