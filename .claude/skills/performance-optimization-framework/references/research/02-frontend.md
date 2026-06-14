# 前端/Web 性能优化流派调研

> 主题 Skill `performance-optimization-framework` 素材。代表人物：Steve Souders（《High Performance Web Sites》）、Addy Osmani（Google / web.dev）、Google Chrome / web.dev 团队。
> 标注约定：【本人】= 流派代表人物原话/原文；【官方】= web.dev / Chrome 团队文档；【他人总结】= 第三方解读；【推断】= 调研者归纳。可信度：一手（原始书籍/博客/官方文档）/二手（第三方转述）。

---

## 一、核心方法论

### 1. 性能黄金法则（Performance Golden Rule）— Souders

【本人，一手】"80-90% of the end-user response time is spent on the frontend. Start there."（80-90% 的终端用户响应时间花在前端，从这里开始。）
来源：Steve Souders 博客 https://www.stevesouders.com/blog/2012/02/10/the-performance-golden-rule/

- 后端时间 = 服务器返回首字节的耗时（数据库查询、Web service 调用、HTML 拼装）。
- 前端时间 = 其余一切（JS 执行、页面渲染、下载所有引用资源的网络时间）。
- 为什么聚焦前端：开发者对前端有更大控制权（异步加载脚本、合并资源、域名分片等），改进潜力更大、更简单、且被实践验证有效。【本人/官方混合表述，一手+二手】
- 2012 年复核：所有页面（Top 10、~10000 名、初创公司）即便是动态页面，前端占比仍达 76-92%。【本人，一手】

| 站点类别 | 前端占比 |
| --- | --- |
| Top 10 网站 | 76% |
| 排名 ~10000 网站 | 92% |
| 投资组合公司网站 | 84% |
| HTTP Archive Top 50000 | 87% |

历史：黄金法则最早由 Souders 与 Tenni Theurer 于 2007 年 Web 2.0 Expo 首次公开提出。【他人总结，二手】

### 2. 14 条规则（《High Performance Web Sites》, 2007）— Souders

【本人，一手】完整 14 条（顺序如原文）：
1. Make Fewer HTTP Requests（减少 HTTP 请求）
2. Use a Content Delivery Network（使用 CDN）
3. Add an Expires Header（添加 Expires 头）
4. Gzip Components（Gzip 压缩组件）
5. Put Stylesheets at the Top（样式表放顶部）
6. Put Scripts at the Bottom（脚本放底部）
7. Avoid CSS Expressions（避免 CSS 表达式）
8. Make JavaScript and CSS External（JS/CSS 外置）
9. Reduce DNS Lookups（减少 DNS 查询）
10. Minify JavaScript（压缩 JS）
11. Avoid Redirects（避免重定向）
12. Remove Duplicate Scripts（移除重复脚本）
13. Configure ETags（配置 ETag）
14. Make AJAX Cacheable（让 AJAX 可缓存）

来源：https://stevesouders.com/examples/rules.php
书籍宣称：这些规则可削减 25%-50% 的响应时间；即便已高度优化的站点（Yahoo! Search、Yahoo! 首页）也能受益。【本人/出版方，一手】

> 矛盾/时效性说明：规则 9（域名分片相关思路）、规则 13（ETag）在 HTTP/2 时代部分过时——HTTP/2 多路复用使"减少请求数/域名分片"的收益大幅下降。原则精神（减少阻塞、善用缓存、合并资源）仍成立，但具体战术需结合协议版本。【推断】

### 3. 关键渲染路径（Critical Rendering Path, CRP）— web.dev / Chrome

【官方，一手/二手混合】浏览器把 HTML/CSS/JS 转为屏幕像素的步骤序列：
1. **DOM**：HTML 解析构建，**增量式**（token → node → DOM 树）。
2. **CSSOM**：CSS 解析构建，**渲染阻塞且不可增量**——因 CSS 级联规则可被覆写，必须完整解析后才能用于构建渲染树。
3. **渲染树（Render Tree）**：合并 DOM + CSSOM，仅含需渲染的可见节点（`display:none` 被排除）。
4. **布局（Layout）**：计算所有渲染树元素的位置和尺寸。
5. **绘制（Paint）**：填充像素（颜色、图像、边框、阴影），重叠则合成（composite）。

