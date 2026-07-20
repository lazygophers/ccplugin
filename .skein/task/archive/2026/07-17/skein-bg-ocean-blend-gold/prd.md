# 背景海浪式交融渐变真金 — PRD

## 目标
前一版波浪分割 (skein-bg-blue-gold-ratio-split) 被用户拒绝: 波浪太分明锯齿 (circle 46px 半圆), 蓝金硬切 50% 无渐变, skein-gold #FFD98A 偏黄非金。用户要: ① 海浪式柔和大波浪交融 (非锯齿半圆); ② 蓝金渐变过渡区 (非硬切); ③ 真金色调 (非黄)。成功: 浏览器刷新后背景呈现上蓝下金、中间柔和渐变过渡带的海浪式交融, 流沙微光不丢, 暗模式不动。

## 用户确认决策 (AskUserQuestion 已拍板)
- 交融方式: **上下大波浪交融** — 上蓝下金, 中间 40% 宽柔和过渡带 (渐变交融, 非硬切线)
- 金色色值: **#E8C264 亮金** (饱和金黄, 非 #FFD98A 偏黄)
- 参考图分析: 蓝金渐变交融无硬切, 暖金从一角扩散融入浅蓝, 水彩晕染式柔和波浪感

## 边界
- 范围内: `src/input.css` 浅色 body 背景 (98-128 行波浪 + wave-flow keyframes) + `--skein-gold` 令牌 (line 43); `dist/app.css` 重建
- 范围外: board.js/task.js 业务逻辑; 状态色 (--h-*/--st-*); 暗模式金沙星点 (132-146 行, 独立美学不动); surface-bg 纯色面 (line 59, 非背景); body::after 流沙微光 (110-118 行, 质感保留); 顶栏/卡/logo 配色 (它们引用 --skein-gold, 金色令牌变更自动跟随, 不单独改); legacy board/themes/skein.css
- 约束: petite-vue webapp 无构建, CSS 纯静态; --skein-gold 全局令牌变更会联动 logo mark / theme-toggle / btn-primary / card 流光描边 / 进度条 skein-fill / 暗模式金辉 — 这些联动是期望的 (整体换真金调), 非破坏

## 验收标准
- [ ] 浅色背景上蓝下金, 中间有渐变过渡带 (非 50% 硬切, 非锯齿半圆)
- [ ] 波浪形态柔和 (大半径/模糊边缘, 海浪式交融, 非小半圆梳齿)
- [ ] --skein-gold 改为 #E8C264 (真金, 非偏黄 #FFD98A)
- [ ] 流沙微光仍叠上层 (质感不丢)
- [ ] 暗模式金沙星点不动 (状态色不动)
- [ ] dist/app.css 重建含新背景 + 新金色令牌
- [ ] ESM 无破坏 (task.js 能 import, 页面渲染)

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
