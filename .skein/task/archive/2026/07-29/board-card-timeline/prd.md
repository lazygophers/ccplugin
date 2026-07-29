# board 卡片时间线 — PRD (主入口)

## 目标
- [x] board 看板每个 task 卡片显一条精简横向 5 态 stepper (创建 → 就绪 → 起始 → 检查 → 完成), 实心点=已到, 空心点=未到, 用 status 推已达态 (不依赖后端补字段)。
- [x] 成功: 打开 /board, 每个 task 卡片可见一行 5 个圆点步进, 直观呈现该 task 走到生命周期的哪一步。

## 边界
范围内:
- [x] 前端 `assets/webapp/src/pages/board.js` card HTML 加横向 stepper 渲染 + 对应 CSS (复用 var(--st-pending)/--st-active/--st-check/--st-done token)。
- [x] stepper 用 card 数据已有的 `status` 推已达态 (待处理→[创], 就绪→[创,就], 进行中→[创,就,起], 检查中→+检, 已完成→+完), 老 task confirmed/checked=null 也正确显示。

范围外 (非目标):
- [x] 不改 task 详情页时间线 (task.js 已有合并竖向时间线)。
- [x] 不改后端 `_view_board_data` (card 已有 created/started/checked/finished + status, 够用)。
- [x] 不改其他 card 字段/布局 (prd/docRow/subtable/DAG 不动)。
- [x] 不改后端其他视图。

已知约束:
- [x] 时间字段单位 = Unix 秒。
- [x] 卡片密集, stepper 须极简 (一行 5 点 + 连线), 不膨胀卡片高度。

## 验收标准
- [x] 后端: `python3 skein.py doctor` 通过 (card 数据不改)。
- [x] 前端: board 卡片渲染 5 态 stepper, 实心/空心用 status 推已达态, 正确反映各态是否到达。
- [x] 前端: `node --check` board.js 语法通过。
- [x] 前端: 老 task (confirmed/checked=null) stepper 不报错, status 驱动正确显示 (待处理就绪点空心; 已完成全亮)。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list board-card-timeline`)
