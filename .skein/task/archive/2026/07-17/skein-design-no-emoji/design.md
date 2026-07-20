# 设计 — 去 emoji (全 SVG 图标)

## 原则 (用户强调)
尽可能用 icon/SVG 实现, 不用 CSS 几何占位方块。所有 emoji → 对应语义的 inline SVG 线条图标 (Feather/Lucide 风格, stroke=currentColor)。

## 1. nav SVG 图标 (index.html L15-20)
每 nav 项 emoji → inline SVG (15x15, stroke=currentColor, sw 1.6):

| nav | 旧 emoji | SVG 图标 | path |
|---|---|---|---|
| 概览 | 📊 | dashboard (仪表盘) | `<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>` |
| 看板 | 📋 | grid | `<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>` (或看板变体) |
| 队列 | ⏳ | clock | `<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>` |
| 任务 | 📄 | file | `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>` |
| 规范 | 📖 | book | `<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>` |
| 归档 | 🗄 | archive | `<rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><line x1="10" y1="12" x2="14" y2="12"/>` |

html 模板:
```html
<a href="/dashboard" data-nav><svg class="nav-ico" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">[PATH]</svg> 概览</a>
```

## 2. 搜索 icon (index.html L23)
🔍 → SVG 放大镜: `<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>`

## 3. 空态/错误 SVG 图标 (pages/*.js)
每 emoji → 语义对应 SVG (大尺寸 48x48, opacity .5, 居中):

| 位置 | 旧 emoji | SVG 图标 | path |
|---|---|---|---|
| router.js:41 | 🧵 (404) | hash/file-x | `<line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>` |
| task.js:93 | 🔍 (未找到) | search | `<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>` |
| task.js:93 | ⚠️ (错误) | alert-triangle | `<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>` |
| task.js:237 | 🧵 (空态) | inbox/hash | 同 router |
| queue.js:40 | ✅ (空态) | check-circle | `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>` |
| archive.js:50 | 📦 (空态) | archive box | 同归档 nav |
| archive.js:56 | 🔍 (无果) | search | 同搜索 |
| dashboard.js:48 | 🧵 (空态) | hash | 同 router |
| spec.js:31 | 🗂️ (空态) | folder | `<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>` |

pages/*.js 改法: `<div class="text-4xl mb-2">🧵</div>` → `<div class="empty-ico">[SVG]</div>`

input.css 加空态图标样式:
```css
.empty-ico { display: flex; justify-content: center; margin-bottom: 8px; opacity: .45; color: var(--accent); }
.empty-ico svg { width: 40px; height: 40px; }
```

## 4. 不改
- index.html L28-29 ☀☾ (保留)
- logo mark (CSS 渐变方块)
- 注释里 emoji
- skein.py 终端横幅
- board/themes legacy

## 验证
- grep 表情 emoji 全清 (除 ☀☾/注释)
- SVG inline 无外部依赖
- ESM 语法过
- dist 重建 (input.css 改了)
