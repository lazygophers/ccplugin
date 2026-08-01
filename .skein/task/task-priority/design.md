# task 优先级 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 出发点: 这是补缺口, 不是从零建

字段早就有 (0-10 数字, 默认 5), 列表读取也早就按优先级降序排了。但两个断点让它形同虚设:
建 task 的命令没有对应参数 (于是永远取默认值), 认领的最终排序又不看优先级。两个断点都补上, 这
功能才算通。

## 取值: 四档枚举, 存量按映射迁移

落盘存**稳定的机器值** (如 urgent/high/normal/low), 展示层映射成中文档位 —— 文案会改, 落盘值
不该跟着变。

存量 0-10 数字按分段映射, 映射表必须写死并有用例钉住 (否则每次改都可能悄悄改变存量语义):

| 原数字 | 新档位 |
|---|---|
| 8-10 | 紧急 |
| 6-7  | 高 |
| 4-5  | 中 (默认 5 落这里) |
| 0-3  | 低 |

迁移前先做快照, 保证可逆。迁移是一次性写盘动作, 会打乱 task.json 的 mtime —— 而看板的软刷新
靠 mtime 判变化, 所以迁移后看板会整体刷一次, 这是预期内的, 不是 bug。

## 排序: 优先级抬到拓扑深度之上

认领现在的排序键是 `(拓扑深度降序, task 登记序, subtask 登记序)`。改成:

    (优先级降序, 拓扑深度降序, task 登记序, subtask 登记序)

**取舍 (用户裁定, 代价已知)**: 拓扑深度优先本来是个真优化 —— 先跑挡住最多人的, 总工期最短。
优先级抬到它上面, 意味着一个标了「紧急」但没人依赖的任务会插到关键路径前面, 总工期可能变长。
接受这个代价, 因为「标了紧急却不先跑」比「总工期长一点」更让人无法信任这个旋钮。

另一处要改: 现有代码把执行中的 task 视为同级, 明确不比优先级 (有注释写明是刻意的)。这与「优先级
参与排队」直接冲突, 本次改掉 —— 执行中的 task 之间同样按优先级排。

依赖硬优先不需要额外代码: 依赖未满足的 task 根本进不了就绪集, 排序阶段见不到它。禁写「高优先级
可越过依赖」的例外分支。

同档稳定序: 排序键后面几项本就是登记序, 用稳定排序即可。全同档时第一项相等, 结果退化为改动前的
顺序 —— 零回归由此成立, 不需要额外分支。

## 改优先级: 任意状态可改

优先级是调度旋钮而非规划契约, 不锁状态 (与工时/deps 不同)。改动只写字段, 碰不到执行中的槽, 所以
「不打断已在跑的」是结构性成立而非靠代码保证。

## 页面改优先级: 复用白名单命令通道

看板已有一条「页面触发白名单命令」的通道 (确认规划、归档等都走它)。改优先级只需把新命令加进白名单
+ 前端加个控件, **不新增专用写接口** —— 少一个写入口就少一处要防的地方。

## 测试接缝 (seam)

- **唯一主接缝 = 认领命令的返回顺序**。构造若干 task 跑认领, 断言返回的 id 序列。四档排序、优先级
  压过拓扑深度、依赖优先、同档稳定、全同档零回归五种场景全部只看这一个外部输出。
- 其中「优先级压过拓扑深度」是本次改动的核心断言 —— 构造一个低拓扑深度但高优先级的 task, 断言它
  先被认领。这条缺了, 等于核心改动没验。
- **迁移接缝 = 迁移前后的落盘档位**: 构造覆盖四个区间的老数据, 断言档位符合映射表。
- 页面改优先级靠浏览器人工核对, 不写 UI 自动化断言。

## p2 完成留痕 (2026-08-02)

**改动文件 (file:line, worktree `.worktrees/skein-task-priority`)**:
- `skeinlib/cli.py:38-42` — `create` 加 `--priority` 参数 (不带 argparse choices, 原样透传给
  `validate_priority`, 免两处错误信息各抄一份合法值列表); 新增 `priority` 子命令 (`id [--set]`),
  查/改 task 优先级
- `skeinlib/cli.py:175/195` — dispatch 挂 `"priority": sk.lifecycle.priority`; `priority` 进
  `MUTATING` (会写 task.json, 需工作区锁)
