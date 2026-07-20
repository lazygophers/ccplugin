# board 卡片详情按钮 — PRD

## 目标
/board task 卡片标题行右侧加跳转详情页图标按钮 (→), 比标题文字链接更明显。

## 边界
- 范围内: board.js renderCard h2 加图标按钮 + input.css 按钮样式 + dist 重建
- 范围外: 标题文字链接 (保留); 卡片其他内容; task 详情页; router (已支持 /task?id=)
- 约束: 用户选 "标题行右侧图标" (→ 箭头)

## 设计
- 位置: h2 标题行右侧 (h2 已 flex display, 加到末尾, margin-left:auto 推右)
- 图标: 箭头 SVG (Feather 风格, stroke=currentColor, viewBox 0 0 24 24), 同现有 nav-ico 风格
- 链接: `<a href="/task?id=...">` 包 SVG (router 全局拦截站内 a[href] → SPA 导航)
- hover: accent 色

## 验收标准
- [ ] h2 标题行右侧有 → 图标按钮
- [ ] 点击跳转 /task?id=<task-id>
- [ ] 标题文字链接保留
- [ ] dist/app.css 重建
- [ ] ESM 过

## 索引
- 任务/子任务/调度: task.json
