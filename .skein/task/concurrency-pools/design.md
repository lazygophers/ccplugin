# 并发池重构: work/gate 双池 + research 状态 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 状态机

```
                      ┌──────────────┐
                      ▼              │
  [create] → 待处理(plan) ⇄ 调研中(research)
                 │
                 │ confirm --approved   ← 人审门 + 原 start 的全部职责
                 ▼
            进行中(exec)
                 │ check
                 ▼
            检查中(check)
                 │ finishing            ← 占 gate 槽, 之后 main 才派 finisher
                 ▼
            收尾中(finishing)
                 │ finish
                 ▼
            已完成(done)
```

**删「就绪」**: 它只存在于 confirm 与 start 之间, 没人真正停在那里 —— 人审通过的下一秒就该开工。
留着等于要求调用方记住「confirm 完还得 start」, 而忘了 start 的 task 会静静躺着不被调度, 看板上
还显示得挺正常。一个门一个状态转换, 中间态多余。

**加「调研中」**: research 今天完全不在状态机里 —— 派了 researcher 之后引擎眼里这 task 还是「待
处理」, 既不占槽也答不出「它在干嘛」。加了才谈得上调度和计数。

**加「收尾中」**: 同理, 但原因更硬。gate 池要限并行 finisher, 而 finisher 是 main 派出去的 agent,
引擎看不见。只有拆成「先占槽标收尾中 → 派 finisher → finisher 跑 finish 释放槽」两步, 限制才落得
下去。一步式 `finish` 拿着工作区 flock, 天然串行, 限它没有意义。

### 转换规则

| 转换 | 触发 | 前置条件 |
|---|---|---|
| 无 → 待处理 | `create` | — |
| 待处理 → 调研中 | `research <tid>` | 至少一个 phase=research 的 subtask |
| 调研中 → 待处理 | `plan <tid>` | research subtask 全 done |
| 待处理 → 进行中 | `confirm --approved` | 人审 + subtask/prd/estimate 齐 + 原 start 全套 |
| 进行中 → 检查中 | `check` | — |
| 检查中 → 收尾中 | `finishing` | gate 池有空槽 |
| 收尾中 → 已完成 | `finish` | 合并 / 销 worktree 成功 |

**调研中禁止直达开工态**。查完资料必须回 plan 走一遍规划/总结/设计 —— 调研的产出是信息不是计划,
少了那道把信息变成计划的工序, 就会变成「查完就闷头开写」。`confirm` 在调研中态直接抛错, 提示先
`plan`。

**research 态允许增删 research subtask**。查到一半发现还要多查一样东西是常态, 逼人先退出 research
态再加纯属仪式。

## 2. subtask.phase

新增字段, 取值 `exec` | `research`, 缺省 `exec`。

缺省而非必填, 为的是老数据免迁移 —— 读到没 phase 的 subtask 一律当 exec, 语义与今天完全一致。

check / finish **不设 subtask**: 它们是 task 级一次性动作 (一个 checker / 一个 finisher 对一个
task), 天然 1:1, 用 task 状态计数就够, 造一层 subtask 是无谓的间接。

## 3. 两个池

| 池 | 上限 | 计数对象 | 为什么这样分 |
|---|---|---|---|
| work | `pools.work` (2) | 全局 phase ∈ {exec, research} 且状态=运行中的 subtask | 都在读写工作树, 抢磁盘与注意力 |
| gate | `pools.gate` (3) | 状态 ∈ {检查中, 收尾中} 的 task | 只读验证 + 收尾, 可放宽 |

两池**完全独立**: work 满不影响 check 推进, gate 满不影响派 exec。这正是拆池的目的 —— 旧设计共用
一个数字, 想放宽验证就得连带放宽执行。

task 级上限 (同时最多 N 个进行中 task) **取消**。按 subtask 计数后它是冗余的: 十个进行中 task 的
running subtask 总和一样受 work=2 卡死, 再加一层只会两套上限互相干扰, 解释成本翻倍。

