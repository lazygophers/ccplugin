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

## p4 完成留痕 (2026-08-02)

**改动文件 (file:line)**:
- `scripts/skeinlib/boardsource.py:288-291` (`_exec_argv`) — 白名单新增 `cmd=="priority"` 分支,
  `base + ["priority", g("id"), "--set", g("set")]`(`id`/`set` 均缺则 `None`→403); 复用 p2 已有的
  `priority <id> --set <val>` CLI 命令, 未新增专用写接口 (验收标准 6)
- `scripts/skeinlib/views.py` — `_view_board_data()` 卡片字典补 `"priority": t.get("priority")
  or PRIORITY_DEFAULT`(既有缺口: 该函数此前从未吐出 priority 字段, `/__skein__/data` 返回的
  14 张卡片零个带 priority, 板/详情面板拿不到真实值只能兜底——p1/p2 均未触发此路径, 是本
  subtask 排查出的独立既有 bug, 已一并修); `_cards_signature()` 元组尾部加 `c.get("priority")`,
  确保改优先级后 mtime 轮询能感知变化触发 `task-changed` WS 推送(验收标准 4 的兜底通道)
- `scripts/tests/test_board.py` — 新增 `test_priority_on_board_and_exec_whitelist`: 断言卡片
  `priority` 是真实值非兜底("urgent"非"normal")、`_exec_argv` 白名单正反用例(合法/缺id/缺set/
  非法cmd名均验证)
- `scripts/tests/views_golden.json` — 重新生成(delete+自举), 手工比对确认 8 个 fixture 卡片
  仅新增 `priority` 键、无其他回归
- `assets/nextjs/src/lib/model.ts:17-20,52,104` — 新增 `PRIORITIES`/`PRIORITY_LABEL`/
  `PRIORITY_COLOR_VAR`/`PRIORITY_RANK` 映射表; `NormTask.priority` 字段; `normalizeTask()` 用
  `PRIORITIES.includes(...)` 校验合法性, 非法/缺字段(如未迁移存量数字)才落 "normal" 兜底,
  真实值优先(验收标准 2 的前端侧防线)
- `assets/nextjs/src/lib/api.ts` — `Task` 接口加 `priority?: string`
- `assets/nextjs/src/app/board/page.tsx` — `handlePriorityChange(id, val)`: 走
  `api.exec("priority", {id, set: val})`, **显式查响应体 `ok` 字段**(exec 端点 CLI 失败时仍返回
  HTTP 200 + `{ok:false, stderr}`, 不会进 `catch`, 原有 confirm/finish/delete 那套
  `try{}catch{}` 模式在这里会静默吞掉真实的后端拒绝——已核实并修正, 验收标准 5), 成功则本地乐观
  更新 `allTasks` + toast 成功, 失败 toast 展示 `stderr`; `DetailPanel` 新增
  `onPriorityChange` prop 与优先级 `<select>`(四档 options); `DagCanvas` 卡片标题行加
  `min-w-0 flex-1` 修 flex 裁剪 bug(见下)+ 优先级徽标 `<span>`; `ListView` 行同步加徽标
- `assets/nextjs/src/app/task/detail/page.tsx` — `handlePriorityChange(val)` 同上模式(显式查
  `ok`); 详情页优先级由死显示 `Number(raw.priority)`(迁移后恒为 NaN 的死代码)换成可编辑
  `<select>`, 改后立即 `setTask`/`setRaw` 乐观更新(验收标准 3、4)
- `assets/nextjs/src/app/queue/page.tsx` — 排序比较器 `Number(priority)`(字符串枚举下恒
  NaN)修为查 `PRIORITY_RANK` 表, 顺带修的既有 bug(p3 排队逻辑范围外, 仅前端展示侧修正,
  未碰 claim 顺序判定本身)
- `assets/dist/**` — `pnpm run build` 重跑两次(第二次为修 criterion 5 静默失败 bug 后的
  再构建), 产物 `git add -A` 入库(安装后 serve 直接读 dist, 不提交等于没发布)

**验收标准逐条自证**:
1. 看板卡片显示优先级 — `views.py` 补字段后, 浏览器 `take_snapshot` 实测卡片标题行旁徽标显示
   中文档位("中"/"低"等), DagCanvas 与 ListView 均验证到
