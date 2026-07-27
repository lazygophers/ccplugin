---
title: webapp 重写范式 (petite-vue → htm 原生 DOM + Tailwind CDN buildless)
layer: recall
category: frontend
keywords: [frontend,htm,petite-vue,buildless,tailwind,cdn,page契约,ctx,render,onLive,ws,per-resource,dag,sugiyama,base-href,跨树import]
source: finish:webapp-rewrite
authored-by: skein-spec
created: 1785111188
status: active
related: [frontend-soft-refresh-pattern,reconstruct-57,build/reconstruct-44]
updated: 1785111188
---

## 触发场景

 Skein webapp 大规模 UI 重写: 把 petite-vue (vDOM/diff) 换 htm + 原生 DOM, 配 Tailwind CDN 去 build 步; 6 个 page 一致契约 + 后端 WS per-resource + 跨树 import 整理。

## 陷阱-正解

**陷阱**: 每个 page 自己写一套渲染入口 / 自己接 WS / 自己造 DAG 布局 / 物理路径与 URL 路径错位致 MIME 错。

**正解**: 固定四件套契约 + 双轨 WS + 跨树 import 纪律 + 入口 base 注入。

## 规则

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

## 案例

webapp-rewrite task (commits 7e76104c1 → ec0005d8b, 2026-07):
- 入口 base 注入: skein.py:1951-1958 (`_webapp_html` replace `<head>` 注 base)。
- page 契约: pages/dashboard.js:198 `export async function render(mount, params, ctx)`; 注释 line 5 列契约。
- ctx 依赖容器: app.js:214-222 `{ api, md, h, onLive, navigate }`。
- WS 双轨: live.js:13-25 (subs Set + taskSubs Map) + dispatch line 45-60 三型 JSON。
- 跨树 import: pages/board.js:12 + pages/task.js:12 共用 dag.js; pages/task.js:13 共用 prd-parse.js。
- 编辑态保守: pages/spec.js:677-680 onLive 订阅但编辑态跳过保草稿。

## 关联

- core/frontend-soft-refresh-pattern (ctx.onLive + router 自动退订同源)
- recall/frontend/reconstruct-57 (SPA page 文件名 = 路由白名单名 — 6 page 命名规则)
- recall/build/reconstruct-44 (webapp buildless 运行态 — 预构建 dist 的另一面, 本规则是开发态 buildless)
