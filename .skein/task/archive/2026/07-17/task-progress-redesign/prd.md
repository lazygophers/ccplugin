# task 进度计算重新设计 — PRD

## 目标
task 进度从"subtask 均值"升级为"plan/exec/check 三阶段加权"模型, board/看板显示总%+阶段标签。

## 背景
当前 task_pct (skein.py L1448): done=100, 否则 subtask _sub_pct 均值。问题: planning 完成但未 start 的 task = 0%, check 阶段无进度区分。

## 设计

### 进度模型 (权重: plan 10% / exec 75% / check 15%)

阶段推断 (按 task status + subtask 存在性):
- **plan 阶段** (0→10%): task 无 subtask (planning 中); 有 subtask 登记 = plan 完成
- **exec 阶段** (10→85%): status=进行中 (S_ACTIVE), exec_pct = 10 + 75 * (subtask 均值/100)
- **check 阶段** (85→100%): status=检查中 (S_CHECK), 固定 85% (check 无 subtask 细分; 全过即 finish→100)
- **完成** (100%): status=已完成 (S_DONE)

公式:
```
if S_DONE: 100
elif S_CHECK: 85
elif S_ACTIVE: 10 + round(75 * avg(_sub_pct) / 100)
else (S_PENDING):
  if has_subtasks: 10  # plan 完成, 待 start
  else: 5  # planning 中 (估算 plan 进度一半)
```

### 显示
board.js task 卡片进度条 + 阶段标签:
- 总百分比 (新算法)
- 阶段标签 chip: `[plan]` / `[exec]` / `[check]` / `[done]`
- 紧跟百分比后

### 改动点
1. **skein.py `task_pct`** (L1448): 重写为三阶段加权
2. **skein.py `_brief`** (L830) + **L809** (status cmd): 同步新 pct
3. **skein.py `_board_data`**: card 加 `stage` 字段 (plan/exec/check/done)
4. **board.js**: 进度条区加阶段标签 chip
5. **task.js**: task 详情页头部进度也同步

## 边界
- 范围内: skein.py task_pct 重写 + stage 字段; board.js/task.js 阶段标签
- 范围外: subtask 级 pct (_sub_pct 不动); dashboard 页 (后续); CLI list 输出格式
- 约束: 权重 10/75/15; 按状态推断; 总%+标签

## 验收标准
- [ ] task_pct 三阶段加权 (plan 10 / exec 75 / check 15)
- [ ] S_PENDING 有 subtask = 10%, 无 subtask = 5%
- [ ] S_ACTIVE = 10 + 75*subtask均值/100
- [ ] S_CHECK = 85%
- [ ] S_DONE = 100%
- [ ] _brief + status cmd 同步新 pct
- [ ] card 含 stage 字段
- [ ] board.js 显示 [plan]/[exec]/[check]/[done] 标签
- [ ] ast.parse 过 + ESM 过

## 索引
- 任务/子任务/调度: task.json
