# 背景蓝金 1:1 上下波浪分割 — PRD

## 目标
skein-blue-gold-quicksand-theme 完成后背景是中心包裹式双色光晕 (蓝+金 radial 叠加居中)。用户要 1:1 对半分割, 非包裹。成功: 上蓝下金 1:1, 中间波浪分割带缓动, 保留流沙微光质感。

## 边界
- 范围内: `src/input.css` body 背景 + ::after/::before 波浪层; `dist/app.css` 重建
- 范围外: board.js/task.js 业务逻辑; 状态色 (--h-*/--st-*); 暗模式金沙星点 (独立美学不动); legacy board/themes/skein.css
- 约束: petite-vue webapp 无构建, CSS 纯静态; 用户确认"上下波浪 1:1"

## 验收标准
- [ ] 浅色背景上半蓝、下半金, 1:1 对半 (非中心包裹)
- [ ] 中间波浪分割 (非直线硬切), 有缓动流动感
- [ ] 流沙微光仍叠上层 (质感不丢)
- [ ] 状态色 / 暗模式不动
- [ ] dist/app.css 重建含新背景
- [ ] ESM 无破坏 (task.js 能 import, 页面渲染)

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
