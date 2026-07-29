# board 卡片富文本竖向时间轴 — PRD (主入口)

## 目标
- [ ] 重构 board.js `cardStepper` 为竖向时间轴: 每个生命周期态 (创建/就绪/起始/检查/完成) 一个节点, 每节点显三要素。
- [ ] 节点三要素: (1) 发生时刻 (MM-DD HH:mm 或相对); (2) 当前状态 (已完成/进行中/待执行); (3) 耗时 (段间隔 + 从创建累计)。
- [ ] 成功: 打开 /board, 每个 task 卡片可见一条竖向时间轴, 每态一行清晰呈现时刻+状态+耗时。

## 边界
范围内:
- [ ] `assets/webapp/src/pages/board.js` 重写 `cardStepper(c)` 函数 + 替换原 `.stepper/.st-*` CSS 为竖向时间轴样式 (复用 var(--st-*) 色)。
- [ ] 耗时算法:
  - 段间隔 = 该态时刻 - 上一态时刻 (首态=创建, 段间隔显 "-")
  - 累计 = 该态时刻 - created (首态显 "-")
  - 当前态 (status 停在该态, 下一态未到) → 段间隔/累计算到 now (进行中, 实时增长)
  - 未到态 → 时刻/耗时显 "-", 状态显 "待执行"
- [ ] 状态判定: 时间戳 truthy 或 status 已达该态 → 已完成; status 当前停在该态 → 进行中; 否则待执行。

范围外 (非目标):
- [ ] 不改 task 详情页时间线 (task.js)。
- [ ] 不改后端 (card 数据已有 created/started/checked/finished + status 够用; confirmed=null 用 status 推就绪态)。
- [ ] 不改其他 card 字段/布局。
- [ ] 不改 subtask 时间 (本轴只 task 级 5 态)。

已知约束:
- [ ] 时间字段单位 = Unix 秒, 可 null (老 task confirmed/checked 可能无)。
- [ ] 卡片竖向空间有限, 时间轴须紧凑 (每态一行 ~20px, 5 态 ~100px), 不爆卡片。
- [ ] 5 态顺序固定: 创建→就绪→起始→检查→完成。

## 验收标准
- [ ] 前端: board 卡片显竖向时间轴, 5 态节点各显时刻 + 状态 + 段耗时 + 累计耗时。
- [ ] 前端: 进行中态耗时实时 (now - 该态时刻), 待执行态显 "-"/"待执行"。
- [ ] 前端: `node --check` board.js 通过。
- [ ] 前端: 老 task (confirmed/checked=null) 用 status 推, 不报错, 已过态显已完成。
- [ ] 后端: `python3 skein.py doctor` 通过 (不改后端)。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list board-timeline-rich`)