## 4. work 池出线打分

三项加权, 分高者出线:

```
score = 关键路径权重 × W_CRIT
      + 等待小时数    × W_WAIT
      + (phase == exec ? W_EXEC : 0)
```

- **关键路径权重**: 沿用现有拓扑深度 (最长下游链)。这就是「优先级」—— 不另立字段, 阻塞下游最多
  的活本来就该先跑。
- **等待小时数**: `now - created`, 防饿死。低权重的活等够久能翻盘, 不会永远排在后面。
- **类型加权**: exec 得固定加分。**软优先不是硬抢占** —— 同分时 exec 先走, 但等久了的 research
  能越过刚入队的 exec。硬抢占会让 research 在长执行期里彻底饿死, 而调研通常是后续规划的前置,
  饿死它等于卡住整条线。

常数放模块级, 不进 config。三个可调参数暴露给用户 = 三个没人知道该填什么的旋钮, 真需要调再说。

同分按 (task 登记序, subtask 登记序) 稳定排序, 保证同输入同输出 —— 调度结果不可复现会让排查变成
玄学。

## 5. 配置

```yaml
pools:
  work: 2   # exec + research 共享
  gate: 3   # check + finish 共享
```

`max_active` **直接删**, 不留 fallback (用户明确要求)。代价是已有工作区升级后并发限制静默变回默认
值 —— 靠 doctor 检出配置里残留的 `max_active` 并提示已废弃来兜, 至少不是无声的。

## 6. 影响面

引擎: 模型层状态枚举与别名/排序/阶段映射、生命周期 (confirm 吸收 start + 三个新转换)、调度器
(两池计数 + 打分)、只读查询、体检、看板渲染、Web 视图数据、配置默认值、CLI 子命令表。

外围: 注入给 AI 的运行配置文案、skein-flow skill 及其 references、各 agent 定义、参考文档、Web
前端 (两池占用展示)、测试。

## 7. 已知风险

- **漏改点多**: 「就绪」「start」「max_active」三个字符串散落在引擎、skill、agent、文档、前端。
  对策: 各写一个源码扫描测试钉零残留, 不靠人肉 grep。
- **老工作区静默降级**: 见 §5, 只能提示不能自动迁移 (用户不要 fallback)。
- **收尾中态被跳过**: 调用方直接从检查中跑 finish 的话 gate 限制形同虚设。对策: finish 只接受收尾
  中态入参, 逼调用方走 finishing 那一步。

## 测试接缝 (seam)

check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

**接缝 = CLI 子进程 + 落盘的 task.json** (现有 `tests/` 里 `ws` fixture 的既有做法, 复用不新建)。

理由: 状态转换与池计数的真值全在 task.json 上, 它同时也是 Web 视图、看板、doctor、注入文案的共同
上游。在这一层断言, 一次覆盖全部下游, 且完全不碰实现细节 —— 打分常数怎么调、池计数写在哪个类里,
测试都不该知道。

**不新建接缝**: 不为打分函数单独开测试入口。要保住的性质只有三条 (exec 同分优先 / 等待能翻盘 /
池上限不被突破), 全都能从 `claim` 的输出观察到; 直接测打分数值等于把常数焊死在测试里, 一调就红。

唯一的例外是三个「零残留」扫描测试 —— 它们的接缝是源码文本本身, 因为要防的正是「某个角落漏改了
但运行时碰不到」这类静默残留。

## s2 边界调整 (2026-08-02, main 裁定)

s2 原定只改 `CONFIG_DEFAULTS` 与 init 写出的 config.yaml。实测发现删 `max_active` 后
`store.py:246` (`render_task_board(t, self._cfg()["max_active"])`) 抛 `KeyError`，
而该行位于 `TaskStore.save()` —— **task.json 唯一写入口**，任何写盘命令 (create/confirm/
exec/check/finish) 都过它。s2 单独落地 = 主干瞬间全灭 (140 failed / 219 passed)。

