# /board task 卡片删 prdBlock 验收标准章节 — PRD

## 目标
/board task 卡片 PRD 区 (prdBlock) 不再展示「验收标准」章节。subtask 明细表的 acc 列保留。

## 边界
- 范围内: board.js prdBlock (L224-234) filter `sec.name === "验收标准"` 跳过
- 范围外: subtable acc 列 (保留); prdBlock 其他章节 (目标等保留); 其他页
- 约束: 用户明确"只删 prdBlock 验收章节", subtable acc 列不动

## 改动
- board.js L226 prd.map 回调: 加 `if (sec.name === "验收标准") return "";` 跳过该章节

## 验收标准
- [ ] /board task 卡片 PRD 区无「验收标准」章节
- [ ] 「目标」等其他章节正常
- [ ] subtable 验收标准列保留
- [ ] board.js node -c 过
- [ ] chrome 实测

## 索引
- 任务/子任务/调度: task.json
