# queue 页条目悬浮详情 (hover + click 钉住) — PRD

## 目标
webapp /queue 三区 (就绪 task 批 / 就绪 subtask / 待执行总览) 每条加悬浮详情浮层:
- **hover** 鼠标移上即弹浮层, 离开即收
- **click** 钉住浮层 (不随鼠标离开消失), 再 click 或点外部收起
- task 条目显: id / 名 / desc / 状态 / 依赖 / subtask 完成进度
- subtask 条目显: tid/sid / 名 / desc / agent / depends_on / 状态

## 边界
**内**:
- skein.py `_queue()` / `_pending_queue()` 返回字段扩展 (t1)
- queue.js 浮层组件: 三区条目统一 hover+click 行为 (t2)
**外**:
- board.js / task.js / dashboard.js 不动
- 排序逻辑 / 调度算法不动 (只加展示字段)
- 浮层样式复用现有 CSS 变量 (var(--card)/var(--head)/var(--line)/var(--brd)/var(--muted)/badge 类), 不引入新设计系统

## 改动

### t1-backend-fields (skein.py)
`_queue()` (line 1674) + `_pending_queue()` (line 1147) 字段扩展:
```
readyTasks: 现 {id,name,deps} → 加 desc/status/spct
  status: task["status"]
  desc: task.get("desc","")
  spct: _task_pct(t) (或复用 board 的 task 完成百分比函数)

readySubtasks: 现 {tid,sid,name,agent} → 加 desc/status/depends_on
  status: subtask["status"] (SS_PENDING/SS_RUNNING/SS_DONE/SS_FAILED)
  desc: s.get("desc","")
  depends_on: s.get("depends_on",[])

pendingQueue: 现 {tid,sid,name,agent,ready,trank,ti,crit,est,i}
  → 加 desc/status/depends_on (同 readySubtasks)
```
- 不改排序键 (trank/ti/crit/i 不动)
- spct 复用现有 task 百分比计算 (若已有), 无则 inline 计算 done/total*100

### t2-frontend-popover (queue.js)
- 三区条目 li/a 加 `@mouseenter`/`@mouseleave` + `@click` 事件
- 浮层: 绝对定位 div, 显示条目详情字段
- 状态: reactive `pinnedId` (当前钉住条目 key, null=无钉住) + `hoverId` (当前 hover key)
- 浮层显隐条件: hoverId===key || pinnedId===key
- click 切换 pinnedId (同 key 再 click 清空); 浮层内 click stopPropagation (不触发外部收起); document click 清空 pinnedId
- task 浮层: id/名/badge(状态)/desc/依赖列表/进度条(spct)
- subtask 浮层: tid/sid/名/badge(状态)/desc/agent/依赖列表
- 样式: 复用 badge-* 类 + var(--card)/var(--brd)/var(--head); 绝对定位 z-index 高于卡片

## 验收标准
- [ ] `_queue()` 三类条目含新字段 (curl /__skein__/queue 验证)
- [ ] readyTasks 含 desc/status/spct
- [ ] readySubtasks + pendingQueue 含 desc/status/depends_on
- [ ] 排序不变 (pendingQueue 顺序与改前一致)
- [ ] queue.js 三区条目 hover 弹浮层, 离开收
- [ ] click 钉住, 再 click/点外部收
- [ ] task 浮层显 6 字段; subtask 浮层显 6 字段
- [ ] 浮层不破坏现有布局 (绝对定位, 不挤开列表)
- [ ] node --check queue.js pass
- [ ] 无 console error

## 索引
- 任务/子任务/调度: task.json (`skein.py subtask list skein-queue-hover-detail`)
