# 调研: 任务看板/进度可视化/UI 对比 — 对 skein task.html 看板的优化建议

> 罗盘: skein 是**静态渲染 + 轻量**定位 (serve 每请求实时渲染 task.json → shell.html + 内联 JSON; 前端无框架, 命令式 innerHTML + WS 热重载软刷新)。所有建议以此为筛: 只借「信息架构/可视化形式/交互范式」的设计原理, 不引入重运行时。

---

## 一、skein 现状 (本地勘察真值)

**架构** (`scripts/skein.py`):
- `_board_data()` (L1495-1693): Python 算全部业务数字 (pct/耗时/DAG 节点边/Sugiyama 分层/next-up/prd 解析/关键路径权重), 出结构化 JSON。前端**不重算业务**。
- `_board_html()` (L1695-1735): 读 `assets/board/shell.html` 模板, 内联 JSON 进 `window.__SKEIN__`, 填 token。serve 实时不落盘。
- 软刷新: `GET /__skein__/data` 拉新 JSON → `renderBoard(data)` 重渲染 `.layout` innerHTML, 保滚动态 (board-render.js L304-405)。WS `/__skein__/live` rev 变推 reload。
- 双前端: 旧 `assets/board/` (board-render.js 405 行 + switcher.js 180 + doc.js + live.js; 2 主题 skein/skein-dark) + 新 `assets/webapp/` (petite-vue SPA, 7 页 dashboard/board/queue/task/spec/archive)。

**看板展示信息** (board-render.js renderBoard L304-388):
- 左栏 sticky: 任务进展卡 = 4 状态 stat 卡 (可点筛选) + 已耗总计 + 当前进度条 + **待执行队列** (pending subtask 调度序, 就绪/排队 chip) + **task 维度 DAG** (Sugiyama SVG, 节点状态色) + **subtask 维度 DAG** (切换)。
- 右栏卡片流: 每个 task 一卡 = id+状态徽标+下一个 chip + 名称 + docLinks (PRD/设计/调研) + **prd 徽标/目标+验收 checklist** + 前置/worktree/耗时/预期 + 子任务进度条 + 明细折叠 (subtask DAG + 子任务表)。

**主题/配色** (`assets/board/base.css` L1-141):
- 设计令牌系统: seed (--h/--c-neutral/--c-accent/--h-accent) × 明度锚点 → oklch 派生全套契约 (--bg/--fg/--accent/--st-*)。
- 2 主题 (skein 浅晨曦玻璃 / skein-dark 夜空金沙), 状态色语义固定跨主题不变。
- 动效: 晨曦呼吸背景 + hover conic 流光描边 + active 蓝脉动 + 进度条蓝金流光 (视口外 .voff 门控暂停), `data-motion=full` 默认不跟系统 reduce-motion。

**已有亮点 (非空)**:
- DAG + 关键路径权重排序 (`_crit_weight` L1245, `_pending_queue` L1265) — 比多数看板强。
- 软刷新保滚动态 + DAG 视图滚动位复原 (board-render.js L374-386)。
- prd checklist 实时解析徽标 (badge = done/total)。
- 节点状态色 + 调度序队列 + 就绪/排队区分。

**缺什么 (对照主流看板信息架构)**:
- 无**时间维度**: 只有 "已耗 Xm / 预期 Ym" 文字, 无甘特/时间轴/时间条 (任务 prompt 提的 "时间条" 在现码里实为进度条 `.bar`, 非时间轴)。
- 无**阻塞可视化**: blocked task 仅靠 trank 排序隐含, 无 blocker flag/原因/卡在哪。
- 无**WIP 限制/超限告警**: 多 task 并行无上限提示。
- 无**筛选维度**: 只有状态筛选, 无按 agent/worktree/前置/阶段(plan/exec/check/done) 筛选。
- 无**排序选项**: 固定按状态序, 无按耗时/创建/进度排序。
- 无**聚合趋势**: 完成率是单点, 无 burndown/velocity/cycle-time/cumulative flow。
- 无**card aging**: 看不出哪个 task 卡了很久 (有 elapsed 文字但无视觉强调)。

---

## 二、外部对比 (主流看板/编排器/终端/甘特库)