- `skeinlib/cli.py:95` — `list --json` help 文案补 `priority` 字段
- `skeinlib/lifecycle.py:179-189`(新增 `priority` 方法, 紧邻 `deps` 之前) — 无 `--set` 时查当前值
  (兜底 `PRIORITY_DEFAULT`), 有则走 `validate_priority` 校验并落盘; **不判 `t["status"]`** (对比
  `repos`/`estimate`/`deps` 都锁 pending/ready) —— design.md 已定「调度旋钮不是规划契约, 任意状态
  可改」, 只改字段不碰执行槽, 「不打断已在跑的」结构性成立
- `skeinlib/query.py` — `status()` 单 task 文本行插入 `priority` 列; `list_()` 每行插入
  `priority` 列; `_brief()` (被 `status --json` 与 `list --json` 共用) 补 `priority` 键

**入口覆盖**: 建 task `--priority` 未传落 `normal`(复用 p1 `validate_priority`, 未另写校验);
非法值经 `create --priority` 与 `priority --set` 两条入口均报 `SkeinError` 且列出四个合法值
(同一份 `PRIORITIES`, 无重复硬编码); 单 task `status` 与 `list`(含 `--json`) 均可见真实优先级值。

**测试**: 新增 `tests/test_priority.py` 6 条 CLI 用例 (`test_create_with_priority_flag_persists` /
`test_create_with_illegal_priority_rejected_and_lists_four_values` /
`test_priority_cmd_query_and_set` / `test_priority_cmd_rejects_illegal_value` /
`test_priority_cmd_changes_active_task`(直改盘面 status=进行中 模拟已 start, 断言仍可改) /
`test_status_and_list_show_priority`)。`pytest tests/test_priority.py` — **25 passed, 0
failed**(19 条 p1 + 6 条 p2 新增)。

全量套件 `pytest tests/ --deselect tests/test_mypy_strict.py` — **379 passed, 5 failed**,
5 个失败经 `git stash` 逐一核实为**p1 完成时已记录的同一批 baseline red**
(`test_config_cli::test_show_json` / `test_spec_autofix.py` 两条 / `test_views_char::
test_views_characterization` / `test_mypy_strict::test_mypy_strict_clean`), stash 前后失败集
完全一致, 非本 subtask 引入。`mypy --strict` 单独跑本次改动 4 个文件
(`cli.py/lifecycle.py/query.py/priority.py`) 报的 6 处错误全部位于 `serve.py`/`boardsource.py`
(跨模块引用被拉进检查图), 经比对与 p1 留痕记录的既有错误一致, 本次改动文件自身 0 新增错误。

**doctor**: 跑出与 p1 留痕记录相同的 1 条既有错误 (`spec-map-namespace: worktree 路径不存在`,
环境性, 与本次改动无关), 未引入新错误。

**p2 范围外, 明确留给后续 subtask**: 认领排序纳入优先级/优先级压过拓扑深度 (p3)、看板展示 + 页面
直接改优先级 (p4)、doctor 非法优先级值体检 (p5)。

## p1 完成留痕 (2026-08-02)

**改动文件 (file:line)**:
- `skeinlib/model.py:47-55` — 新增 `P_URGENT/P_HIGH/P_NORMAL/P_LOW` 四常量 + `PRIORITIES` tuple +
  `PRIORITY_DEFAULT="normal"` + `PRIORITY_RANK` (排序权重表, 保留原有「数字越大越靠前」的相对顺序,
  不改排序结构本身 — 「优先级压过拓扑深度」是 p3 的活, 这里只保证类型换了排序不崩)
- `skeinlib/priority.py` (新增) — `validate_priority(raw)` (None→"normal" 默认档, 非法值抛
  `SkeinError` 且列出 `PRIORITIES` 全部四个合法值); `priority_from_legacy(n)` (0-10→四档,
  8-10 紧急/6-7 高/4-5 中/0-3 低, 与 design.md 映射表逐字一致); `migrate_priority_values(root,
  tasks_dir, archive_dir)` (扫未归档 + 已归档 task.json, priority 是数字才处理 → 幂等; 改前
  copy2 原文件进 `.skein/.priority-migration-backup/<时间戳>/`, 结构照抄源相对路径)