- CSS 渲染阻塞（render-blocking），JS 解析阻塞（parse-blocking）。
- **优化 CRP = 最小化步骤 1-5 的总耗时**，尽快首次渲染并减少后续屏幕更新间隔。
- DOM 越小越好：节点越多，后续 CRP 事件越慢。
- CRP 各步延迟直接影响 FCP / LCP。
来源：https://web.dev/articles/critical-rendering-path/render-tree-construction ; https://web.dev/learn/performance/understanding-the-critical-path ; MDN https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path

### 4. RAIL 性能模型 — Google Chrome 团队（2015）

【官方，一手/二手】以用户为中心的性能模型，把生命周期拆为 4 个动作并设定目标：

| 维度 | 目标 | 含义 |
| --- | --- | --- |
| **Response（响应）** | ≤ 100ms | 用户输入（点击/触摸）后 100ms 内反馈，感觉即时 |
| **Animation（动画）** | 每帧 ≤ 10ms | 60fps 下每帧预算 16ms，浏览器自身约耗 6ms，留给业务 10ms |
| **Idle（空闲）** | 任务块 ≤ 50ms | 主线程工作分块，留出响应用户输入的窗口；空闲期做延迟工作 |
| **Load（加载）** | ≤ 5000ms | 中端移动设备 + 慢速 3G 下 5 秒内可交互；重复访问目标 2 秒 |

口号：【官方，一手】"Focus on the user; the end goal isn't to make your site perform fast on any specific device, it's to make users happy."

> **重要时效性矛盾**：web.dev 官方注明 RAIL **已被 Core Web Vitals 取代**——"Core Web Vitals ... is the recommended approach for defining performance goals over RAIL, and has different thresholds than those detailed here."【官方，一手】RAIL 作为思维框架仍有价值，但目标阈值应以 CWV 为准。
来源：https://web.dev/rail/ ; MDN https://developer.mozilla.org/en-US/docs/Glossary/RAIL

### 5. PRPL 模式 — Google Polymer 团队 / Addy Osmani 推广

【官方+本人，一手/二手】PRPL = Push / Render / Pre-cache / Lazy-load 的加载策略（2016 提出，针对弱网+低端机）。web.dev 表述的核心步骤：
- **Preload** 关键资源
- **Render** 尽快渲染初始路由
- **Pre-cache** 用 Service Worker 预缓存其余资源
- **Lazy-load** 其他路由和非关键资源

Osmani 原话：【本人，二手】"PRPL (Push, Render, Precache and Lazy-Load) is a pattern for aggressively splitting code for every single route, then taking advantage of a service worker to pre-cache the JavaScript ... and lazy load it as needed."
web.dev 提醒：【官方，二手】"not all of the techniques need to be applied together"——任一技术都能带来可观提升。
来源：https://developers.google.com/web/fundamentals/performance/prpl-pattern/ ; https://www.patterns.dev/vanilla/prpl/

> 时效性矛盾：patterns.dev 指出 PRPL 实现细节已演化——Chrome 已移除 server push，app shell 被现代 SSR + streaming 吸收，衡量指标从 TTI 启发式转为 LCP/INP。支柱思想仍成立，实现已变。【他人总结，二手】

### 6. 代码分割与懒加载 — Addy Osmani

【本人，二手】
- 代码分割是单体 bundle 的解药：在代码中定义 split-point，拆成按需懒加载的文件，改善启动时间、更快可交互。
- 路由级分块（route-based chunking）：公寓 app 例子——落在列表路由时不需要详情/预约路由的代码，只发当前路由所需 JS，其余动态加载。
- 核心准则原话："To stay fast, only load JavaScript needed for the current page. Prioritize what a user will need and lazy-load the rest with code-splitting."
- 图片懒加载：首屏之外/视口之外的图片应延迟加载（Lighthouse 有对应审计）。
来源：Addy Osmani, "The Cost Of JavaScript" https://medium.com/@addyosmani/the-cost-of-javascript-in-2018-7d8950fbb5d4

