# 悬浮窗统一最上层 z-index — PRD

## 目标
所有悬浮窗 (浮层/弹出/模态/tooltip/dropdown) z-index 统一拉到最高层, 高于 topbar(50)/内容(1)/背景(0), 确保悬浮时永远在最上层不被遮挡。成功: 任意悬浮窗打开时覆盖所有其他元素, 无被 topbar/card/其他浮层盖住的情况。

## 根因 (扫描发现)
| 元素 | 文件:行 | 当前 z-index | 问题 |
|---|---|---|---|
| search-dropdown | app.js:28 | **无** | 缺 z-index, position:fixed 但可能被后续元素盖 |
| .qpop (queue 弹出) | queue.js:20 | 50 | 跟 topbar 同级, 弹出可能被 topbar 盖 |
| .dag-tip (DAG tooltip) | board.js:74 | 60 | 低于 .doc-modal(120), 但 tooltip 需高于模态? (看交互) |
| .doc-modal (文档模态) | board.js:86 | 120 | 当前最高, 但无规范 |

## z-index 层级规范 (统一)
- 0: 背景层 (body::after, body::before)
- 1: 内容基线 (topbar, main#view)
- 50: sticky 顶栏 (.topbar)
- **1000+: 浮层 (所有悬浮窗统一)** — 高于一切常规层
  - 具体: 浮层用 z-index: var(--z-float) 统一令牌, 值 1000
  - 模态框 (有 backdrop 遮罩全屏) 用更高 z-index: var(--z-modal) = 2000 (盖其他浮层)

## 边界
- 范围内: app.js (search-dropdown), queue.js (.qpop), board.js (.dag-tip, .doc-modal); input.css 加 z-index 令牌 (--z-float / --z-modal)
- 范围外: topbar z-index 50 (保持, 它不是悬浮窗); body 背景/织纹/流沙 (z-index 0 保持); .dots (z-index 2, 卡内局部非浮层); 暗模式; legacy board/themes
- 约束: 纯 CSS/JS 微改, 无功能变更, 只改 z-index 值 + 加令牌

## 验收标准
- [ ] search-dropdown 加 z-index (浮层级, ≥1000)
- [ ] .qpop z-index 拉到浮层级 (≥1000, 高于 topbar 50)
- [ ] .dag-tip z-index 浮层级 (≥1000)
- [ ] .doc-modal z-index 模态级 (≥2000, 有 backdrop 最高)
- [ ] input.css 定义 --z-float / --z-modal 令牌, 各浮层引用
- [ ] topbar(50)/内容(1)/背景(0) 不动
- [ ] dist/app.css 重建 (input.css 改了的话)
- [ ] 无 ESM 破坏

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json
