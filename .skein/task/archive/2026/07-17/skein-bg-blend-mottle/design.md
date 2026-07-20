# 设计 — 整面蓝金光斑交融

## body 背景 (L98-109) 重写
去掉上下分割 linear 基底 + 单行波浪层。改多块 radial-gradient 光斑散布全屏:

```css
body {
  background:
    /* 金斑: 多块散布不同位置/大小 */
    radial-gradient(42% 38% at 18% 22%, color-mix(in srgb, var(--skein-gold) 22%, transparent) 0%, transparent 65%),
    radial-gradient(38% 34% at 82% 28%, color-mix(in srgb, var(--skein-gold) 18%, transparent) 0%, transparent 60%),
    radial-gradient(46% 40% at 72% 78%, color-mix(in srgb, var(--skein-gold) 20%, transparent) 0%, transparent 65%),
    radial-gradient(34% 30% at 28% 82%, color-mix(in srgb, var(--skein-gold) 16%, transparent) 0%, transparent 60%),
    /* 蓝斑: 交错散布 */
    radial-gradient(44% 38% at 72% 18%, color-mix(in srgb, var(--accent2) 20%, transparent) 0%, transparent 65%),
    radial-gradient(38% 34% at 22% 52%, color-mix(in srgb, var(--accent2) 18%, transparent) 0%, transparent 60%),
    radial-gradient(42% 36% at 88% 62%, color-mix(in srgb, var(--accent2) 16%, transparent) 0%, transparent 65%),
    radial-gradient(36% 32% at 48% 88%, color-mix(in srgb, var(--accent2) 14%, transparent) 0%, transparent 60%),
    /* 底色: 蓝金混合中性 (非纯蓝/纯金, 免大色块) */
    linear-gradient(135deg, var(--surface-bg-1) 0%, var(--surface-bg-2) 50%, var(--surface-bg-3) 100%);
  background-attachment: fixed;
  ...
}
```

关键点:
- **8 块光斑** (4 金 + 4 蓝) 散布不同位置 (at X% Y%), 大小/透明度略变, 交错互混
- **光斑柔和**: 透明度 0%→transparent, 色浓度 14-22% (低浓度免过艳), 渐变到 transparent 60-65% (宽软边)
- **底色 linear 135deg** (surface-bg-1→2→3, 蓝→中性→金微): 非纯色块, 全屏轻微蓝金渐变作底, 光斑叠上
- **不再用 wave-flow keyframes** (无单行波浪层) — 可删 keyframes + body animation, 或保留 body::after 流沙微光做流动

## body::after 流沙微光 (L110-118) — 保留
已有双色软光带飘移, 叠上层增强交融流动。不动。

## wave-flow keyframes (L124-128) — 删
body 不再用波浪层 + wave-flow 动画。删 keyframes + body `animation: wave-flow ...`。body 流动感由 body::after quicksand-shimmer 提供。

## 验证
- 视觉: 整面光斑交错, 无上下分割, 无单条波纹
- 性能: 8 层 radial-gradient + 底色 1 层 = 9 层, 固定背景, 可接受 (现代浏览器 GPU 合成)
- grep: 无 `circle 240px` / `wave-flow` / `50% 50%` 硬切残留 (在 body 块)