### 7. 性能预算（Performance Budget）— Addy Osmani / web.dev

【本人+官方，一手】把性能指标当预算管理，设上限并强制执行。
- Osmani 定位：【本人，二手】"performance budgets usher a culture of accountability"——把预算视为可花费、可交易的"用户体验货币"。
- 指标类型组合：
  - **数量型（Quantity）**：JS 体积、图片重量、请求数。移动端 JS 预算建议 **< 170KB**（压缩后），关键路径资源总量 **< 170KB**（压缩/最小化）以保证低端机+慢 3G 下也快。
  - **里程碑/时序型（Milestone/Timing）**：如 First Interactive（主线程不被单任务阻塞超 50ms 的时点）。
  - **用户中心指标**：LCP 等。
- 示例规则：产品页移动端 JS < 170KB；搜索页桌面端图片 < 2MB；首页 Slow 3G / Moto G4 下 5s 内可交互；博客 Lighthouse 性能分 > 80（建议 ≥ 85）。
- 强制执行：用 Lighthouse CI 在 PR 上卡性能分，低于阈值则 fail。
- 理念：【本人，二手】"performance is a constant process, not a one-time checklist"；性能是渐进退化的（"a date picker adds 38 KB, marketing ships a heavier hero image ..."），预算强制更早做权衡决策。
- 注意：数量型预算因站点类型而异（电商图多 vs 新闻多文本），需按目标设备分级。
来源：Addy Osmani "Start Performance Budgeting" https://medium.com/@addyosmani/start-performance-budgeting-dabde04cf6a3 ; web.dev "Your first performance budget" https://web.dev/articles/your-first-performance-budget

---

## 二、关键指标与阈值

### Core Web Vitals（CWV）— web.dev / Google

【官方，一手】Google 的统一质量信号倡议，三大指标在 **75 分位**（mobile/desktop 分别统计）达标才算"good"，三项需同时达标。
来源：https://web.dev/articles/vitals ; 阈值定义方法论 https://web.dev/articles/defining-core-web-vitals-thresholds

| 指标 | 衡量 | Good 阈值 | Needs Improvement | Poor |
| --- | --- | --- | --- | --- |
| **LCP**（Largest Contentful Paint） | 加载性能（最大内容元素渲染时点） | ≤ 2.5s | 2.5-4.0s | > 4.0s |
| **INP**（Interaction to Next Paint） | 交互响应性 | ≤ 200ms | 200-500ms | > 500ms |
| **CLS**（Cumulative Layout Shift） | 视觉稳定性 | ≤ 0.1 | 0.1-0.25 | > 0.25 |

【官方，一手】**FID 已于 2024 年被 INP 取代**——"INP became a stable Core Web Vital metric in 2024."
阈值定义原则：必须对现网内容**可达成（achievable）**，且为用户中心、可在真实环境（field）测量的指标。TBT 等是诊断 INP 的辅助实验室指标，但因不可 field 测量而不入 CWV 核心集。

#### LCP 子部分与优化（web.dev https://web.dev/articles/optimize-lcp）【官方，一手】
LCP = TTFB（~40%）+ Resource Load Delay（<10%）+ Resource Load Duration（~40%）+ Element Render Delay（<10%）。
- 让 LCP 资源在初始 HTML 中可被 preload scanner 发现；CSS/JS 中引用的用 `<link rel="preload">`。
- LCP 图片加 `fetchpriority="high"`，**禁用** `loading="lazy"`。
- 减少/内联渲染阻塞样式表；延迟同步脚本；SSR 让图片提前可发现；拆分长任务。
- 优化图片格式/压缩；用 CDN；高效缓存策略；降低 TTFB（减少重定向、CDN 边缘缓存）。

