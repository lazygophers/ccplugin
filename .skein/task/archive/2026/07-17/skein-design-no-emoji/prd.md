# webapp 设计去 emoji — PRD

## 目标
webapp UI 所有设计 emoji 移除, 尽可能用 inline SVG 图标替代 (Feather/Lucide 风格, stroke=currentColor)。

## 范围
- 范围内: index.html (nav 6 emoji + 搜索 🔍), pages/*.js (空态/错误 emoji), input.css 加图标样式
- 范围外: ☀☾ 主题 toggle (保留), logo mark (CSS 渐变方块), 注释里 emoji, skein.py 终端横幅, board/themes legacy
- 约束: petite-vue webapp 无构建, SVG inline 无外部依赖; dist/app.css 需重建 (input.css 改了)

## 验收
- [ ] nav 6 项 emoji → SVG 线条图标
- [ ] 搜索 🔍 → SVG 放大镜
- [ ] 空态/错误 emoji → SVG 图标 (非 CSS 几何占位)
- [ ] ☀☾ 保留
- [ ] grep 表情 emoji 全清 (除 ☀☾/注释)
- [ ] ESM 语法过 (node --input-type=module)
- [ ] dist/app.css 重建

## 索引
- 设计: design.md
- 任务/子任务/调度: task.json
