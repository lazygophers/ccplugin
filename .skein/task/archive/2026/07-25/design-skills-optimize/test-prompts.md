# Test Prompt 验证集（dim8）

> 每个配 should-trigger + 预期行为。过 `claude -p` 验证 AI 可正确识别路由 / 三方向门 / 自检逻辑。

## design-uiux test prompts

### T1: should-trigger · 媒介路由 + 三方向门
```
我要做一个电商网站的商品详情页布局，帮我设计结构。
```
**预期**：触发 design-uiux → 定媒介 HTML → 三方向初稿门先出 3 个差异化结构 → 不直接给单版。

### T2: should-trigger · CLI 媒介 + 组件
```
我的 CLI 工具命令结构太乱，帮我优化参数布局。
```
**预期**：触发 design-uiux → 定媒介 CLI → 三方向门 → 引用 cli/layout + cli/components。

### T3: should-not-trigger · 配色（应走 design-color）
```
帮我的 SaaS 仪表盘选一套配色。
```
**预期**：触发 design-color（非 design-uiux）→ 配色三方向门。

## design-color test prompts

### T4: should-trigger · 配色 + 可访问性
```
帮我设计一套金融 App 的配色，要求暗模式和色盲友好。
```
**预期**：触发 design-color → 定媒介 App → 配色三方向门 → 可访问性硬指标（对比度/Okabe-Ito）。

### T5: should-trigger · UI 风格清单
```
我想给落地页选个 UI 风格，有哪些选择？
```
**预期**：触发 design-color → 引用 styles-catalog.md（67 风格）。

### T6: should-not-trigger · 布局（应走 design-uiux）
```
帮我把页面布局改成三栏结构。
```
**预期**：触发 design-uiux（非 design-color）。
