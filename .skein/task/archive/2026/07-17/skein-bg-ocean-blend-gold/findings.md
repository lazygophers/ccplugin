# 调研收敛 — 海浪式交融渐变真金

## 参考图分析 (mcp__4_5v_mcp__analyze_image)
- 主色: 浅蓝 (#E6F7FF-#B3E5FC) + 暖金 (#FFF3E0-#FFE0B2), 冷暖对比
- 蓝金交融: 渐变分层+区域划分, 无硬切线, 水彩晕染式
- 暖金从一角扩散融入浅蓝, 弧形渐弱 (海浪拍岸余波感)
- 纹理: 无明确海浪形态, 但渐变光晕模拟柔和波浪感

## 用户决策
- 交融: 上下大波浪交融 (非一角扩散, 中间 40% 宽过渡带)
- 金: #E8C264 亮金 (非 #FFD98A 偏黄)

## 前版波浪问题 (skein-bg-blue-gold-ratio-split)
- circle 46px 半圆 = 锯齿梳齿, 非海浪
- linear 50%→50% 硬切 = 无渐变过渡
- #FFD98A = 偏黄非金
- recall: style/css-wavy-divider-radial-gradient-00.md (前版技法, 本版在其上改大半径+软边+过渡区)
