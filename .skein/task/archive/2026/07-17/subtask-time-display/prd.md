# subtask 时间点展示 — PRD

## 目标
subtask 时间数据 (created/started/finished) 在 webapp 展示: /task 详情页显示时间点 (混合格式), /board 看板 subtable 每行显示耗时+等待时间。同时修复数据完整性 (fail 不置 finished)。

## 背景
subtask schema (skein.py L1303-1312) 已含 created/started/finished。但:
- backend subtable (_board_data L1563-1571) 未透传这三字段 → board.js 拿不到
- task.js 无时间展示
- fail 路径 (L1391-1394) 不置 finished → 失败 subtask 时间链断裂

## 边界
- 范围内: skein.py subtable 加三字段 + fail 置 finished; board.js subtable 渲染耗时+等待; task.js subtask 时间点展示
- 范围外: dashboard 页; CLI subtask list; task 级 elapsed 逻辑 (已存)
- 约束: /board subtask 级每行; /task 混合格式 (日期+时刻+相对)

## 设计

### backend (skein.py)
1. `_board_data` subtable (L1563-1571): 加 `"created": s.get("created"), "started": s.get("started"), "finished": s.get("finished")`
2. fail 路径 (L1391-1394): `elif a.action == "fail":` 块加 `s["finished"] = now()` (与 done 对称, 记录失败时刻)
3. `_task_detail` (L1713): 已返回 raw subtasks (含三字段), 无需改

### frontend board.js
- subtable 渲染行 (subtable() 函数): 每行加耗时 (finished-started) + 等待 (started-created), 复用 fmtDur

### frontend task.js
- subtask 列表每项加时间点: created/started/finished, 混合格式 `07-17 14:30 (3h ago)`

## 验收标准
- [ ] subtable 透传 created/started/finished
- [ ] fail 路径置 finished
- [ ] /board subtable 每行显示耗时+等待 (done/running 有值, pending 显示 -)
- [ ] /task 详情页 subtask 显示混合格式时间点
- [ ] ast.parse 过
- [ ] ESM 过 (board.js + task.js)

## 索引
- 任务/子任务/调度: task.json

## 扩展需求 (2026-07-17 并入)

### 新增: task 各阶段时间戳
task schema 加 `checked` 字段 (进入检查阶段时刻)。当前 task 只走 pending→active→done, check 是 skill 流程概念不落 status。需:
- task schema 加 `"checked": None`
- 新增 task check 命令 (或复用) 在进 check 阶段时置 checked=now() + status=S_CHECK
- task 级等待时间 = started - created (已有字段, 前端计算)

### subtask 已满足 (backend-fields 已做)
- created/started/finished 三时间戳已透传 subtable
- fail 置 finished 已修
- subtask 等待时间 = started - created (前端计算)
- subtask 执行耗时 = finished - started (前端计算)