原切法 (s2 配置 / s4 调度器 / s6 看板 / s7 文案) 要求主干在中间态连续全灭数轮，切法错误。

**裁定: s2 边界扩到「全部读取方机械替换为 `pools.work`」**，限定行为零变化 —— `pools.work`
默认 2 = 原 `max_active` 默认 2，替换后全量 pytest 必须回到 359 passed 全绿。涉及
`store.py` / `query.py` / `boardsource.py` / `lifecycle.py` / `hooks/prompt.py` / `cli.py` 文案。

**语义改造仍归原 subtask**: 两池独立计数与加权打分 → s4；取消 task 级并发上限 → s3
(s2 只换取值来源，校验本身留着)；看板两行 → s6；doctor 两池超限 → s5；全仓表述清理 → s7。

design §5「不留 fallback」指配置真值层面禁新旧双读，不禁读取方单向切新键 —— 故不加过渡兜底。

## s1 交付后的中间态不一致 (2026-08-02, main 审 golden 后记, s3 必须收口)

s1 按裁定 B 只改 `model.py` 五张表、剔除表内「就绪」条目, `S_READY` 常量留过渡。这产生一个
**跨表不一致的中间态**, 记在这里免得 s3 执行者当成自己引入的 bug:

- 6 个消费文件 (lifecycle/scheduling/dag/query/doctor/views) 仍在往 task.json 写 `S_READY`,
  所以 task 的 `status` 照旧是「就绪」;
- 但 `PHASE_OF` 已删掉 `S_READY: "ready"`, 就绪态 task 的 `stage` 落到兜底值 `"plan"`;
- `STATUS_ORDER` 也删了 `S_READY`, 就绪态 task 在看板排序里掉到末尾。

净效果: **`status="就绪"` 而 `stage="plan"`, 且排序位置改变**。

**main 对 golden 重生成的审计结论 (放行依据)**: s1 连带重生成了 `tests/views_golden.json`
(336 行变动)。main 用集合比对逐项核过, 全部变化仅两类, 均可归因到上述 `PHASE_OF`/`STATUS_ORDER`
剔除:

1. `board_data.cards[gamma].stage` 与 `[zeta].stage`: `"ready"` → `"plan"` (这两个是 fixture 里
   仅有的就绪态 task)
2. 排序位置变化: `board_data.cards` 顺序由 `alpha,super1,beta,gamma,zeta,delta,ghost1,epsilon`
   变为 `alpha,super1,beta,delta,ghost1,epsilon,gamma,zeta`; `queue.pendingQueue[].ti` 索引跟着变

`dashboard.etaCards` / `dashboard.recentActive` / `queue.queueTasks` 三处经集合比对确认**纯重排,
内容逐项相等**; `archive_list` / `search_*` / `task_detail_*` 六处**逐字未变**。**没有吞掉未察觉的
漂移**, 故放行。

**s3 的收口义务**: s3 做完 (`S_READY` 彻底删除 + 6 个消费文件迁到新状态机) 后, 上述不一致必须消失
—— 届时不该再有任何 task 落到「status 是就绪」这个值上。s3 完成时须复核 golden 里 gamma/zeta 两项
的 `status`/`stage` 是否已收敛到新状态机的合法组合, 而不是继续停在 `status="就绪"`。

## s3 收口完成记 (2026-08-02, redo 续做)

接手时 (worktree `.worktrees/skein-concurrency-pools`) 引擎代码 (model/lifecycle/scheduling/
dag/doctor/query/views/config/cli) 与部分测试已由前一执行者改完并自动提交
(`1bf3e1de9`), 但 36 failed / 330 passed。逐一定位: 均为**测试/文档残留调用已删的
`skein start` 或旧「就绪」态**, 非引擎逻辑错误 —— 判定为续做, 非回退。