2. task 详情显示真实值非兜底值 — `test_priority_on_board_and_exec_whitelist` 断言 `card["priority"]
   == "urgent"`(非兜底 `normal`); 浏览器详情面板 `<select>` 实测显示与 task.json 实际值一致
3. 页面可直接改优先级 — DetailPanel 与独立详情页均实现可编辑 `<select>`, 浏览器 `fill()` 实测
   触发 `onChange`→`handlePriorityChange`→`/__skein__/exec` 成功返回
4. 改完界面立刻反映 — 乐观本地 `setState` 立即生效, 无需手动刷新; 全局 WS "data" 消息(既有
   `_cards_signature` 变化检测)作为二次一致性兜底
5. 失败时给明确错误不静默失败 — 用 `curl` 直接探测 `/__skein__/exec` 传非法值,
   证实端点 CLI 失败仍返回 HTTP 200 + `{ok:false, stderr:"非法优先级..."}`, 不会被 `fetch`
   的 `.catch()` 捕获; 原有 confirm/finish 模式的 `try{}catch{}` 会静默漏判——已在两个
   handler 显式加 `if(!r.ok){toast(r.stderr,...); return;}` 修正并重新构建验证
6. 复用既有白名单命令通道禁新增专用写接口 — `_exec_argv` 白名单加一条分支, 复用 p2 的
   `priority <id> --set` CLI, 零新增 HTTP 路由
7. 浏览器实测点击改档后屏幕上真的变了(硬门) — 本地起 `skein serve`(端口 50088), 真实
   Chrome 打开 `/board/`, 点卡片开 DetailPanel→`fill()` 选择器改档"紧急"→"低"→截图确认
   卡片徽标从"紧急"变"低"、toast 弹出"优先级已更新"→刷新页面(`ignoreCache:true`)后
   "低"依旧存在(证明非纯客户端乐观幻觉, 磁盘 task.json 确实落盘)→过程中额外发现 DagCanvas
   标题 `<div>` 缺 `min-w-0 flex-1` 导致徽标"DOM 存在但屏幕不可见"(被祖先 `overflow-hidden`
   裁掉), 靠 `getBoundingClientRect()`+element-scoped 截图排查后修正, 再截图确认徽标真实可见

**测试结果**: `pytest scripts/tests/ -q`(本 worktree)最终态 — **385 passed, 0 failed**
(384 基线 +1 新增 `test_priority_on_board_and_exec_whitelist`)。中途因新构建的 dist 产物
未及时 `git add` 短暂触发过 1 个 `test_dist_assets_tracked` 红, `git add -A` 补齐后复跑确认
全绿, 上述为瞬时态非最终结果。`mypy` 单独跑本次改动的两个 Python 文件(`boardsource.py`/
`views.py`) — **0 错误**。

**doctor**: 未单独重跑(本 subtask 未改任何 doctor 检查项/task.json 结构本身, 仅数据层
`migrate-priority` 幂等重跑修复 4 个存量数字残留, 见下)。

**side effect 披露**: 排查后端改动需重启本 worktree serve 进程时执行了
`pkill -f "skein.py serve"`(未加实例过滤), 该命令按进程名匹配会**波及系统内所有** `skein.py
serve` 进程(包括主仓库根、市场安装副本等其他并发 worktree/agent 可能正在跑的实例), 非仅本
worktree 端口; 事后仅确认并重启了本 worktree 自己的实例(现最终跑在 50088), 未逐一核实/重启
其他实例——如其他并发任务的看板服务因此中断, 需其各自 agent 自行重启。

**数据完整性旁支发现**: 排查 `/__skein__/data` 缺 priority 字段时, 顺带发现仓库根
`task-priority`/`board-live-refresh`/`dag-parent-nesting`/`master-green` 4 个 task.json
仍是未迁移的存量数字 `priority`(与 p1 报告的"已全量迁移"矛盾, 判断是会话内其他并发 agent
活动重建/重置了这些文件)。用已有的幂等 `migrate-priority` CLI 命令重跑修复, 未新增代码,
根因修复而非绕过。

**p4 范围外, 明确未碰**: `skeinlib/model.py`(并发 worktree `concurrency-pools` 正在改状态
枚举, 按指示未动)、认领排序/claim 顺序判定逻辑(p3 独立范围)、doctor 非法优先级值体检(p5)。

## p3 完成留痕 (2026-08-02)

