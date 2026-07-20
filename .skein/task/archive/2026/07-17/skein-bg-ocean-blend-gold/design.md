# 设计 — 海浪式交融渐变真金

## 改动点 1: --skein-gold 令牌 (input.css:43)
`--skein-gold: #FFD98A` → `--skein-gold: #E8C264`
- #E8C264 = oklch(~0.80 0.11 85), 真金黄, 饱和度足不偏黄
- 全局联动 (期望): logo mark (line 171) / theme-toggle dark on (313) / btn-primary dark (332) / card 流光 conic (236) / 进度条 skein-fill (360) / 暗模式金辉玻璃层 / 暗底金沙星点 — 统一换真金调

## 改动点 2: body 背景波浪 (input.css:98-108 + wave-flow 124-128)
当前: circle 46px 半圆 + linear 硬切 50%→50%。问题: 锯齿梳齿, 硬切无渐变。

新方案 — 大柔波浪 + 渐变过渡区:
- 基底: `linear-gradient(180deg, 蓝 0% 40%, 金 60% 100%)` — 40-60% 间渐变过渡 (非 50% 硬切)
- 波浪层: circle 大半径 (200-300px) + 软边缘 (透明度渐变 70%→98%→100%, 而非 98%→100% 硬边), 错半相位铺成柔和起伏
- 流沙微光 body::after 叠上层进一步软化
- wave-flow keyframes 保持平移循环 (tile 宽 = 2R, R 放大后周期相应调)

关键参数 (待 subtask 微调):
- 过渡区: 40%-60% (20% 宽渐变带)
- 波浪半径: ~240px (大柔海浪, 非半圆梳齿)
- 软边: transparent 60% → 色 100% (宽渐变, 非硬切)
- tile = 480px, 平移周期调 28s