### 改动 (按文件)
- `test_stage_hooks.py`: 删 `test_start_before_and_after_fire` (start 阶段钩子已不存在,
  由 confirm 阶段钩子覆盖同语义); 全文件删 8 处冗余 `skein_cli(ws,"start",tid)` (ready=True
  的 `_mk` 已经 confirm 直达进行中); `test_finish/archive_before_and_after_fire` 补
  `check`→`finishing` 两步 (finish 仅收「收尾中」)。docstring "9 个阶段"→"8 个阶段"。
- `test_worktree_disabled.py`: 删 3 处冗余 `skein_cli(ws,"start",tid)`。
- `test_rename.py:91-99`: 断言文案 `"仅限 start 前"` → `"仅限 confirm 前"` (与
  `lifecycle.py:582-584` 实际报错一致), 前置流程去掉冗余 `start`。
- `test_supertask.py:141-155`: `confirm→start→finish` 改 `confirm→check→finishing→finish`;
  手工造 supertask finish 门态从 `"进行中"` 改 `"收尾中"` (finish 硬门要求)。
- `test_ready_scheduling.py`: **整文件删除**。该文件测的是"就绪 task 未 start 直接 claim
  自动启动"这条特性 — `scheduling.py:11,62` 已明确记录该中间态随 confirm 吸收 start 一并
  消失, 无就绪态可自动启动, 特性与测试前提均不复存在。
- `test_views_char.py`: fixture gamma/zeta 的 `status="就绪"` → `"待处理"` (s3 收口义务),
  连带更新顶层索引与模块 docstring; 重生成 `views_golden.json`。
- `test_docs_commands.py` / `test_finish_autocommit.py` / `test_reply_prefix.py`: 排查后
  发现已是绿, 无需改动 (前一执行者已修或本就未受影响, 之前的 36 红列表里带了级联噪音)。

### golden 重生成归因审计
逐字段 diff 旧新 `views_golden.json`, 全部变化可归两类:
1. **gamma/zeta `就绪`→`待处理`** 直接导致: `status`/`stage` 字段本身、`board_data`/
   `dashboard`/`queue` 里 `就绪`/`待处理` 统计数漂移 (2→None / 2→4)、`readyTasks`
   清空 (1→0)、`toPlanTasks` 从 1 增到 3、card/queue/etaCards 因 `STATUS_ORDER` 无
   「就绪」项而重排序 (ghost1/gamma/epsilon/zeta 互换位置, 内容逐项仍可对应, 非内容错乱)、
   `task_detail_alpha.dependents[0].status` 同步跟随。
2. **s1 已落地但此前从未被这份 golden 实测过的 `_TASK_PCT_RANGE` 重分布**
   (`dag.py:26-27`): 新增调研中(5-10)/收尾中(95-98) 两态占位, 进行中区间从 (10,90) 收窄到
   (10,85)、检查中从 (90,98) 收窄到 (85,95) —— alpha(进行中) pct 98→95、beta 类
   (检查中) pct 同比下调, 纯算术推导, 无内容错乱。
无法归因到以上两类的字段变化: 0。放行。

### 7 条验收核对
1. confirm 后直进「进行中」且建 worktree: `lifecycle.py:275-342`,
   `test_worktree_cli.py::test_start_builds_worktree_dir_and_branch` 实测通过; 另手工脚本核过
   (task.json status=进行中, worktree 非空)。
2. 调研中调 confirm 报错提示先 plan: `lifecycle.py:282-283`, 手工脚本实测:
   `feat-manual-check 调研中 — 先 \`skein plan feat-manual-check\`...`。
3. research 未全 done 时 plan 被拒: `lifecycle.py:264-267`, 手工脚本实测:
   `... 调研 subtask 未全完成: s1 — 先 done 它们再 plan`。
4. finish 拒非「收尾中」态: `lifecycle.py:411-413`,
   `test_statemachine.py` 系列 + `test_supertask.py::test_finish_aggregate_guard` 覆盖。