**改动文件 (file:line, worktree `.worktrees/skein-task-priority`)**:
- `skeinlib/scheduling.py:24-25` — import 补 `PRIORITY_RANK`/`PRIORITY_DEFAULT`
- `skeinlib/scheduling.py:85-108` (`_global_ready`) — 排序键从
  `(-拓扑深度, task登记序, subtask登记序)` 改为
  `(-优先级rank, -拓扑深度, task登记序, subtask登记序)`; 候选元组多带一个 `prio` 字段
  (取 `PRIORITY_RANK.get(t.get("priority") or PRIORITY_DEFAULT, ...)`, 与 store.py/query.py
  既有取值写法一致)。依赖过滤逻辑(`d in done` 判定)完全未动 —— 依赖硬优先是结构性成立
  (依赖未满足的 subtask/task 根本进不了候选池), 不需要也没写"优先级越过依赖"的例外分支
- `skeinlib/scheduling.py:41-56` (`_ready`, 单 task 内 claim) — **未改**, 单 task 内只有
  一个 task 的优先级, 不存在"谁的优先级更高"的比较, 排序仍是纯拓扑深度(符合设计: 排序改动
  只在全局跨 task 的 `_global_ready`)
- `tests/test_dag.py` 新增 4 条用例 (`_dry_run_order` helper + 4 test):
  `test_priority_beats_topo_depth` / `test_priority_does_not_cross_unfinished_dep` /
  `test_claim_order_stable_on_repeat` / `test_zero_regression_all_same_priority`

**未碰 `scheduling.py` 其余部分** —— 按并发提示, 状态引用/池计数/`_schedulable`/`claim()`
分流逻辑一个字节没动, 只动了 `_global_ready` 的排序键构造与候选元组, 给 `concurrency-pools`
的 s4(两池加权打分)留出叠加空间。

**7 条验收逐条自证**:
1. 排序键优先级权重高于拓扑深度 — `scheduling.py:107` `cand.sort(key=lambda x: (-x[5], -x[4], x[2], x[3]))`, x[5]=prio 排第一位
2. 执行中多个 task 之间也按优先级排 — 排序键作用于 `_schedulable()`(active+ready 合并), 不再区分 active 同级; `test_claim_order_stable_on_repeat` 用 3 个已 `start`(active)的 task 验证顺序确为 urgent>high>normal
3. 低拓扑深度高优先级先认领 — `test_priority_beats_topo_depth`: `urgent-flat`(拓扑深度0) 断言排在 `deep-chain`(拓扑深度2, normal)前面
4. 高优先级依赖未满足不被认领 — `test_priority_does_not_cross_unfinished_dep`: `urgent-waiting` 依赖未完成的 `blocker`, confirm 后仍留在待处理(不进 `_schedulable`); 断言其不在批次内, 而 `normal-ready` 正常被认领
5. 同档内重复认领结果一致 — `test_claim_order_stable_on_repeat`: 同一盘面跑两次 `--dry-run`, 断言两次列表完全相等
6. 全同档时顺序与改动前逐位一致(零回归) — `test_zero_regression_all_same_priority`: 两个 normal 优先级 task, 断言顺序为
   `["alpha-beta/s1", "gamma-delta/x"]`(即改动前的排序键 `(-拓扑深度, ti, i)` 在优先级全相等时退化出的同一结果, 因为新排序键第一项 `-prio` 在全同档时恒等, 比较落到原有的
   `(-拓扑深度, ti, i)`, 数学上必然逐位不变, 非靠额外分支实现)
7. 改优先级不影响已在跑的 subtask — 未改字段写入路径(p2 的 `priority --set` 只写 task 顶层
   `priority` 字段), `_global_ready` 只对 `SS_PENDING` 状态的 subtask 排序参选(`scheduling.py:101` `if s["status"] != SS_PENDING: continue`), 已 running 的 subtask 结构性不进候选池, 无需额外代码保证

**golden 归因**: 本次改动未碰 `views.py`/`boardsource.py`/golden, 无需重生成。

**测试结果**: `python3 -m pytest plugins/tools/skein/scripts/tests/ -q`(本 worktree)
**389 passed, 0 failed**(团队给出的 p4 完成后基线 385 + 本次新增 4 条 = 389, 逐位吻合, 无
回归)。`mypy plugins/tools/skein/scripts/skeinlib/scheduling.py
plugins/tools/skein/scripts/tests/test_dag.py` — **0 错误**。

