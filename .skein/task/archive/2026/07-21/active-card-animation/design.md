# active-card-animation — 详细设计

## 用户确认 (2026-07-20, AskUserQuestion)

- **范围**: 进行中(active) + 检查中(check) 的 task card + 运行中(running) subtask card 动画
- **形态**: 复用现有 `.card.active` active-pulse 脉动 + 进度条 shimmer (表进度在涨)

## 现状 (审计)

### CSS (input.css) — 动画已写好, 未接线
- `.card.active` (line 251): `active-pulse` 2s box-shadow 脉动光环 (亮模式蓝, 暗模式金辉)
- 注释: "`.active` 由各页给运行中卡" — **但各页没给**
- `.skein-bar > .skein-fill` (line 363): 进度条蓝金流光, **无 shimmer 动画**

### 前端渲染 — card 未按状态加 .active
- **board.js** (line 320): task card `class="card' + (c.nextUp ? " next-up" : "")"` — 只 next-up, 无 active
- **task.js** (line 183): subtask card `<div class="rounded p-3" style="border...">` — 无 card class, 无 active
- **queue.js** (line 46+): activeTasks/runningSubs 用 `.qrow` 行 (非 card), 无脉动

## 修法

### 1. board.js task card 接线 (line 320)
```js
return '<section class="card' + (c.nextUp ? " next-up" : "")
  + ((c.status === "进行中" || c.status === "检查中") ? " active" : "")
  + '" id="task-' + esc(c.id) + '" ...>'
```

### 2. task.js subtask card 接线 (line 183)
现 subtask card 是 `<div class="rounded p-3">` 无 .card class。加 active class (运行中 subtask):
```html
<div class="rounded p-3" :class="s.status === '运行中' ? 'card active' : ''" style="border:1px solid var(--line)">
```
(注: subtask card 非 .card 样式, 给 .card.active 会带来 .card padding 冲突 — 改用独立 class `.sub-active` 或复用 active-pulse 动画但独立选择器)

### 3. queue.js 接线
queue 用 .qrow 行非 card。running subtask 行加脉动 (左边缘高光已有, 加 subtle pulse):
```html
<a ... :class="s.status === '运行中' ? 'qrow-active' : ''" ...>
```
CSS 加 `.qrow-active { animation: active-pulse 2s ease-in-out infinite; }` (复用 keyframes)

### 4. 进度条 shimmer (新增 CSS keyframes)
`.card.active .skein-fill` 或 `.skein-fill.active` 加 shimmer:
```css
.card.active .skein-fill::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 30%, transparent), transparent);
  animation: shimmer 1.8s linear infinite;
}
@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
```
(进行中 card 内进度条叠加流光, 表"进度在涨")

## subtask 拆解

1. **st1** (board.js): task card 接线 .active (进行中+检查中) + 进度条 shimmer CSS
2. **st2** (task.js): subtask card 运行中加脉动 (独立 class 避免 .card 冲突)
3. **st3** (queue.js): running subtask 行加脉动
4. **st4** (input.css): shimmer keyframes + subtask/queue 脉动选择器 + 验证

st1/st2/st3 各页独立可并行; st4 依赖 (CSS 汇总)。

实际: CSS 分散到各 st 改 (st1 加 shimmer, st2 加 sub 脉动, st3 加 qrow 脉动), st4 改为整合验证。或合并: st1 (board+CSS) / st2 (task) / st3 (queue) 并行, 验证在 check。

简化为 3 subtask:
1. **st1** (board.js + input.css): task card .active 接线 + shimmer keyframes + .card.active .skein-fill shimmer
2. **st2** (task.js + input.css): subtask 运行中脉动 (独立 .sub-active class + keyframes 复用)
3. **st3** (queue.js + input.css): running subtask 行脉动 (.qrow-active)

st1/st2/st3 并行 (各改各页 + 各加 CSS 块, input.css 不同区域无冲突)。

## 验证

- serve 起看板: 进行中 task card 脉动 + 进度条流光; 运行中 subtask 脉动
- 暗模式: 金辉脉动正常
- claude -p 质检门: 改了前端 JS+CSS 非 SKILL, 非强制
