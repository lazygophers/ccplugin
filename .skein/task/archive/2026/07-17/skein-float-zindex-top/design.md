# 设计 — 悬浮窗 z-index 统一

## z-index 令牌 (input.css :root 加)
```css
--z-float: 1000;   /* 浮层: dropdown/tooltip/popover */
--z-modal: 2000;   /* 模态: 有 backdrop 全屏遮罩 */
```

## 各浮层改法
| 元素 | 文件:行 | 改前 | 改后 |
|---|---|---|---|
| search-dropdown | app.js:28 cssText | 无 z-index | 加 `z-index:1000` (或 var, 但 inline cssText 用字面量) |
| .qpop | queue.js:20 | z-index:50 | z-index:1000 |
| .dag-tip | board.js:74 | z-index:60 | z-index:1000 |
| .doc-modal | board.js:86 | z-index:120 | z-index:2000 |

注: app.js search-dropdown 是 inline `box.style.cssText`, 用字面量 `z-index:1000` (inline 不走 CSS 变量除非 `var()` 字符串拼接, 直接字面量最简)。

## 不改
- topbar z-index 50 (sticky 顶栏, 非悬浮窗)
- body::after/before z-index 0 (背景层)
- .topbar/main#view z-index 1/50 (内容基线)
- .dots z-index 2 (卡内局部)

## 验证
- 浏览器: 打开各悬浮窗 (搜索下拉/queue 弹出/DAG tooltip/doc 模态), 确认不被 topbar/card 盖
- grep: 全文件无 z-index < 1000 的浮层残留 (除背景/内容层)