#### INP 三部分与优化（web.dev https://web.dev/articles/optimize-inp）【官方，一手】
INP = Input Delay + Processing Duration + Presentation Delay。
- **拆分长任务**："break up the work in event callbacks into separate tasks"（用 `setTimeout` / yield）。
- 仅在事件回调中跑下一帧视觉更新所需逻辑，其余延后。
- 缩小 DOM（"large DOMs do require more work to render"）。
- 避免布局抖动（layout thrashing：同任务内读写样式）。
- 用 CSS `content-visibility` 懒渲染接近视口的元素。

#### CLS 成因与修复（web.dev https://web.dev/articles/optimize-cls）【官方，一手】
CLS 无单位，= 可见内容位移量 × 位移距离的累计。
- 成因：无尺寸的图片；广告/嵌入/动态注入内容；Web 字体（FOUT/FOIT）。
- 修复：图片设 `width`/`height`（现代浏览器据此推断 aspect-ratio 预留空间）；用 `min-height`/CSS `aspect-ratio` 为晚加载内容预留空间；字体用 `font-display: optional` + 合适回退字体 + preload；动画用 `transform: translate`（合成动画不影响其他元素，不计入 CLS），避免动 `top`/`left`。

### 实验室 vs 现场（Lab vs Field）
【官方，一手】现场测量必要，因性能随设备、网络、其他进程、交互方式大幅波动。CWV 强调 field 可测且用户中心。

---

## 三、核心信念（流派反复出现）

1. **聚焦用户，不聚焦机器**：RAIL 口号、CWV 用户中心指标——性能终点是让用户满意而非跑分。【官方】
2. **前端是主战场**：80-90% 时间在前端，优化收益最大。【本人 Souders】
3. **性能是持续过程，不是一次性清单**：需持续监控 + 预算 + CI 强制。【本人 Osmani】
4. **只发当前所需，其余懒加载**：代码分割 + PRPL + 图片懒加载。【本人 Osmani】
5. **可测量才可管理**：设阈值、定预算、CI 卡口；75 分位真实用户数据。【官方/Osmani】
6. **减少关键路径上的阻塞与资源**：减请求、内联关键 CSS、defer 脚本、缩小 DOM。【Souders + web.dev】
7. **JS 是最贵的字节**：移动端 JS < 170KB 预算，因解析/执行成本高于等量图片。【本人 Osmani】
8. **可达成的阈值**：标准必须对现网内容现实可行，否则无人能达标。【官方】

---

## 四、反对的反模式（Anti-patterns）

- **过多 HTTP 请求 / 未合并资源**（规则 1）。【Souders】
- **脚本放头部阻塞渲染**、**样式表放底部**（规则 5/6 的反面）。【Souders】
- **CSS 表达式、重复脚本、无谓重定向**（规则 7/11/12）。【Souders】
- **不缓存**（缺 Expires/ETag/AJAX 不可缓存）。【Souders】
- **LCP 图片用 `loading="lazy"`** 或不可被 preload scanner 发现。【web.dev】
- **图片/广告/嵌入无预留尺寸** → 布局抖动。【web.dev】
- **用 `top`/`left` 做动画**（应用 `transform`）。【web.dev】
- **布局抖动（layout thrashing）**：同任务读写样式强制同步布局。【web.dev】
- **长任务阻塞主线程** → 输入延迟、INP 差。【web.dev】
- **单体 bundle / 一次性加载全部 JS**，不做代码分割。【Osmani】
- **过大 DOM**。【web.dev】
- **字体 FOIT（不可见文本闪烁）**。【web.dev】
- **把性能当一次性任务**而非持续预算化流程。【Osmani】
- **只优化后端**而忽视前端（黄金法则的反面）。【Souders】

---

## 五、代表性引用（带出处）

