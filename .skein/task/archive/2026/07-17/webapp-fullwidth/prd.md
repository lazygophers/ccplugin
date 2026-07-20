# webapp 全站宽度撑满 — PRD

## 目标
每页内容区撑满浏览器宽度, 去掉 max-width 上限, 展示更多有效信息。保留合理左右 padding (不过度贴边)。

## 现状 (宽度约束清单)
| page | 约束 | 宽度 |
|---|---|---|
| dashboard | `.wrap` max-width:1240px (input.css:200) | 1240px |
| task | `<div class="max-w-6xl mx-auto">` (task.js:90) | ~1152px |
| queue | `<div class="max-w-4xl mx-auto">` (queue.js:30) | ~896px |
| archive | `<div class="max-w-4xl mx-auto">` (archive.js:24) | ~896px |
| spec | 三栏 flex, 无 max (huashu 已撑满) | 已满 |
| board | `.layout` grid, 无 max | 已满 |

## 范围
- 范围内: input.css (.wrap), pages/{task,queue,archive}.js (容器 class)
- 范围外: spec.js / board.js (已撑满); doc-modal / dag-tip 等浮层 (独立尺寸, 不属页面宽度)
- 约束: 保留左右 padding (复用 .wrap 的 padding:30px 28px 或等价); 不破坏响应式 @media 断点

## 验收
- [ ] dashboard 内容撑满 (.wrap 去 max-width, 留 padding + margin auto 无意义可留)
- [ ] task 详情撑满 (去 max-w-6xl, 改 w-full + 左右 padding)
- [ ] queue 撑满 (去 max-w-4xl)
- [ ] archive 撑满 (去 max-w-4xl)
- [ ] spec / board 不受影响 (已满)
- [ ] 超宽屏不贴边 (保留 padding ≥ 28px)
- [ ] 响应式 @media 断点不破坏 (窄屏仍可用)
- [ ] ESM 过 / dist 重建

## 索引
- 任务: task.json