5. `S_READY` 常量与全部消费点已彻底删除: `grep -rn "S_READY" plugins/tools/skein/scripts/` 全仓 0 命中。
6. task 级并发上限已取消: `lifecycle.py` confirm 全文无任何「同时进行中 task 数」校验
   (s2 只换 `max_active`→`pools.work` 取值来源, 校验本身在 s1 之前的 start 里就已随
   start 整体删除, 未见残留)。
7. golden gamma/zeta 收敛: 见上「golden 重生成归因审计」, 两项现落 `status="待处理"`,
   `stage="plan"`, 无 task 落在 `status="就绪"`。

### 质量门
`python3 -m pytest plugins/tools/skein/scripts/tests/ -q` → **360 passed, 0 failed**
(基线 359 passed; 净 +1 = 删 5 条 `test_ready_scheduling.py` 死测 + 前一执行者/本次新增/
调整测试综合结果)。
`python3 -m mypy plugins/tools/skein/scripts/skeinlib/` → **Success: no issues found in 46
source files**。

### subtask list s3 行 (main 亲跑, 主仓根)
跑 `subtask done` 前状态: `s3	运行中	10%	...` (main 仓 .skein 尚未同步 worktree 内进度,
待 `subtask done` 落盘后才反映)。

## s6 交付记录 — 看板 + Web 视图 (`a9ae96628` + `5799c9cc9`)

### 改动 file:line
- `board.py:62-79` `render_task_board(t, work_active, gate_active)` — 双参, 底部两行
  「work 池上限」「gate 池上限」(旧单行「并发上限」删)
- `store.py:244-246` `_write_task_board` 同步双参调用
- `views.py:29-34` `Snapshot.__init__` 加 `gate_active` 字段; `views.py:163-166,257-260`
  `_view_board_data` 计算 `work_running`(全局 running subtask 数)/`gate_running`
  (`cnt[检查中]+cnt[收尾中]`), `overview` 新增 `pools: {work:{limit,running},
  gate:{limit,running}}`; `maxActive` 旧字段原样保留 (前端 ETA 折算并行墙钟仍依赖它)
- `boardsource.py:52-58` `_snapshot()` 传 `pools["work"]`/`pools["gate"]` 两值
- 前端 `status.tsx:4-16` `ST_META`/`ST_ORDER` 加 `research`(调研中)/`finishing`(收尾中),
  `ST_ORDER` 按生命周期时序: planning→research→ready→active→check→finishing→done
- 前端 `model.ts` `STATUS_MAP` 补「调研中」→`research`、「收尾中」→`finishing`
- 前端 `globals.css` 明暗两套加 `--st-research`(ocean-600/800)/`--st-finishing`(reef-600/800)
- 前端 `board/page.tsx`: `ALL_STATUSES`/`DEFAULT_FILTER`/`toggleAll` 同步两新态; 新增
  `pools` state 接线 `overview.pools`, 头部渲染 work/gate 两行占用条 (running/limit, 满槽加粗)

### 3 条验收逐条自证
1. **看板显示 work 与 gate 两行**: CLI 侧 `board.py` 单 task 看板底部两行 (「work 池上限」
   「gate 池上限」); Web 侧 `board/page.tsx` 头部新增 work/gate 两行占用条组件, 手工脚本核
   `_view_board_data` 输出 `overview.pools` 非空验证接线通。
2. **Web 视图 JSON 含两池字段**: `_run(); out['board_data']['overview']['pools']` 实测输出
   `{"work": {"limit": 2, "running": 1}, "gate": {"limit": 3, "running": 1}}`。
3. **新状态在看板有正确排序位**: 前端 `ST_ORDER`/`ALL_STATUSES` 新插 `research`/`finishing`
   于 `ready`/`check` 后对应位置, `ListView` 逐 `ALL_STATUSES` 渲染列 → 两态各得一新列, 位置
   随生命周期时序, 非追加在末尾。

