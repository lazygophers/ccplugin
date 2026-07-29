# task 详情时间以时间线展示 — PRD (主入口)

## 目标
- [ ] 看板 task 详情页 (task.js) 把 task 生命周期 + subtask 时间**合并成一条按时间排序的时间线**可视化展示 (活动流)。
- [ ] 更细粒度记录生命周期各态时刻: 创建 → 就绪(confirm) → 起始(start) → 检查(check) → 完成(finish)。
- [ ] 成功: 打开某 task 详情, 看到一条时间线依次呈现 task 各态迁移 + 各 subtask 的建/起/讫事件, 按真实时间先后排列。

## 边界
范围内:
- [ ] 后端 `scripts/skein.py`: 补 `confirmed` (就绪时刻) 字段 — task.json 初始化模板加 `"confirmed": None`, `confirm()` 命令置 `t["confirmed"] = now()`。(`checked` 已有且 check() 已写; created/started/finished 已有)。
- [ ] 前端 `assets/webapp/src/pages/task.js`: 新增合并时间线组件 — 汇总 task 级 (created/confirmed/started/checked/finished) + 各 subtask (created/started/finished) 事件, 按 ts 升序渲染。视觉形态 (横向 stepper / 竖向 timeline) 由执行 agent 按现有 UI 风格 (var(--head)/card/badge/fmtMix) 自适应定, 复用 `fmtMix` 格式化。

范围外:
- [ ] 不改 view 层 `_view_task_detail` (已传 task.json 全文, confirmed 字段自动流到前端)。
- [ ] 不改其他页面 (board/dashboard/queue/archive/spec)。
- [ ] 不新增后端 API 端点。
- [ ] 不追溯回填历史 task 的 confirmed (老 task 无此字段 → 前端时间线该节点显 "-"/跳过, 容错 null)。

已知约束:
- [ ] 时间字段单位 = Unix 秒 (fmtMix 内 `new Date(ts*1000)`)。
- [ ] null 时间字段容错: 未到达的态 (如未 finish) 对应节点显占位, 不报错。

## 验收标准
- [ ] 后端: task.json 模板含 `confirmed` 字段; `skein.py confirm <id>` 后该 task.json 的 `confirmed` 为非 null 时间戳。
- [ ] 后端: `python3 skein.py doctor` 通过 (结构不变量不破)。
- [ ] 前端: task 详情页渲染一条合并时间线, 含 task 级 5 态节点 (有值的) + subtask 事件, 按时间升序; null 态容错不报错。
- [ ] 前端: `node --check task.js` 语法通过。
- [ ] 现有 subtask 平铺时间 (建/起/讫) 与新时间线不冲突 (整合或明确保留, 由 agent 判)。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 任务/子任务/调度: task.json (`skein.py subtask list task-detail-timeline`)
