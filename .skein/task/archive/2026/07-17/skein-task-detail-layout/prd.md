# task 详情页两栏布局 + 全量平铺展示 — PRD

## 目标
webapp /task?id= 详情页重构: 两栏布局 (左 subtask DAG+列表+目标/验收 / 右文档 tab 默认详细设计), 尽可能平铺展示全部信息, 不需下拉即见关键内容。

## 边界
**内**:
- 抽取 board.js DAG 渲染为共享模块 `src/dag.js` (t1)
- task.js 改两栏布局 + 默认详细设计 tab + 平铺目标/验收 (t2)
- PRD markdown 解析「## 目标」「## 验收标准」章节 (t3)
**外**:
- board.js 看板主布局不动 (只改 import dag.js)
- queue.js / dashboard.js / archive.js 不动
- task 详情 api (`_task_detail`) 不动 (已含全量: task.json + docs + subtasks + contracts)
- 调度/排序逻辑不动

## 布局设计 (两栏)
```
┌─ header (全宽: id/名/状态/desc/命令条) ──────────────────┐
├──────────────────────┬──────────────────────────────────┤
│ 左栏 (subtask 区)     │ 右栏 (文档 tab)                   │
│  · subtask DAG 图     │  [详细设计][PRD][调研收敛]        │
│  · subtask 列表        │  (默认详细设计, 非 PRD)            │
│    (含状态/进度/依赖)  │  markdown 渲染                    │
│  · 目标 (PRD 抽出)     │                                  │
│  · 验收标准 (PRD 抽出) │                                  │
├──────────────────────┴──────────────────────────────────┤
│ 契约区 (全宽, 空则不显)                                   │
└──────────────────────────────────────────────────────────┘
```
- 桌面 (≥900px): 两栏 grid (左 2/5, 右 3/5)
- 移动 (<900px): 单栏堆叠 (左在上, 右在下)

## 改动

### t1-extract-dag-module (board.js + 新建 src/dag.js)
- 抽取 board.js 的 `dagHtml(nodes, tips, links, forceVertical)` (line ~199) + 相关 helper (esc, 节点布局算法) 到 `src/dag.js`
- board.js 改 `import { dagHtml } from "../dag.js"` (或 IIFE 全局挂 window.SkeinDag)
- 抽取后 board.js 看板渲染行为不变 (diff 最小)
- dag.js 导出: `dagHtml(nodes, tips, links, forceVertical)` 纯函数

### t2-two-col-layout (task.js)
- task.js TASK_STYLE + TPL 重构为两栏
- header 保持全宽
- 左栏: subtask DAG (调 dag.js dagHtml 渲染) + subtask 列表 (现有) + 目标区 + 验收标准区
- 右栏: 文档 tab (PRD/详细设计/调研收敛), 默认 tab 从 `"prd"` 改 `"design"`
- subtask DAG: task.json subtasks 的 depends_on 构造 nodes/links, 调 dagHtml
- 契约区保持全宽底部
- 响应式: media query 切单栏

### t3-prd-section-parse (task.js 或 src/prd-parse.js)
- 解析 prd.md markdown, 抽 `## 目标` / `## 验收标准` 章节 (## 标题分割)
- 抽出的章节 markdown 渲染 (md.renderSafe) 显示在左栏
- PRD tab 内仍显完整 PRD (含目标/验收, 不删)
- 解析逻辑: 按 `^## ` 分割, 匹配标题前缀 (目标/验收标准)

## 验收标准
- [ ] src/dag.js 存在, 导出 dagHtml 纯函数
- [ ] board.js import dag.js, 看板渲染不变 (diff 仅 import + 删除原函数)
- [ ] task.js 两栏布局 (桌面), 移动单栏
- [ ] 左栏含 subtask DAG 图 (复用 dag.js)
- [ ] 左栏含 subtask 列表 (状态/进度/依赖)
- [ ] 左栏含目标区 (PRD 解析)
- [ ] 左栏含验收标准区 (PRD 解析)
- [ ] 右栏文档 tab 默认「详细设计」
- [ ] PRD 解析抽目标/验收章节正确 (## 标题分割)
- [ ] node --check task.js / dag.js / board.js 全 pass
- [ ] 无 console error, 布局不破

## 索引
- 任务/子任务/调度: task.json (`skein.py subtask list skein-task-detail-layout`)
