# SKEIN 领域词汇 (glossary)

架构评审 (deepening) 引入的模块概念, 供后续探索复用同一命名, 不再各起别名。
架构词汇沿用 `/codebase-design` (module/interface/depth/seam/adapter/leverage/locality)。

## 深模块概念

- **Snapshot** — 一次目录扫描得到的 task/subtask 内存快照 (`tasks: list[dict]` 来自 `_render_tasks()`)。惰性: prd.md/design/findings 按需读 (`snap.prd(tid)`), dashboard/queue 只用 `snap.tasks` 不碰盘。所有 board 视图的统一输入, 每请求构造一次。取代原来 6 个视图方法各自 `_all()`/`_render_tasks()`/逐 task 读盘。

- **view (视图投影)** — `view(snapshot) → dict` 的纯函数族 (module-level, 无 `self`)。board_data / dashboard / queue / task_detail / archive_list / search。接口即测试面: 喂假 Snapshot 即可断言, 无需 git 临时仓。

- **DataSource** — `build_app(ds)` 消费的只读数据面 Protocol seam: 6 视图法 (经 Snapshot) + rev/spec/exec/config/资产目录。真实 `Skein` 结构性满足 (无需继承), 测试用假源覆写单个端点即证路由走注入源 = 两 adapter = 真 seam, 令路由脱 uvicorn 经 TestClient 单测。

## 既有核心概念 (评审勘察所得)

- **幽灵骨架 (ghost skeleton)** — 顶层索引 `task.json` 存在但 per-task 目录 `task.json` 缺失。per-task 目录是真值源, 顶层是去规范化镜像。调度/mutation 走**严格** `_all()` (幽灵骨架不可派发/归档), 看板只读走**宽松** `_render_tasks()` (镜像补齐, 容忍幽灵骨架)。

- **真分层 (tiered layout)** — 主看板 DAG 的布局规则 (`layoutTiered`): **一行 = 一个依赖深度**。层号 = 最长路径深度 (Kahn 推进, 环上节点按原序补进保证全量绘制), 层内按 barycenter (前驱平均 x) 排两遍, 一行放不下就折行 (整层仍是同一深度的相邻几行), 层内居中且永不超宽。曾因「98 张卡摊成 66 行 15500px」被 ADR 0001 判死, 但那 15500 = 66 行 × **220px 行高** —— 行高是卡片尺寸给的, 不是分层算法给的。节点降到 190×52 / 120×32 后, 同样的层数只占 2326px, 回绕 0。见 ADR 0002 (ADR 0001 已 Superseded)。子任务迷你 DAG 仍走 `layoutPacked` 分层装箱。

- **节点密度两档 (density)** — `DAG_DENSITY` 的 `compact 190×52` (标题 + id/子任务进度两行) 与 `mini 120×32` (色点 + 标题一行), 详情两档都靠 hover popover。分层排布下画布高 = 层数 × 节点高, 所以**节点尺寸是布局的自变量**, 不是纯样式。默认档由 `autoDensity(h, viewH)` 算: 先按 compact 排, 高过 `max(600, 视口高) × 3` 才降 mini —— 刻意不用「> N 个任务」的节点数阈值, 图窄或任务少时 compact 本来就装得下。用户手动切换存 `localStorage['skein.dag.density']`, 再点一次回自动。

- **边捆绑 (edge bundling)** — 扇入 ≥3 的**跨行**长边合流到一条主干竖线 (走目标卡左侧的列间通道)，各源先下探到自己所在行的行间通道再横向并入。真实数据里 `m8-version` 单点扇入 31，不捆就是 31 根贯穿全高的竖线。主干 x **不过通道错开 (`chan`)** —— 错开即散束，合流全靠共用同一 x。同行/相邻短边不参与 (本来一格到位，绕主干反而更长)。

- **边语义色 (edge kind)** — 连线 `from → to` 表示「to 依赖 from」，颜色由 **from 的可执行性**决定: 绿 `ready` (from 已完成，依赖已满足) / 黄 `blocked` (from 未完成但它自己的依赖全 done，现在就能跑) / 红 `stuck` (from 自己也有未完成依赖，这条链短期解不开)。图外 id 视为已满足。

- **task 状态机** — 待处理 ⇄ 调研中(research) → [confirm 用户门, 吸收原 start 职责] → 进行中 → [check] → 检查中 → [finishing] → 收尾中 → [finish] → 已完成。**进行中**占 `pools.work` 槽, **检查中/收尾中**占 `pools.gate` 槽; 归档=保留期后目录迁移, 非状态。

- **supertask** — `kind=supertask` 的顶层父聚合层, 自身不写代码不占 worktree, 只聚合一组 `parent` 指向它的 child `task` (各 child 自成完整 plan→exec→check→finish 闭环)。与默认 `kind=task` 的区别: 普通 task 独立闭环, supertask 是纯归属容器。`parent`/`kind` 是唯一受控父子字段 (深度限 2 层: supertask→task→subtask, 不可再嵌套), 与 `deps` (执行顺序 DAG) 正交。存量 task 事后改挂用 `skein task parent <id> --set <parent-id>` (`--set ""` 摘除), 复用 `create --parent` 同一条链校验 (自引用/父不存在/深度超限拒)。supertask finish 前要求全部 child 已完成, 否则脚本硬拒 (聚合收束门)。