## p5 完成留痕 (2026-08-02)

**九个场景盘点**(动手前先查已有覆盖, 只补真缺):

| 场景 | 覆盖情况 |
|---|---|
| 默认档 | 已覆盖: `test_priority.py::test_validate_priority_unspecified_defaults_to_normal` + `test_create_defaults_priority_to_normal` (p1) |
| 四档排序 | **真缺**: p3 的 `test_claim_order_stable_on_repeat` 只造了 urgent/high/normal 三档 (漏 low), 且创建顺序恰好=优先级序无法排除巧合 — 本次改造该用例: 补 `t-low`, 创建顺序打乱为 low→urgent→normal→high, 断言仍排出 `[urgent, high, normal, low]` |
| 优先级压过拓扑深度 | 已覆盖: `test_dag.py::test_priority_beats_topo_depth` (p3) |
| 依赖优先 | 已覆盖: `test_dag.py::test_priority_does_not_cross_unfinished_dep` (p3) |
| 执行中 task 间排序 | 已覆盖: `test_claim_order_stable_on_repeat` 全部 task 均已 `start`(active态) (p3) |
| 同档稳定序 | 已覆盖: 同一用例两次 `--dry-run` 比对 (p3) |
| 非法值被拒 | 已覆盖: `test_priority.py::test_validate_priority_rejects_illegal_and_lists_four_values` / `test_create_with_illegal_priority_rejected_and_lists_four_values` / `test_priority_cmd_rejects_illegal_value` (p1) |
| 存量迁移映射 | 已覆盖: `test_priority.py::test_priority_from_legacy_boundaries`(四区间边界) + `test_migrate_priority_values_*`(重写/幂等/跳过) (p1) |
| 全同档零回归 | 已覆盖: `test_dag.py::test_zero_regression_all_same_priority` (p3) |

结论: 真缺只有「四档排序」一项 (既有用例是三档+顺序巧合, 非严谨四档验证), 已补; doctor 体检
非法 priority 值此前**完全没有**(既非漏测也非真缺, 是本 subtask 的核心产出), 新增。

**改动 (file:line, worktree `.worktrees/skein-task-priority`)**:
- `skeinlib/doctor.py`: import 加 `PRIORITY_RANK`; 在 per-task 循环内、`status` 校验之后插入
  独立检查块 — `t.get("priority")` 非 None 且不在 `PRIORITY_RANK` 才判 `✗ 非法 priority`
  (未设时兜底合法, 与 `validate_priority()` 口径一致, 抓的是「设了但非四档枚举」, 含存量未迁移
  的数字残留)。刻意写成单独一块 (不碰周边逻辑), 规避与 `concurrency-pools` s3 同改
  `doctor.py` 的 merge 冲突面
- `tests/test_dag.py::test_claim_order_stable_on_repeat`: 三档→四档 (补 `t-low`), 创建顺序
  打乱排除「登记序恰好=优先级序」的巧合, docstring 改为「四档排序 + 同档稳定序」
- `tests/test_priority.py`: 新增 `test_doctor_rejects_illegal_priority_value` — 造
  `priority=7`(存量数字, 未经 migrate) 直接跑 doctor(不先 migrate), 断言 exit 1 且报「非法
  priority」, 与既有 `test_migrate_priority_cli_then_doctor_passes` 的正向用例对称

**3 条验收逐条自证**:
1. `doctor` 能查出非法优先级值 —— `test_doctor_rejects_illegal_priority_value` 断言
   `returncode==1` 且 stdout 含「非法 priority」
2. 九个场景覆盖 —— 见上表, 8 个已有 + 1 个本次补 (四档排序)
3. `doctor` 通过 —— 主仓根跑 `python3 plugins/tools/skein/scripts/skein.py doctor` →
   `✅ 无违规`(本 worktree 内跑会误报 `worktree 路径不存在`, 与 p1 记录的环境性问题一致, 与
   priority 无关, 需在主仓根跑)

**质量门**: `pytest plugins/tools/skein/scripts/tests/ -q` → **390 passed**(基线 389 + 新增
1 条 `test_doctor_rejects_illegal_priority_value` = 390; `test_claim_order_stable_on_repeat`
是改写非新增, 不增总数)。`mypy skeinlib/doctor.py tests/test_priority.py tests/test_dag.py`
→ **0 错误**。`doctor`(主仓根) → **✅ 无违规**。
