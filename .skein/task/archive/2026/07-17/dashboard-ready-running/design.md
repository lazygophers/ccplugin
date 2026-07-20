# 概览页就绪/执行中列表 — 设计

## 布局 (2 栏, 替换现有"队列·待处理项"单 section)

```
┌──────────────────────────────┬──────────────────────────────┐
│ Subtask (左栏)               │ Task (右栏)                  │
│                              │                              │
│ ▸ 进行中 (running)           │ ▸ 执行中 (active)            │
│   · tid/sid name · agent     │   · id name · 进度% · done/  │
│     耗时 Xm / 预期 Ym        │     total · 耗时 Xm/预期 Ym  │
│                              │                              │
│ ▸ 就绪 (ready)               │ ▸ 就绪 (ready)               │
│   · tid/sid name · agent     │   · id name · 前置: -        │
└──────────────────────────────┴──────────────────────────────┘
```

## 后端 _dashboard() 补 3 字段 (skein.py:1702)

```python
# 复用 _board_data cards + _queue 逻辑
def _dashboard(self) -> dict:
    data = self._board_data()
    ov = data["overview"]
    # ... 现有 ...
    # 新增: running subtask (active task 内 SS_RUNNING)
    running_subs = []
    for t in self._active():
        for s in t.get("subtasks", []):
            if s.get("status") == SS_RUNNING:
                running_subs.append({
                    "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                    "agent": s.get("agent", "skein-executor"),
                    "elapsed": _elapsed_sub(s), "est": s.get("estimate"),
                })
    # 新增: ready tasks (pending + 前置全 done)
    ready_tasks = [{"id": t["id"], "name": t.get("name", t["id"]),
                    "deps": t.get("deps", []), "desc": t.get("desc", "")}
                   for t in self._all()
                   if t["status"] == S_PENDING
                   and not any(self._dep_unfinished(d) for d in t.get("deps", []))]
    # 新增: active tasks (执行中, 含进度/耗时)
    active_tasks = []
    for c in data["cards"]:
        if c["status"] in (S_ACTIVE, S_CHECK):
            active_tasks.append({
                "id": c["id"], "name": c.get("name", c["id"]), "status": c["status"],
                "pct": c["pct"], "sdone": c["sdone"], "stotal": c["stotal"],
                "elapsed": c.get("elapsed"), "est": c.get("est"),
            })
    return {... 现有 ...,
            "runningSubs": running_subs, "readyTasks": ready_tasks,
            "activeTasks": active_tasks}
```

注: cards 已含 elapsed/est/sdone/stotal/pct (board_data 算好)。subtask elapsed 需小 helper (started → now 分钟)。

## 前端 dashboard.js

### data 扩展 (fetchState)
```js
runningSubs: r.runningSubs || [],
readyTasks: r.readyTasks || [],
activeTasks: r.activeTasks || [],
```

### TPL: 替换"队列·待处理项" section 为 2 栏 grid

```html
<section class="grid grid-cols-1 md:grid-cols-2 gap-4">
  <!-- 左: Subtask -->
  <div class="card p-5">
    <h2>Subtask</h2>
    <!-- 进行中 -->
    <div class="sec-label">进行中 <span>{{ runningSubs.length }}</span></div>
    <div v-if="!runningSubs.length" class="empty-hint">无进行中</div>
    <a v-for="s in runningSubs" :key="s.tid+'/'+s.sid" :href="'/task?id='+encodeURIComponent(s.tid)" class="list-item running">
      <span class="li-name">{{ s.name }}</span>
      <span class="li-meta"><code>{{ s.tid }}/{{ s.sid }}</code> · {{ s.agent }}</span>
      <span class="li-progress">耗时 {{ fmtDur(s.elapsed) }}<span v-if="s.est"> / 预期 {{ s.est }}m</span></span>
    </a>
    <!-- 就绪 -->
    <div class="sec-label">就绪 <span>{{ readySubs.length }}</span></div>
    <div v-if="!readySubs.length" class="empty-hint">无就绪</div>
    <a v-for="s in readySubs" ... class="list-item ready">
      <span class="li-name">{{ s.name }}</span>
      <span class="li-meta"><code>{{ s.tid }}/{{ s.sid }}</code> · {{ s.agent }}</span>
      <span class="ready-tag">就绪</span>
    </a>
  </div>
  <!-- 右: Task -->
  <div class="card p-5">
    <h2>Task</h2>
    <!-- 执行中 -->
    <div class="sec-label">执行中 <span>{{ activeTasks.length }}</span></div>
    <a v-for="t in activeTasks" :href="'/task?id='+encodeURIComponent(t.id)" class="list-item running">
      <span class="li-name">{{ t.name }}</span>
      <span class="li-meta"><code>{{ t.id }}</code> · {{ t.sdone }}/{{ t.stotal }} · {{ t.pct }}%</span>
      <span class="li-progress">耗时 {{ fmtDur(t.elapsed) }}<span v-if="t.est"> / 预期 {{ fmtDur(t.est) }}</span></span>
    </a>
    <!-- 就绪 -->
    <div class="sec-label">就绪 <span>{{ readyTasks.length }}</span></div>
    <a v-for="t in readyTasks" :href="'/task?id='+encodeURIComponent(t.id)" class="list-item ready">
      <span class="li-name">{{ t.name }}</span>
      <span class="li-meta"><code>{{ t.id }}</code> · 前置 {{ t.deps.length || '-' }}</span>
    </a>
  </div>
</section>
```

### readySubs (computed)
现有 pendingQueue.filter(q=>q.ready) → 提为 computed readySubs。

### fmtDur helper
复用 board 的 fmtDur 逻辑 (分钟 → Xm / XhYYm)。

### CSS (input.css 加)
```css
.sec-label{font-size:11px;font-weight:600;letter-spacing:.04em;color:var(--muted);margin:10px 0 6px;text-transform:uppercase}
.list-item{display:flex;flex-direction:column;gap:2px;padding:8px 10px;border-radius:8px;border:1px solid var(--line);margin-bottom:6px;text-decoration:none;color:inherit;transition:border-color .15s}
.list-item:hover{border-color:var(--accent)}
.list-item.running{border-left:3px solid var(--st-active)}
.list-item.ready{border-left:3px solid var(--st-pending)}
.li-name{font-size:13px;font-weight:500;color:var(--head)}
.li-meta{font-size:11px;color:var(--muted)}
.li-progress{font-size:11px;color:var(--accent)}
.empty-hint{font-size:12px;color:var(--muted);padding:6px 0}
```

## 不改
- KPI 指标墙 / 完成率环 / 状态分布
- _queue() / _board() / 其他 pages
- 后端字段只加不删

## 验证
- 后端: python3 -c "import ast; ast.parse(open('scripts/skein.py').read())" 语法过
- 前端: ESM node --input-type=module dashboard.js 过
- dist 重建 (input.css 改)
- 手动: 起 serve 看/dashboard 4 区渲染

## 索引
- PRD: prd.md
