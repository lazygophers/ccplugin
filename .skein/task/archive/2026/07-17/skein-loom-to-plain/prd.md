# dashboard 织机隐喻换通用词 — PRD

## 目标
- [ ] dashboard.js 中文文案织机词 → 通用词 (用户可见处全换)
- [ ] JS 变量/注释织机词 → 通用词 (KNOT_CLS→DOT_CLS 等)
- [ ] input.css 织机类名 → 通用类名 (.loom-face→.status-panel 等)
- [ ] dashboard.js 引用同步 + dist/app.css 重建

## 映射表
| 织机词 | 通用词 |
|---|---|
| 织机总览 / Loom Overview | 总览 |
| 经线墙 | 指标墙 |
| 纬线总数 (task) | 任务总数 |
| 织入进度 (含 subtask) → 织入进度 (保留词, 只删括号) |
| 织面 / 状态织面 | 状态分布 |
| 经线股 | 状态段 |
| 织结 | 状态点 |
| 游走梭 (进行/检查) → 编织中 (带纺织味大众可懂) |
| 线轴 / bobbin | 队列项 |
| 空织机 | 空 |
| 挂上第一根经线 | 创建第一个任务 |
| .loom-face | .status-panel |
| .weft-row | .stat-row |
| .knot | .dot |
| .bobbin | .queue-item |
| .knots | .dots |
| KNOT_CLS | DOT_CLS |

## 边界
范围内: dashboard.js + input.css + dist/app.css
范围外: 其他 pages / app.js / index.html / skein.py

## 验收
- [ ] dashboard 无织机隐喻词 (grep 零命中)
- [ ] CSS 类名全换 + 引用同步
- [ ] build-css.sh exit 0
- [ ] render 契约不破

## 追加需求 (逻辑改)
- [ ] 上机队列区只展示可执行 task (ready=true), 过滤前置依赖未完成的
  - dashboard.js pendingQueue → computed readyQueue (filter q.ready), 模板 v-for readyQueue.slice(0,6)
  - 空态文案 "线轴架空 — 无待上机 subtask" → "无就绪 subtask" (过滤后语义)
  - 冗余 ready-tag (过滤后全 ready) 可删