| 类别 | 代表 | 对 skein 最值得借的设计 |
|---|---|---|
| 看板 SaaS | Linear / Trello / WeKan / Focalboard / Kanboard | Linear 键盘优先+极简卡片; 卡片=信息辐射器 (标题/owner/priority/blocker/due); blocker **不单列列, 留在原列叠 flag** |
| 数据编排器 | Airflow / Dagster / Prefect | Airflow **Grid View** (run × task 矩阵, 时间轴+状态色), Graph View (DAG 拓扑+状态色); 长跑/重试实例明细 |
| 甘特库 | frappe-gantt / dhtmlx-gantt / mermaid gantt / Bryntum | frappe-gantt 轻量 SVG (契合 skein 轻量定位); dhtmlx 重 (30k task, 依赖/关键路径/资源, 过重) |
| 终端看板 | taskwarrior-tui / basilk / Kanban-TUI | taskwarrior **scrollable calendar view** (due 日期可视化); 高信息密度+vim 导航 |
| AI agent 看板 | MCP kanban servers / Trello MCP | AI agent 自组织看板 schema; 与 skein 同生态 (任务由 agent 产出, 非人填) |

**关键共识 (多源交叉)**:
1. **卡片信息辐射器**: 标题/owner/priority/blocker/due 五要素够, 详情进卡内不堆卡面 ([Wrike](https://www.wrike.com/kanban-guide/kanban-cards/), [Atlassian](https://www.atlassian.com/agile/kanban/cards))。
2. **WIP 限制**: 每列上限让瓶颈可见, 超限视觉告警不藏卡 ([Atlassian WIP](https://www.atlassian.com/agile/kanban/wip-limits), [Businessmap](https://businessmap.io/kanban-resources/getting-started/what-is-wip))。
3. **阻塞不单列列**: 留原列叠 flag+原因+日期+解阻链接 ([marcusoft](https://www.marcusoft.net/2017/02/comments-on-board-practices.html), [Nave](https://getnave.com/blog/blocked-work-in-kanban/))。
4. **Grid View (时间×任务矩阵)**: Airflow 主视图, 适合多 run/多态的编排场景, 一眼看出哪个 task 卡在哪个阶段 ([Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/ui.html))。
5. **趋势指标**: burndown/velocity/cycle-time/CFD 是 PM 工具标配 ([Atlassian metrics](https://www.atlassian.com/agile/project-management/metrics), [Sourcegraph 2026](https://sourcegraph.com/blog/agile-metrics-what-to-track-and-why-they-matter-2026))。

---

## 三、Top 借鉴点 (按 skein 罗盘筛过, 带「值不值得」判定)

### 1. 阻塞可视化 (blocker flag) — 强荐
- 现状: blocked task 仅 `_pending_queue` 的 `trank=2` 排序隐含, 卡面无任何阻塞标识。
- 借鉴: 在卡面叠 flag (如 ⛔ + 前置未完成 task 名), **不新增状态/列**。数据现成 (`_dep_unfinished`, depNames 已在卡)。
- 罗盘判定: 契合。零新依赖, Python 已有 `_dep_unfinished`, 前端加一个 flag DOM + CSS 类即可。信息架构增量最大 / 成本最小。

### 2. card aging (卡龄视觉强调) — 中荐
- 现状: elapsed 文字 "耗时 Xm" 在 meta 里, 无视觉突出; 长卡 task 和刚启动 task 视觉无差。
- 借鉴: 按 elapsed 阈值给卡边框/进度条加 age 提示 (如 >2h 边框微红), 或 stat 卡加 "最长卡龄" KPI。
- 罗盘判定: 契合。elapsed 已算, 加 CSS 阈值类。但 skein task 粒度大 (单 task 小时~天级), aging 阈值要按实际分布调, 非 Jira 天级标准。

### 3. Grid View (时间 × task 矩阵) — 选荐 (需用户裁)
- 现状: 只有 DAG (依赖拓扑) + 队列 (调度序), 无时间轴。
- 借鉴: Airflow Grid = run(时间轴) × task (行), 格子状态色。skein 可做 task(行) × subtask/阶段(列) 矩阵, 或 task × 天(时间轴)。
- 罗盘判定: **半契合**。skein 无多 run 概念 (task 一次性), 但 task/subtask/阶段三维天然适合矩阵。成本中 (新视图 + 布局), 收益取决于用户是否需要"一眼看全局状态分布"。**需用户裁: 加矩阵视图 vs 沿用 DAG**。

### 4. 轻量甘特/时间条 — 弱荐 / 谨慎
- 现状: 无时间轴, 仅文字耗时。
- 借鉴: frappe-gantt 思路 (SVG 条, start/end 横轴), 不引库 (skein 已有 Sugiyama SVG 基建, 自绘时间条同档成本)。
- 罗盘判定: **谨慎**。skein task 多无明确 start/end 计划 (pending 无预期开始), 甘特核心=时间区间, skein 数据撑不起完整甘特 (只有 elapsed 回顾, 无 forward 计划)。若只做"已耗时间条"=重复进度条。**需用户裁: 甘特是否对 skein 场景有意义**。

### 5. 趋势指标 (burndown/cycle-time) — 弱荐
- 现状: dashboard 页有完成率环/状态分布, 但无时序趋势。
- 借鉴: burndown (剩余 task 随时间) / cycle-time (task 从 create 到 done 的耗时分布)。
- 罗盘判定: **弱**。skein 是单项目线性推进 (非 sprint 迭代), burndown 价值有限; cycle-time 需历史数据 (task.json 有 created/finished 可算, 但单项目样本少)。收益/成本比低, 除非用户要长期复盘。

### 6. WIP 限制告警 — 中荐
- 现状: 无并行上限视觉; skein 有 `max_active` 槽位概念 (config), 但看板不显。
- 借鉴: stat 卡 "进行中" 显示 `3/4` (active 数 / max_active), 超限高亮。
- 罗盘判定: 契合。max_active 已在 config, `_board_data` stats 已有 active 计数, 加除数显示即可。

---

## 四、可视化形式选型 (DAG vs Gantt vs Kanban vs Timeline)

| 形式 | 适配 skein | 判定 |
|---|---|---|
| **DAG (现有)** | task/subtask 依赖拓扑 + 关键路径, skein 核心 | 保留主力, 已比多数看板强 |
| **Kanban (列)** | skein task 状态只有 4 态且非流转密集, 列式信息密度低 | 不适合 (Linear/Trello 的列式依赖人拖卡, skein 状态自动流转) |
| **Gantt** | 需 start/end 计划, skein 数据撑不起 | 弱 (见借鉴点 4) |
| **Timeline/时间轴** | 适合"task 何时启动/完成"回顾 | 中 (card aging 是其轻量替代) |
| **Grid 矩阵** | task × 阶段/subtask, 全局状态分布 | 选荐 (借鉴点 3) |

**结论**: skein 选 DAG 是对的 (编排场景依赖 > 时间)。增量优先级 = 阻塞 flag > card aging > WIP 告警 > Grid 矩阵 > (甘特/趋势, 需裁)。

---

## 五、交互 / 主题 / 性能

**交互 (筛选/排序/折叠/主题)**:
- 现有: 状态多选筛选 + 搜索 (id/名/描述, 高亮+DAG 节点灰) + DAG 维度切换 + 详情折叠 + 主题切换 + motion 开关。已较全。
- 缺: 按 agent/worktree/阶段 筛选; 按耗时/进度排序; 卡片折叠全部 (现 details 默认 open, 多卡时页面长)。
- 罗盘判定: 筛选/排序增量值得做 (数据现成), 全折叠是小优化。

**主题/配色 (4 主题 6 配色是否过重)**:
- 实测: 现码只 2 主题 (skein/skein-dark), 非 4 主题 6 配色 (prompt 描述与码不符, 可能指 seed 派生的虚拟变体或历史版本)。令牌系统 (oklch seed × 明度锚点) 是**成熟做法**, 非过重 — 主流设计系统 (Tailwind/Radix) 都走 token 派生。
- 动效 (晨曦呼吸+流光描边+进度条流光) 是 skein 签名, `data-motion=full` 默认开 + `.voff` 视口外门控已处理性能。
- 罗盘判定: 主题不过重, 保留。若用户嫌动效重 → motion 默认改 off 或加更多档 (full/reduce/off)。

**token/性能 (前端是否可更轻)**:
- 旧 board: 无框架, 命令式 innerHTML, 单页 ~860 行 JS+CSS, 已极轻。
- 新 webapp: petite-vue (vendored IIFE, 非完整 Vue), 7 页 SPA。轻量但比旧 board 重。
- 软刷新拉 JSON 重渲染 = 标准轻量模式, 无需 SSE/morphdom (现 WS+reload 够)。
- 罗盘判定: 已足够轻, 无需再瘦。唯一可议: 旧 board 与新 webapp 并存, 长期维护两套前端是否值得 (非 UI 优化范畴, 留 main 裁)。

---

## 六、需要 (用户裁 / 信息缺口)

1. **Grid 矩阵视图 vs 沿用 DAG** — 借鉴点 3, 需用户拍板是否要矩阵视图 (成本中, 收益看场景)。
2. **甘特/时间轴是否对 skein 有意义** — 借鉴点 4, skein 无 forward 计划数据, 甘特可能空转。
3. **4 主题 6 配色描述与现码不符** — 实际 2 主题; 需用户澄清是否指预期目标 (要做 4 主题?) 还是历史版本残留。
4. **趋势指标是否要** — burndown/cycle-time 收益依赖长期多项目数据, 单项目场景弱。
5. **Trellis 具体指什么** — 外搜未找到名为 "Trellis" 的看板产品 (只有 Trello), 需用户澄清是否笔误或指特定 repo。

---

## 七、证据来源

**本地 (file:line)**:
- `plugins/tools/skein/scripts/skein.py` L1495-1693 (`_board_data`), L1695-1735 (`_board_html`), L1245-1294 (`_crit_weight`/`_pending_queue`), L2210-2300 (serve endpoints)。
- `plugins/tools/skein/assets/board/board-render.js` L304-405 (renderBoard), L49-300 (dagHtml/overview/卡片)。
- `plugins/tools/skein/assets/board/switcher.js` L1-180 (主题/筛选/搜索/DAG 切换)。
- `plugins/tools/skein/assets/board/base.css` L1-141 (令牌/bar/DAG 染色), `themes/skein.css` L1-105。
- `plugins/tools/skein/assets/board/shell.html` (模板 token)。
- `plugins/tools/skein/assets/webapp/` (index.html + src/pages/{dashboard,board,queue,task,spec,archive}.js + router.js)。

**外部** (经 agent-reach AVAILABLE, 本次降级用 WebSearch — agent-reach doctor 未跑, 但 WebSearch 已覆盖网页/社区/dev 三类, 视频类未覆盖):
- 看板信息架构: [Wrike kanban cards](https://www.wrike.com/kanban-guide/kanban-cards/), [Atlassian kanban cards](https://www.atlassian.com/agile/kanban/cards)。
- WIP 限制: [Atlassian WIP](https://www.atlassian.com/agile/kanban/wip-limits), [Businessmap](https://businessmap.io/kanban-resources/getting-started/what-is-wip)。
- 阻塞可视化: [marcusoft](https://www.marcusoft.net/2017/02/comments-on-board-practices.html), [Nave](https://getnave.com/blog/blocked-work-in-kanban/)。
- Airflow UI: [Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/ui.html)。
- 甘特库对比: [Bryntum](https://bryntum.com/blog/top-5-javascript-gantt-chart-libraries/), [FusionCharts](https://www.fusioncharts.com/blog/best-gantt-chart-library/)。
- 敏捷指标: [Atlassian metrics](https://www.atlassian.com/agile/project-management/metrics), [Sourcegraph 2026](https://sourcegraph.com/blog/agile-metrics-what-to-track-and-why-they-matter-2026)。
- 编排器对比: [ZenML](https://www.zenml.io/blog/orchestration-showdown-dagster-vs-prefect-vs-airflow)。
- 终端看板: [taskwarrior-tui](https://github.com/kdheepak/taskwarrior-tui)。
- 轻量实时: [Morphdom+WS](https://sdehm.dev/posts/making-a-static-blog-dynamic/), [SSE](https://dev.to/lovestaco/real-time-data-without-websocket-overhead-3h5j)。
