# board 卡片时间线 — PRD (主入口)

## 目标
- [ ] board 看板每个 task 卡片显一条精简横向 5 态 stepper (创建 → 就绪 → 起始 → 检查 → 完成), 实心点=已到, 空心点=未到, null 容错。
- [ ] 成功: 打开 /board, 每个 task 卡片可见一行 5 个圆点步进, 直观呈现该 task 走到生命周期的哪一步。

## 边界
范围内:
- [ ] 后端 `scripts/skein.py` `_view_board_data` 的 card dict 补 `"confirmed": t.get("confirmed")` (现 created/started/checked/finished 已传, 缺 confirmed)。
- [ ] 前端 `assets/webapp/src/pages/board.js` card HTML 加横向 stepper 渲染 + 对应 CSS (复用 var(--st-pending)/--st-active/--st-check/--st-done token)。

范围外 (非目标):
- [ ] 不改 task 详情页时间线 (task.js 已有合并竖向时间线, 本 task 只管 board 卡片)。
- [ ] 不改其他 card 字段/布局 (prd/docRow/subtable/DAG 不动)。
- [ ] 不改后端其他视图 (_view_dashboard/_view_task_detail 等)。

已知约束:
- [ ] 老 task 无 confirmed (null) → stepper 就绪点显空心, 容错。
- [ ] 时间字段单位 = Unix 秒。
- [ ] 卡片密集, stepper 须极简 (一行 5 点 + 连线), 不膨胀卡片高度。

## 验收标准
- [ ] 后端: skein.py `_view_board_data` cards 每项含 `confirmed` 键。
- [ ] 后端: `python3 skein.py doctor` 通过。
- [ ] 前端: board 卡片渲染 5 态 stepper, 实心/空心正确反映各态是否到达。
- [ ] 前端: `node --check` board.js 语法通过。
- [ ] 前端: 老 task (confirmed=null) stepper 不报错, 就绪点显空心。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list board-card-timeline`)
