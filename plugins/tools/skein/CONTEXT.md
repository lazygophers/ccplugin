# SKEIN 领域词汇 (glossary)

架构评审 (deepening) 引入的模块概念, 供后续探索复用同一命名, 不再各起别名。
架构词汇沿用 `/codebase-design` (module/interface/depth/seam/adapter/leverage/locality)。

## 深模块概念

- **Snapshot** — 一次目录扫描得到的 task/subtask 内存快照 (`tasks: list[dict]` 来自 `_render_tasks()`)。惰性: prd.md/design/findings 按需读 (`snap.prd(tid)`), dashboard/queue 只用 `snap.tasks` 不碰盘。所有 board 视图的统一输入, 每请求构造一次。取代原来 6 个视图方法各自 `_all()`/`_render_tasks()`/逐 task 读盘。

- **view (视图投影)** — `view(snapshot) → dict` 的纯函数族 (module-level, 无 `self`)。board_data / dashboard / queue / task_detail / archive_list / search。接口即测试面: 喂假 Snapshot 即可断言, 无需 git 临时仓。

- **DataSource** — `build_app(ds)` 消费的只读数据面 Protocol seam: 6 视图法 (经 Snapshot) + rev/spec/exec/config/资产目录。真实 `Skein` 结构性满足 (无需继承), 测试用假源覆写单个端点即证路由走注入源 = 两 adapter = 真 seam, 令路由脱 uvicorn 经 TestClient 单测。

## 既有核心概念 (评审勘察所得)

- **幽灵骨架 (ghost skeleton)** — 顶层索引 `task.json` 存在但 per-task 目录 `task.json` 缺失。per-task 目录是真值源, 顶层是去规范化镜像。调度/mutation 走**严格** `_all()` (幽灵骨架不可派发/归档), 看板只读走**宽松** `_render_tasks()` (镜像补齐, 容忍幽灵骨架)。

- **满铺网格 (grid layout)** — 主看板 DAG 的布局规则: 卡片按拓扑序行主序填格, **一行内可以并排不同依赖深度的卡**。与分层排布 (Sugiyama, 行=依赖层) 相对 —— 后者在「画布不超视口 + 卡片不缩 + 全量绘制」三约束下会把 98 张卡摊成 66 行 15500px (44 行只坐 1 张)。满铺压到 33 行 7316px。代价是行不再表达依赖深度，方向靠箭头 + 边语义色认。见 ADR 0001。子任务迷你 DAG 不适用 (规模小，仍走分层)。

- **边语义色 (edge kind)** — 连线 `from → to` 表示「to 依赖 from」，颜色由 **from 的可执行性**决定: 绿 `ready` (from 已完成，依赖已满足) / 黄 `blocked` (from 未完成但它自己的依赖全 done，现在就能跑) / 红 `stuck` (from 自己也有未完成依赖，这条链短期解不开)。图外 id 视为已满足。

- **task 五态机** — 待处理 → [confirm 用户门] → 就绪 → [start] → 进行中 → [check] → 检查中 → [finish] → 已完成。仅**进行中**占 `max_active` 槽; 归档=保留期后目录迁移, 非状态。