### golden 归因审计
`views_golden.json` 重生成前后逐 key diff: 唯一变化是 `board_data.overview` 新增 `pools`
字段 (`{"work":{"limit":2,"running":1},"gate":{"limit":3,"running":1}}` ← 原为不存在);
`cards`/其余全部视图逐字节相等 (`o['cards']==g['cards']` 实测 `True`)。无法归因字段数: 0。

### dist 重建
`pnpm run build` 成功 (Turbopack, 无 TS 错误), `assets/dist` 产物随源码一并 `git add` 入库
(102 files changed, 含 chunk 文件名因内容 hash 正常轮换)。

### 质量门
`python3 -m pytest plugins/tools/skein/scripts/tests/ -q` → **360 passed, 0 failed**
(与基线一致, 无新增/删除测试)。
`python3 -m mypy plugins/tools/skein/scripts/skeinlib/board.py store.py views.py
boardsource.py` → **Success: no issues found in 4 source files**。

### subtask list s6 行 (worktree 内亲跑)
`s6	已完成	100%	1.5h	看板 + Web 视图	依赖:s1,s2	验收:看板显示 work 与 gate 两行;
Web 视图 JSON 含两池字段; 新状态在看板有正确排序位	skills:-`

## s4 交付记录 — 调度器: 两池计数 + 加权打分 (`0af0c95ee` + `258112f51`)

### 改动 (按文件, `scheduling.py`)
- `_score(s, crit_val)` (模块级新函数): 打分 = 关键路径权重×`_W_CRIT`(100) + 等待小时数×
  `_W_WAIT`(1) + (phase==exec ? `_W_EXEC`(1) : 0)。三常数放模块级不进 config (design §4 原文
  要求)。`_W_CRIT` 远大于其余两项 → 同优先级档内退化为「关键路径优先, 全同分按登记序」,
  与打分引入前零回归。
- `_ready()` (单 task 就绪批, line 41-56): 排序键 `-crit` 换成 `-_score(s, crit)`。
- `_global_ready()` (跨 task 就绪批, line 66-93): cand 元组第 5 项由 `crit` 换成
  `_score(s, crit)`, 排序键 `(-prio, -score, ti, i)` —— **p3 的排序键结构完全不动**, 只是把
  原来单纯的 crit 换成 crit+wait+phase 的加权分, prio 仍是最外层。
- `_claim_check()` (line 179-197): **修一处死代码** —— 原用 `self.ws.store.active()`
  (`STATUS_ACTIVE = {进行中,调研中,收尾中}`, model.py:22, **不含「检查中」**) 遍历, 导致
  「检查中→收尾中」这一路 (`elif t["status"] == S_CHECK`) 永远遍历不到候选, gate 池的
  claim-check 半条腿是死的。改用 `self.ws.store.all_tasks()` + 显式过滤
  `status in (S_ACTIVE, S_CHECK)`。此 bug 非本次引入 (s3 交付时 lifecycle.finishing 本身
  正确, 只是 scheduling.py 没接对候选源), 在写 s4 验收测试时发现并顺手修 (同一文件同一路径,
  拆两个 PR 反而增加解释成本)。
- 满槽提示指明池名 (design §4 验收第 4 条): 新增 `_empty_batch_msg()` 帮助函数, 区分「work
  池已满」/「无待处理 subtask」/「依赖未全部完成」三种成因; `_claim_exec` 两处空批分支
  (dry-run + 正式) 统一调用; 单 task `subtask ready/claim` 空批分支同步改「work 池已满」。
  gate 侧本就有 `lifecycle.py:449` 的 `gate 池已满 ({occupied}/{gate})`, 未改动 (已合规)。