- 【本人 Souders，一手】"80-90% of the end-user response time is spent on the frontend. Start there." — https://www.stevesouders.com/blog/2012/02/10/the-performance-golden-rule/
- 【官方 RAIL，一手】"Focus on the user; the end goal isn't to make your site perform fast on any specific device, it's to make users happy." — https://web.dev/rail/
- 【官方 RAIL，一手】"Core Web Vitals ... is the recommended approach for defining performance goals over RAIL." — https://web.dev/rail/
- 【官方 CWV，一手】LCP "should occur within 2.5 seconds"；INP "200 milliseconds or less"；CLS "0.1 or less" — https://web.dev/articles/vitals
- 【本人 Osmani，二手】"PRPL ... aggressively splitting code for every single route, then ... a service worker to pre-cache the JavaScript ... and lazy load it as needed."
- 【本人 Osmani，二手】"To stay fast, only load JavaScript needed for the current page. Prioritize what a user will need and lazy-load the rest with code-splitting."
- 【本人 Osmani，二手】"performance budgets usher a culture of accountability"；"performance is a constant process, not a one-time checklist."
- 【官方 web.dev，一手】CLS 修复："Composited animations using translate can't impact other elements, and so don't count toward CLS." — https://web.dev/articles/optimize-cls

---

## 六、来源清单

一手（原始书籍/博客/官方文档）：
1. 【一手】Steve Souders, "The Performance Golden Rule" — https://www.stevesouders.com/blog/2012/02/10/the-performance-golden-rule/
2. 【一手】Steve Souders, "14 Rules for Faster-Loading Web Sites" — https://stevesouders.com/examples/rules.php
3. 【一手】web.dev, "Web Vitals" — https://web.dev/articles/vitals
4. 【一手】web.dev, "How the Core Web Vitals metrics thresholds were defined" — https://web.dev/articles/defining-core-web-vitals-thresholds
5. 【一手】web.dev, "Optimize LCP" — https://web.dev/articles/optimize-lcp
6. 【一手】web.dev, "Optimize INP" — https://web.dev/articles/optimize-inp
7. 【一手】web.dev, "Optimize CLS" — https://web.dev/articles/optimize-cls
8. 【一手】web.dev, "Measure performance with the RAIL model" — https://web.dev/rail/
9. 【一手】web.dev, "Critical Rendering Path: Render-tree Construction, Layout, Paint" — https://web.dev/articles/critical-rendering-path/render-tree-construction
10. 【一手】web.dev, "Understand the critical path" — https://web.dev/learn/performance/understanding-the-critical-path
11. 【一手】web.dev, "Apply instant loading with the PRPL pattern" — https://developers.google.com/web/fundamentals/performance/prpl-pattern/
12. 【一手】web.dev, "Your first performance budget" — https://web.dev/articles/your-first-performance-budget
13. 【一手】Addy Osmani, "Start Performance Budgeting" — https://medium.com/@addyosmani/start-performance-budgeting-dabde04cf6a3
14. 【一手】Addy Osmani, "The Cost Of JavaScript in 2018" — https://medium.com/@addyosmani/the-cost-of-javascript-in-2018-7d8950fbb5d4

二手（第三方转述/解读）：
15. 【二手】MDN, "RAIL" 术语表 — https://developer.mozilla.org/en-US/docs/Glossary/RAIL
16. 【二手】MDN, "Critical rendering path" — https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path
17. 【二手】patterns.dev, "PRPL Pattern"（含时效性演化说明）— https://www.patterns.dev/vanilla/prpl/

一手占比：14/17 ≈ 82%。

---

## 缺口与待核实

- 【缺口】Souders 14 条规则的**原书各章详细论证**未逐条读取（仅核对标题与顺序）；如需引用具体数据需回到原书或 stevesouders.com 各规则页。
- 【缺口】Osmani Medium 文章为本人发布但平台为 Medium（非自有域），引用为 WebSearch 转述，未逐句原文核对；关键数字（170KB）多源一致，可信度较高。
- 【时效性矛盾，已保留】RAIL 被 CWV 取代、PRPL 实现演化（server push 移除、TTI→LCP/INP）——构建 Skill 时需明确"思维框架 vs 当前推荐实现"的区分。
- 【未深入】Lighthouse / Lighthouse CI / WebPageTest / SpeedCurve 等工具链的具体配置（本调研聚焦方法论，工具细节可另开）。
