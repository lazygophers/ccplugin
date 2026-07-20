# board task 卡片 subtask 区移除折叠默认展 — PRD

## 目标
board.js:502 task 卡片 `<details class="detail" open><summary>明细 · DAG + 子任务表</summary>` 移除折叠功能 (不可收起) + 移除 summary 说明, 直接展示 subtask DAG + 列表。

## 边界
**内**: board.js:502-504 删 details/summary 结构; .detail CSS 类清理 (input.css + dist/app.css + safelist)
**外**: dagHtml/subtable 渲染逻辑不动; 其他卡片元素不动; task 详情页不动

## 改动
```
改前 (board.js:502-504):
<details class="detail" open><summary>明细 · DAG + 子任务表</summary>
{dagHtml}{subtable}</details>

改后:
<div class="detail-body">
{dagHtml}{subtable}</div>
```
- 删 `<details>`/`</details>` + `<summary>`
- dagHtml+subtable 直接展示 (不可折叠)
- .detail CSS 删; 若 dag/subtable 需间距容器, 简单 div 包 (或裸输出)

## 验收标准
- [ ] board.js 无 `<details`/`<summary` (grep 零)
- [ ] task 卡片 subtask DAG + 列表默认可见, 无折叠箭头/点击收起
- [ ] input.css 无 `.detail` 类定义 (grep 零)
- [ ] dist/app.css 重建后无 `.detail` (grep 零)
- [ ] safelist (tailwind.config.js) 无 `.detail` (若有)
- [ ] dagHtml + subtable 渲染不破 (DAG 节点 + 子任务表正常显)
- [ ] node --check board.js pass

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (`skein.py subtask list skein-board-subtask-unfold`)
