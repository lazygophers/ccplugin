# board 删 current/ready/pop 按钮 — PRD

## 目标
/board 命令快捷条删 current/ready/pop 三按钮, 保留 doctor + 新建 task。

## 边界
- 范围内: board.js L536-538 删三按钮
- 范围外: doctor 按钮 (保留); 新建 task 表单; data-quick handler (保留, doctor 用); CSS cmd-btn (保留); dist (CSS 无关, 不重建)
- 约束: 单文件 3 行删

## 验收标准
- [ ] board.js 无 current/ready/pop 按钮 (L536-538 删)
- [ ] doctor + 新建 task 按钮保留
- [ ] data-quick handler 保留 (doctor 用)
- [ ] ESM 语法过

## 索引
- 任务/子任务/调度: task.json