### 4 条验收逐条自证 (`tests/test_dag.py`, 4 个新测试, 均测 `claim` 外部输出, 不碰打分内部数值)
1. **两池独立 (work 满仍可 check)**: `test_two_pools_independent_work_full_check_still_claimable`
   —— `pools.work=1` 占满后, `claim exec --dry-run` 报 work 池已满, 同时另一 task 全 subtask
   done 直接 `claim check` 仍成功收进检查中 (`"已认领进检查" in out`)。
2. **exec 同分优先**: `test_exec_wins_over_research_on_tie` —— 两 task 各 1 subtask, crit/优先级/
   等待时长 (创建时刻紧邻) 全等, phase=exec 的排在 phase=research 前面 (`_dry_run_order` 断言
   index 顺序)。
3. **等久的 research 能翻盘**: `test_long_waiting_research_overtakes_fresh_exec` —— research
   subtask 用新增 helper `_backdate_created()` 把 `created` 拨前 3h (> `_W_EXEC` 等价的 1h),
   同分场景下反超刚登记的 exec subtask, `_dry_run_order` 断言顺序反转。
4. **满槽提示指明池名**: `test_empty_batch_message_names_which_pool_is_full` —— work 满时
   `claim exec --dry-run` 输出含「work 池已满」; gate 压到 0 后二次 `claim check` (第一次先把
   task 转「检查中」, 第二次才撞 gate 门) 输出含「gate 池已满」, 两处均非泛泛「满槽」。

### 两池计数真值来源 & 与 s6 展示口径核对
- **work 池**: `_global_ready()`/`_ready()` 用 `sum(... s["status"]==SS_RUNNING)`
  (`scheduling.py:73-74`, `47`); s6 的 `views.py` `work_running` 算法同样是「全局 running
  subtask 数」(`design.md` s6 交付记录: `_view_board_data` 计算 `work_running`) —— **两处
  独立实现但计数口径一致** (状态=运行中的全局 subtask, 不分 exec/research, 因两态均落在
  work 池)。未做代码共享抽公共函数: 各自只有一行 `sum()`, 抽公共函数增加的间接成本高于
  重复这一行的成本 (ponytail: 两行重复 < 一层新抽象)。
- **gate 池**: `lifecycle.finishing()` (`lifecycle.py:446-447`) 用
  `sum(... x["status"] in (S_CHECK, S_FINISHING))` 全量 `all_tasks()`; s6 的 `views.py`
  `gate_running` 算法为 `cnt[检查中]+cnt[收尾中]` —— 同一口径 (状态∈{检查中,收尾中} 的 task 数)。

### 加权打分与 p3 优先级排序共存
p3 (task-priority) 在 `_global_ready()` 加了最外层排序键「优先级降序」(`cand.sort(key=lambda
x: (-x[5], -x[4], x[2], x[3]))` 中的 `x[5]`)。s4 只把第二排序键 `x[4]` 从纯 `crit` 换成
`_score(s, crit)` —— **优先级仍压过一切** (标了 urgent 就先跑, `test_priority_beats_topo_depth`
仍绿), s4 的加权打分只在**同优先级档内**生效, 不越过优先级, 也不改动 `(ti, i)` 兜底稳定序。
`_W_CRIT=100` 远大于 `_W_WAIT`/`_W_EXEC` 的量级, 保证「关键路径优先」这条 p2 时代就有的性质
在加权打分引入后仍是同优先级档内的主导因子, `test_zero_regression_all_same_priority` 与
`test_claim_order_stable_on_repeat` 两个既有零回归测试全绿, 未见语义漂移。

### golden 归因
未改动 `views.py`/`board.py` 等展示层文件, `views_golden.json` 未重生成, `git status` 干净
(改动仅 `scheduling.py` + `tests/test_dag.py`)。

### 质量门
`python3 -m pytest plugins/tools/skein/scripts/tests/ -q` → **412 passed, 0 failed**
(基线 408 passed；净 +4 = 本次新增 4 个验收测试)。
`python3 -m mypy plugins/tools/skein/scripts/skeinlib/` → **Success: no issues found in 48
source files**。
