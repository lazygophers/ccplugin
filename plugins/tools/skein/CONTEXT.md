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

- **贴合装箱 (fit packing)** — 主看板卡片位置的真值算法 (`layoutCoord`)：逐张按拓扑序落位，候选落点打分 = 到各邻居 (前驱 + 后继) 的曼哈顿距离 + 落点高度 (权重 1.5) + 回绕惩罚 (0.6)，取最低分；落点 y 由 **skyline** (逐桶记录当前占用底沿) 给出，卡自动贴着已放的卡长上去，所以面积不会退化。跑两遍 —— 第一遍只有前驱已定位，第二遍拿第一遍坐标让前驱后继一起参与。**不是力导向**：纯 barycenter 实测把画布拉到近两倍高 (9112 vs 4946)、边长翻倍，已弃。满铺网格 (`layoutGrid`) 降级为它的初始拓扑序与尺寸来源。见 ADR 0001。

- **行高自适应 (row-adaptive height)** — 满铺网格里卡高按内容算 (`cardHeight`: 描述估行数 + 有无子任务)，行高取该行最高的那张，行内仍**顶对齐**。等高网格会让整张画板被最长的那条描述定调子；完全 masonry 则会同时拆掉蛇形行序与行间走线通道，故只放开行高、不放开行内对齐。`node.rowH` 带出行底 —— 走线找通道必须用它而非卡自身 `h`，否则通道会画进同行更高卡的肚子里。

- **边捆绑 (edge bundling)** — 扇入 ≥3 的**跨行**长边合流到一条主干竖线 (走目标卡左侧的列间通道)，各源先下探到自己所在行的行间通道再横向并入。真实数据里 `m8-version` 单点扇入 31，不捆就是 31 根贯穿全高的竖线。主干 x **不过通道错开 (`chan`)** —— 错开即散束，合流全靠共用同一 x。同行/相邻短边不参与 (本来一格到位，绕主干反而更长)。

- **边语义色 (edge kind)** — 连线 `from → to` 表示「to 依赖 from」，颜色由 **from 的可执行性**决定: 绿 `ready` (from 已完成，依赖已满足) / 黄 `blocked` (from 未完成但它自己的依赖全 done，现在就能跑) / 红 `stuck` (from 自己也有未完成依赖，这条链短期解不开)。图外 id 视为已满足。

- **task 五态机** — 待处理 → [confirm 用户门] → 就绪 → [start] → 进行中 → [check] → 检查中 → [finish] → 已完成。仅**进行中**占 `max_active` 槽; 归档=保留期后目录迁移, 非状态。
