---
title: webapp-assets
category: build
keywords: [build,deployment,css,tailwind,vendor,javascript,framework,token,configuration,nextjs,dist,buildId,构建完整性,引用可达性,diff误判,静态资源引用]
status: active
inclusion: auto
---

## webapp buildless 运行态（预构建 dist）

### 触发场景
发布 webapp。

### 陷阱-正解
**陷阱**：运行时编译 CSS，依赖 npm。
**正解**：dist/ 预构建入库，运行态零下载零构建；改样式经 build-css.sh (standalone tailwind)。

### 规则
tailwind binary 走 ~/.cache，永不 commit。

## petite-vue vendored (IIFE，禁 npm)

### 触发场景
响应式功能。

### 陷阱-正解
**陷阱**：npm 构建期依赖。
**正解**：vendored petite-vue.js (IIFE)，全局 window.PetiteVue，禁 npm 依赖。

### 规则
app.js:11-19 loadPetiteVue 注 <script src="/vendor/petite-vue.js">。

## Tailwind token = CSS 变量薄别名（禁烘焙色值）

### 触发场景
tailwind config。

### 陷阱-正解
**陷阱**：具体配色值烘焙在 config。
**正解**：只把 CSS 变量暴露成 token，禁烘焙色值；主题切换纯 <html data-theme>。

### 规则
tailwind.config theme.extend 引 var(--*)；safelist 保通用组件基类。

## Next.js dist 完整性判据用引用可达性, 不用 diff 大小

### 触发场景
rebuild Next.js dist 后要判断本次构建产物是否完整、可直接发布。

### 陷阱-正解
**陷阱**：拿 `git diff` 前后 dist 差异量大小当判据 ——「diff 很大」就判定「上次构建不完整/本次有问题」。Next.js 每次 build 生成随机 buildId，chunk 文件名随 buildId 变化，rebuild 后 dist 必然产生大量 diff，与构建是否完整无关；曾有 checker 因此误判 FAIL。
**正解**：扫描全部 dist 里 `.html`/`.txt` 文件中出现的 `/_next/` 静态资源引用，逐条确认引用目标文件在 dist 里实际存在（引用总数 vs 缺失数）。引用可达性才是完整性的真判据。
