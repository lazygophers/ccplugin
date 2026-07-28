# 优先级 0-10 打分制

SKEIN task 优先级采用 0-10 整数打分制，默认 5 (中优先级)。用于同状态内排序、资源调度、前端展示。

定义见 `skein.py:574`，排序逻辑见 `skein.py:332-335`。

---

## 打分规则

- **范围**: 0-10 整数 (含 0 和 10)
- **默认值**: 5 (中优先级)
- **存储**: `task.json` 的 `priority` 字段 (数字类型)
- **缺失处理**: 读不到 priority 时按 5 算

```python
# skein.py:574
"priority": getattr(a, "priority", 5) or 5,  # 0-10, 默认 5 (中)
```

---

## 等级映射

| 分数区间 | 等级 | 英文别名 | 含义 |
|---|---|---|---|
| **7-10** | 高优先级 | high | 紧急、重要、阻塞其他 task，优先调度 |
| **4-6** | 中优先级 | mid | 正常优先级，按部就班 (默认) |
| **0-3** | 低优先级 | low | 不急、可以往后排、有空再做 |

```javascript
// app.js:60-64
function prioLevel(p) {
  const n = p != null ? Number(p) : 5;
  if (n >= 7) return 'high';
  if (n >= 4) return 'mid';
  return 'low';
}
```

---

## 存储位置

### 1. 每个 task 的 task.json
```json
{
  "id": "order-create-api",
  "name": "订单创建 API",
  "status": "进行中",
  "priority": 8,
  "deps": [],
  ...
}
```

### 2. 顶层 task.json 索引
顶层 `task.json` 的每个 task 条目也带 `priority` 字段，用于快速排序，免读每个 task 目录。

```python
# skein.py:290-293
tasks = [{"id": t["id"], "status": t["status"], "deps": t["deps"],
          "priority": t.get("priority", 5),
          "worktree": t.get("worktree"),
          "parent": t.get("parent"), "kind": t.get("kind", "task")} for t in self._all()]
```

---

## 排序逻辑

**主规则**: 状态优先 → 同状态内按优先级降序 → 同优先级按 id 序

```
排序键 = (STATUS_ORDER[status], -priority, id)
```

- **状态优先**: 进行中 > 检查中 > 就绪 > 待处理 > 已完成
  - `STATUS_ORDER = {进行中: 0, 检查中: 1, 就绪: 2, 待处理: 3, 已完成: 4}`
- **同状态内**: 优先级数字越大越靠前 (降序)
- **同优先级**: 按 id 字典序稳定排序

```python
# skein.py:332-335
out.sort(key=lambda t: (STATUS_ORDER.get(t["status"], 9),
                        -(t.get("priority") or 5),
                        t["id"]))
```

**前端 queue 页补充**: 同优先级按创建时间降序 (新的在前)

```javascript
// queue.js:32-36
.sort((a, b) => {
  const pa = a.priority != null ? Number(a.priority) : 5;
  const pb = b.priority != null ? Number(b.priority) : 5;
  if (pa !== pb) return pb - pa; // 优先级高的在前
  return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
});
```

---

## 前端展示

### 展示格式
`"{等级}优先级 ({分数})"`

| 分数 | 展示文本 |
|---|---|
| 8 | `高优先级 (8)` |
| 5 | `中优先级 (5)` |
| 2 | `低优先级 (2)` |

```javascript
// app.js:65-68
export function prioLabel(p) {
  const lvl = prioLevel(p);
  return { high: '高优先级', mid: '中优先级', low: '低优先级' }[lvl];
}
```

短标签 (看板卡片等紧凑场景): `高` / `中` / `低`

### 颜色映射

| 等级 | 颜色名 | CSS 类 | 语义 |
|---|---|---|---|
| 高优先级 | danger / red | `text-danger` / `bg-danger` | 危险/紧急，红色系 |
| 中优先级 | warning / gold | `text-warning` / `bg-warning` | 警告/注意，金色系 |
| 低优先级 | accent / blue | `text-accent` / `bg-accent` | 辅助/一般，蓝色系 |

```javascript
// app.js:73-76
export function prioColor(p) {
  const lvl = prioLevel(p);
  return { high: 'danger', mid: 'warning', low: 'accent' }[lvl];
}
```

### 图标映射 (看板 popover)

| 等级 | 图标 |
|---|---|
| 高优先级 | `fa-arrow-up` (向上箭头) |
| 中优先级 | `fa-minus` (横线) |
| 低优先级 | `fa-arrow-down` (向下箭头) |

```javascript
// board.js:137
const prioIcon = prio >= 7 ? 'fa-arrow-up' : prio >= 4 ? 'fa-minus' : 'fa-arrow-down';
```

---

## 调度影响

优先级影响以下调度决策：

1. **看板排序**: 同列 (同状态) 内高优先级在上
2. **start 调度**: `max_active` 满槽时，高优先级就绪 task 先启动
3. **资源分配**: 多 task 并行时，高优先级 task 优先获得执行资源
4. **用户注意力**: 前端视觉上高优先级更醒目 (红色 + 向上箭头)

> **注意**: 优先级不打断正在执行的 task — 已 start 的 task 不会因为有更高优先级的 task 就绪而被抢占。优先级只影响排队顺序和启动顺序。

---

## 设置方式

| 方式 | 命令 / 操作 | 阶段 |
|---|---|---|
| 创建时指定 | `skein create <id> --priority 8` | create |
| 规划时设置 | planning 阶段在 task.json 里填 priority 字段 | pending |
| 运行时调整 | `skein priority <id> <0-10>` (如有此命令) | 任意阶段 |
| 默认值 | 不设置时自动为 5 | - |
