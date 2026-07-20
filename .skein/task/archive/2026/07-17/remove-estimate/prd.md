# 移除预期时间 estimate — PRD

## 目标
移除 skein 全栈 estimate (预期时间/预期耗时) 概念。保留 elapsed (实际耗时) 不动。

## 用户决策
- 删 estimate 留 elapsed
- 关键路径权重 _crit_weight 退化为纯拓扑深度 (每步计 1, 不再用 estimate)

## 范围 (estimate 分布)
### 后端 skein.py
- L440 subtask dataclass 字段 estimate
- L1170-1184 _crit_weight (用 estimate 算权重) → 退化为拓扑深度
- L1215/1533/1550 cards/queue 的 "est" 字段
- L1257 task dataclass estimate
- L1410-1476 board_data est_total/remain_est/est_count/est_meta (estMeta 字符串) → 删 estimate 部分, estMeta 改为只含 elapsed 或删
- L1716 _dashboard estMeta
- L2194 create 默认 estimate: None
- L2423/2476 CLI --estimate 参数 (create + subtask add)

### 前端 webapp
- board.js:235 subtable 预期列 (fmtDur(s.est)) → 删列
- board.js:242 `<th>预期</th>` → 删
- board.js:287 ov.estMeta 显示 → 删或改
- board.js:296 card "耗时 X / 预期 Y" → 删预期部分, 留耗时
- queue.js:126 q.est 显示 → 删
- dashboard.js:87 estMeta 显示 → 删
- dashboard.js:156/165 estMeta 字段 → 删
- dashboard.js (刚加) li-progress "预期 Ym" + activeTasks est → 删 estimate 部分, 留 elapsed

### skills/docs/commands/glossary
- skills/skein-exec/references/scheduling-algorithm.md:9 关键路径权重描述
- skills/skein-plan/SKILL.md:51 --estimate 说明
- skills/skein-plan/references/dispatch-graph.md:23,32 estimate 供值
- docs/reference.md:28,43,46,47,49 estimate 字段/参数/调度说明
- docs/glossary.md:23 关键路径 estimate 描述

### 数据迁移
- task.json 里现有 estimate 字段: 不主动删 (自然留), 新建不再写

## 验收
- [ ] skein.py: 无 estimate 字段/参数/权重; _crit_weight 退化为拓扑深度
- [ ] CLI: create/subtask add 无 --estimate
- [ ] estMeta: 删 (或只含 elapsed)
- [ ] board.js: 无预期列/卡片预期
- [ ] queue.js: 无 q.est
- [ ] dashboard.js: 无 estMeta / li-progress 预期
- [ ] skills/docs: 无 estimate 描述 (改关键路径=拓扑深度)
- [ ] ast.parse 过 / ESM 过 / dist 重建
- [ ] elapsed 保留不动

## subtask 拆分
1. backend-remove-est: skein.py 删 estimate 字段/CLI/权重退化/estMeta
2. frontend-remove-est: board/queue/dashboard 删 estimate 显示
3. docs-remove-est: skills/docs/glossary 删 estimate 描述

## 索引
- 设计: design.md
- 任务: task.json
