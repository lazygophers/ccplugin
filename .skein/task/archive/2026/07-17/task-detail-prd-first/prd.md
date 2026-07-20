# task 详情页默认 PRD tab — PRD

## 目标
/task?id= 详情页右栏文档 tab 默认改为 PRD (当前默认详细设计)。

## 边界
- 范围内: task.js L357 `tab: "design"` → `"prd"`; L259-262 tab 数组顺序 prd 提前 (可选, 视觉一致)
- 范围外: tab 内容渲染逻辑; 左栏 subtask DAG/目标/验收; 其他页
- 约束: 用户明确 "优先展示 prd 而非详细设计"

## 改动
- task.js L357: `tab: "design"` → `tab: "prd"` (默认 tab)
- task.js L259-262: tab 数组顺序调整 (prd 第一, design 第二, findings 第三) + L1 注释更新
- task.js L215 注释 "默认详细设计" → "默认 PRD"

## subtask
| sid | 名称 | agent | 改动 |
|---|---|---|---|
| default-prd-tab | 默认 tab 改 prd + 顺序调整 | skein-executor | task.js |

## 验收标准
- [ ] /task?id= 打开默认显示 PRD tab
- [ ] tab 顺序 prd 优先
- [ ] task.js node -c 过
- [ ] chrome 实测默认 PRD

## 索引
- 任务/子任务/调度: task.json
