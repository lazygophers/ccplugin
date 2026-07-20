# active-card-animation — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [x] 进行中/检查中 task card + 运行中 subtask card 视觉脉动动画, 让用户一眼识别"正在跑"的任务
- [x] 进度条 shimmer 流光效果, 表"进度在涨"
- [x] 复用现有 .card.active active-pulse CSS (已写未接线), 零浪费

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [x] 范围内: board.js task card + task.js subtask card + queue.js running subtask 行 + input.css 动画
- [x] 范围外: 待处理/已完成 card 不动; 非 skein 状态的通用 .active 不碰
- [x] 约束: 复用现有 active-pulse keyframes; 暗模式金辉; 不破坏现有 .card 样式

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] board 进行中 task card 显脉动光环
- [x] board 检查中 task card 显脉动光环
- [x] board 进行中 task 进度条显 shimmer 流光
- [x] task 详情页运行中 subtask card 脉动
- [x] queue running subtask 行脉动
- [x] 暗模式金辉脉动正常

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list active-card-animation`)
