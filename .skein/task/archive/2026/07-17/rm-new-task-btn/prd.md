# 移除 serve webapp 新建 task 按钮

## 目标

webapp /board 移除"＋ 新建 task"按钮及其展开表单。task 创建归 CLI / skein-flow (main 跑 `skein create`), webapp 只读看板。

## 边界

- **删**: "＋ 新建 task" 按钮 (cmd-new toggle-new) + 展开表单 (id/name/desc/deps 输入 + 提交/取消) + wireCmdBar 内 toggle-new/cancel-new/create 逻辑
- **删**: cmd-form CSS (若仅新建表单用) + cmd-new CSS (若仅新建按钮用)
- **保留**: doctor 快捷按钮 + cmd-out 结果区 + wireCmdBar 的 doctor/run/renderResult 逻辑
- **保留**: cmd-bar 容器 (doctor 仍在)
- **范围外**: 其他页 (dashboard/task/spec/archive/queue) 无新建按钮, 不动

## 验收标准

- [x] board.js render() HTML 模板: 删 "＋ 新建 task" 按钮 + `<form data-form="create">` 整块
- [x] wireCmdBar: 删 toggle-new / cancel-new 分支 + form submit create 逻辑 + form.hidden 重置; 保留 doctor / run / renderResult
- [x] cmd-new / cmd-form / cmd-spacer CSS 删 (无其他引用)
- [x] chrome 实测 /board: 无 "＋ 新建 task" 按钮, 无展开表单; doctor 按钮在 + 点击正常
- [x] 无 JS 报错 (form 变量引用清理)

## 索引

- 详细设计: [design.md](design.md)
- 调度: task.json (脚本真值, `skein.py subtask list rm-new-task-btn`)