- `skeinlib/lifecycle.py:82` — `create` 的 priority 落盘改走 `validate_priority(getattr(a,
  "priority", None))` (CLI 尚无 `--priority` 参数, 这是 p2 的活; 此处只保证 create 内部字段合法)
- `skeinlib/store.py:96/144/171/179` — 默认值 `t.get("priority", 5)` → `PRIORITY_DEFAULT`;
  排序键 `-(priority or 5)` → `-PRIORITY_RANK.get(t.get("priority", ""), PRIORITY_RANK[PRIORITY_DEFAULT])`
- `skeinlib/cli.py` — 新增 CLI 子命令 `migrate-priority` (无参, 幂等可重跑), 挂进 `dispatch` +
  `MUTATING` (会写 task.json, 需工作区锁)
- `skeinlib/admin.py` — `Admin.migrate_priority()`: 调 `migrate_priority_values` + 迁移后
  `store.sync()` 刷新顶层镜像索引 `.skein/task.json` (否则镜像仍缓存旧数字)
- `skeinlib/derivatives.py` — 登记 `.priority-migration-backup/` 为衍生物 (可重建快照, 非真值,
  不入库) — 缺这条 `test_derivatives_guard.py::test_no_unregistered_derivative_writes` 会红

**映射实现方式**: `priority_from_legacy` 纯函数, 分段 if/elif, 与 design.md 表格逐字对齐,
用例 `test_priority_from_legacy_boundaries` 覆盖四区间 + 边界值 (0/3/4/5/6/7/8/10)。

**快照与回滚方式**: 迁移改写前, 逐文件 `shutil.copy2` 原样拷贝进
`.skein/.priority-migration-backup/<YYYYmmdd-HHMMSS>/` (镜像源相对 root 的路径结构)。回滚 =
把该时间戳目录下的文件按相对路径拷回原位 (无需专用回滚命令, 目录结构本身就是操作说明)。备份目录
已登记进 derivatives.py, 走 `.skein/.gitignore` 生成链路不入库 (仓库根现有 `.skein/.gitignore`
本身已滞后于 `derivatives.py`, 缺 vision.md/index.html/.edit-tally 等多条 — 这是既有技术债,
不属本 subtask 范围, 未处理)。

**真实存量数据迁移结果**: 在本 worktree 对仓库根 `.skein/task/` 实跑 `skein migrate-priority`
——迁移 32 个 task.json (14 个未归档 + 18 个已归档), 全部原值 `priority: 5` → `"normal"`
(与「存量几乎都是 5, 迁移后绝大多数落中档」的预期一致)。二次重跑幂等, 报告「无待迁移」。

**测试结果**: `pytest tests/test_priority.py` — **19 passed, 0 failed**。全量套件
`pytest tests/ --deselect tests/test_mypy_strict.py` — **373 passed, 5 failed**, 5 个失败
逐一用 `git stash` 核实为**改动前既有的 baseline red**(`test_config_cli::test_show_json`、
`test_spec_autofix.py` 两条、`test_views_char::test_views_characterization`、
`test_mypy_strict::test_mypy_strict_clean` 里的 pre-existing 47 处 mypy 错误, 均与
priority.py/store.py/lifecycle.py 等本次改动文件无关), 非本 subtask 引入。`mypy --strict`
单独跑本次改动的 6 个文件 (`priority.py/model.py/store.py/lifecycle.py/admin.py/cli.py`)
**0 错误**(serve.py/boardsource.py 各自的既有错误经 `git stash` 核实为改动前已存在, 非本次引入)。

**doctor**: `skein doctor` 在本 worktree 跑出 1 条既有错误 `spec-map-namespace: worktree
路径不存在` ——经 `git stash` 核实改动前后一致存在 (本 worktree 未 checkout 该 task 的子
worktree, 环境性问题, 与 priority 迁移无关), 迁移动作本身未引入新的 doctor 错误。

**p1 范围外, 明确留给后续 subtask**: CLI `--priority` 创建参数与改优先级命令 (p2)、认领排序纳入
优先级/优先级压过拓扑深度 (p3)、看板与详情页展示 (p4)、doctor 新增非法优先级值体检 (p5)。
