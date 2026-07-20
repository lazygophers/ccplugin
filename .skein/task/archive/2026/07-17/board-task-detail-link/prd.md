# task↔board 导航往返 — PRD

## 目标
打通 task 详情页与 board 的导航往返: board 卡片可点进详情, 详情页有返回按钮。

## 现状
- board.js renderCard (L290) h2 纯文本无跳转
- task.js 详情页 header (L100) 无返回按钮; 仅 notFound 分支 (L95) 有 `<a href="/">← 返回看板</a>`

## 范围
- 范围内: pages/board.js (卡片 id 加链接), pages/task.js (header 加返回按钮)
- 范围外: 其他
- 约束: 复用 router 全局 click 拦截 (站内 a[href] → SPA 导航); 无构建

## subtask
1. card-link: board.js renderCard h2 task id 包 `<a href="/task?id=<id>">` + hover 样式
2. back-btn: task.js header 区加返回按钮 (`history.back()` 或 `<a href="/board">`)

## 验收
- [ ] board task 卡片 id 可点 → /task?id=<id> 详情页 (SPA 不整页刷)
- [ ] task 详情页 header 有返回按钮, 点 → 回 board (或 history.back)
- [ ] 返回按钮样式贴合 skein 玻璃风, 不破坏 header 排版
- [ ] ESM 过

## 索引
- 任务: task.json
