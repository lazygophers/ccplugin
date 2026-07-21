# task-detail-enhance — 详细设计

## 用户确认 (2026-07-20, AskUserQuestion)

5 项需求:
1. 左侧加**边界**解析展示 (现 prd-parse 只抽「目标」「验收标准」)
2. 内容**动态更新** — 痛点: 滚动/闪烁 + 根本不刷 + subtask 状态不刷
3. 默认展示**详细设计** (design) 而非 PRD
4. **start 强制 prd** — 校验粒度: 结构齐 + 无占位 (复用 _normalize_prd)
5. **taskid 去重** — header 显 task.id, name 兜底也显 task.id 导致重复

## 现状 (审计)

### 前端 webapp (assets/webapp/src/)
- `pages/task.js`: 任务详情页, 两栏 (左 subtask/目标/验收, 右 文档 tab)
  - line 142-143: header `<code>{{task.id}}</code>` + line 144 `<h1>{{task.name || task.id}}</h1>` → name 空时 id 重复 (需求 5 根因)
  - line 268: `DOC_TABS` prd 第一; line 388 `tab: "prd"` 默认 (需求 3 改这两处)
  - line 411: `onLive && onLive(mountApp)` 软刷整重挂 (mount.innerHTML 重设) → 闪烁 + 滚动丢 + tab 丢 (需求 2 根因)
  - line 376-377: `parsePrdSections` 只抽「目标」「验收标准」findSection, 没抽「边界」(需求 1 根因)
- `prd-parse.js` (65 行): parsePrdSections / findSection 工具
- `lib/live.js`: WS data → subs.forEach(cb) 软刷; 触发链正常 (skein.py:2192 _data_rev 含各 task.json)

### 后端 (skein.py)
- `_task_detail` (line 1944): 返回 task + docs{prd,design,findings} + subtasks + contracts
- `start` (line 606): 校验 doctor + subtask 数, **没校验 prd 已填** (需求 4 加门)
- `_normalize_prd` (line 366): 校验二级章节 (目标/边界/验收标准/索引) 齐 + 顺序 — 可复用, 加「无占位 TODO」检查

### WS data 软刷链
- skein.py:2325 `_watch_loop` 每 500ms 比 `_data_rev` (task.json mtime)
- 变 → WS 推 "data" → live.js subs 回调 → task.js mountApp 整重挂
- 问题: 整重挂 `mount.innerHTML = TASK_STYLE + TPL` 闪烁 + 滚动丢 + tab 丢 + 用户感知「不刷」(重挂回初始态看不到增量)

## 修法

### 需求 1: 左侧边界展示
- prd-parse.js `findSection(prdSecs, "边界")` 已支持 (通用查找)
- task.js 左栏加 `<section v-if="boundaryHtml">` 块, 复用 goalHtml/acceptHtml 模式
- mountApp 加 `const boundaryHtml = md.renderSafe(findSection(prdSecs, "边界"))`

### 需求 2: 动态更新 (保 tab + 滚动 + 不闪烁)
- 现软刷整重挂 → 改为**保状态重挂**: 重挂前存 {tab, scrollY, copied}, 重挂后恢复
- mountApp 改造: 读全局/闭包缓存的上次状态, createApp 注入恢复 tab, mount 后 window.scrollTo 恢复滚动
- 「根本不刷」排查: 确认 WS data 真到 task 页 (router onLive 订阅链路), 若链路通则修在重挂体验
- subtask 状态不刷: 重挂已含新 subtasks, 应刷; 若仍不刷查 fetchState 是否拉新

### 需求 3: 默认 design
- DOC_TABS 顺序改 design 优先: [{design},{prd},{findings}]
- mountApp `tab: "prd"` → `tab: "design"` (或动态: design 存在则默认 design, 否则 prd)

### 需求 4: start 强制 prd
- start() line 606 doctor 后加: 跑 _normalize_prd 逻辑 + 检查无占位 (## 章节下无 `- [ ] TODO` 残留)
- 复用 _normalize_prd 校验 (返回不规范 raise SystemExit), 加占位检查
- 不通过 → raise SystemExit 阻止 start, 提示先填 prd

### 需求 5: taskid 去重
- header `<h1>{{task.name || task.id}}</h1>` → `<h1 v-if="task.name">{{task.name}}</h1>` (name 空则不显 h1, id 已在 code 显)

## subtask 拆解

1. **st1** (前端 task.js): 需求 1 边界 + 3 默认 design + 5 id 去重 (同一文件, 一批改)
2. **st2** (前端 task.js): 需求 2 软刷保状态 (tab/滚动/不闪烁)
3. **st3** (后端 skein.py): 需求 4 start 强制 prd 门
4. **st4** (测试): 验证 5 项 + claude -p 质检门 (改了前端非 SKILL, 后端加测试)

st1/st3 可并行 (不同文件); st2 依赖 st1 (同文件); st4 依赖全部。

## 验证

- serve 起本地看板手动验 5 项
- st3: `skein start <无 prd task>` 应被拒
- claude -p 质检门 (改了 task.js 前端逻辑, 非强制但跑一次)
