# DAG 调度算法

SKEIN 双层同构调度 (subtask 级 + task 级) 的核心算法：依赖模型、就绪判定、分层布局、并发控制、完成即派、plan-ahead 填空闲、子任务自愈。

---

## 1. DAG 依赖模型

### 1.1 依赖字段

SKEIN 的调度完全基于显式依赖边，无隐式依赖推测。

| 层级 | 字段 | 登记位置 | 登记命令 |
|---|---|---|---|
| **subtask 级** | `depends_on` (简称 `deps`) | per-task `task.json` 的 `subtasks[].depends_on` | `skein subtask add --deps <sid1>,<sid2>` |
| **task 级** | `deps` | `.skein/tasks.json` 的 `tasks[].deps` | `skein create --deps <tid1>,<tid2>` |

依赖为**有向边**：`A --deps B` 表示 A 依赖 B，即 B 必须先 done，A 才能 ready。

### 1.2 唯一边源原则

- 并行与否**只看显式 DAG**，不靠脚本猜写文件重叠
- 有序关系必须在 planning 阶段写进 `depends_on`，exec 阶段不补
- 无写文件冲突自算 — 发挥 AI 自主性，拆分时靠人/AI 判断真实有序关系

### 1.3 subtask 命令族 (脚本落盘，非肉眼看 md 文件)

subtask DAG 存 per-task `task.json` 的 `subtasks[]` (guard 硬阻 AI 直读写)，全程经 `skein subtask` 命令维护。**参数与状态流转以 [subtask-state-machine.md §操作命令](subtask-state-machine.md) 为单一真值源**，本表只列「谁跑 + 调度语义」：

| 命令 | 谁跑 | 作用 |
|---|---|---|
| `subtask add` | planning/main | 登记 subtask 到 DAG (参数表见 [subtask-operations.md §2.3](subtask-operations.md)) |
| `claim exec` | main (每轮，主路径) | 见 §5.3 |
| `subtask claim <tid>` | main (单 task 兼容) | 见 §5.3 |
| `claim --dry-run` | main (查候选) | 见 §5.3 |
| `subtask check <tid> <sid> --passed "1,3"` | main (**check 阶段**，非 exec) | 勾选已过验收序号 (1-based；`all`/`none`)，更新完成百分比。exec 不勾验收 — 归 check 阶段 checkpoint 核对 |
| `subtask done/fail <tid> <sid>` | main (exec，agent 回) | agent 执行完成/失败即改态。exec 唯一改态出口 (`done`=执行动作完成；验收核对留给 check) |
| `subtask ready <tid>` / `list <tid>` | main (查态) | 只读预览 / 列全 subtask 态 |
| `list --status open --json` | main (取未完成) | 一次取全部未完成 task 压缩 JSON: `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}` |

---

## 2. 就绪判定 (Ready = 所有前置 done)

### 2.1 判定公式

```
subtask.ready = (∀ dep ∈ subtask.depends_on: dep.status == done)
              AND (有空闲并发槽)
```

- **前置全 done**：所有被依赖的 subtask 都处于 `已完成` 态
- **有空闲槽**：全局 running subtask 数 < `max_active`

### 2.2 deps 阻塞的范围

| 操作 | 是否被 deps 阻塞 | 说明 |
|---|---|---|
| `skein create` / `subtask add` | ❌ 不阻塞 | pending task 不论前置是否 plan/finish，一律提前 plan |
| `skein confirm` | ❌ 不阻塞 | planning 正常推进到就绪 |
| `skein start` (task 级) | ✅ 阻塞 | 前置 task 未 done，start 硬拒 |
| `skein claim exec` (subtask 级) | ✅ 阻塞 | 前置 subtask 未 done，不算 ready |

> **核心原则**：plan/confirm 不阻塞，仅 start/claim 等。前置未完成也照常把规划做完，等 start 时才等前置。

---

## 3. 层级布局算法 (BFS 分层 + 拓扑深度)

### 3.1 拓扑深度计算

每个 subtask 的权重 = 最长下游链长度 + 1 (每步等权，纯拓扑深度)。

```
crit_weight(node) = 1 + max(crit_weight(child) for child in children(node))
                   (叶子节点 crit_weight = 1)
```

脚本内部字段为 `_crit_weight`，由 `claim exec` 时自动计算，planning 无需手动指定。

### 3.2 就绪批排序

就绪数 > 空闲槽时，`claim exec` 按以下优先级截取：

1. **拓扑深度降序** — 深度大者阻塞下游最多，先派
2. **task 登记序** — 同深度时，先创建的 task 优先
3. **subtask 登记序** — 同 task 同深度时，先 add 的 subtask 优先

> 稳定排序，不打乱同优先级的相对顺序。

### 3.3 BFS 分层（可视化用）

用于看板渲染 / 调试输出的分层布局：

```
layer 0: 无任何前置依赖的 subtask (源头节点)
layer 1: 所有前置都在 layer 0 的 subtask
layer 2: 所有前置都在 layer 0..1 且至少一个在 layer 1 的 subtask
...
layer N: 最下游节点
```

算法：对每个 subtask，`layer = max(layer(dep)) + 1` (源头 layer = 0)。

---

## 4. 并发上限 (max_active)

### 4.1 配置项

- **配置名**：`max_active`
- **默认值**：`2`
- **查询方式**：`skein config --json | jq -r '.max_active'`

### 4.2 三层并发约束

`max_active` 同时作用于三个层面，是同一个配置值：

| 层面 | 约束 | 校验位置 |
|---|---|---|
| **task 级** | 同时「进行中」的 task 数 ≤ max_active | `skein start` 时硬拒 |
| **单 task 内 subtask** | 单 task 内同时「运行中」的 subtask 数 ≤ max_active | `skein subtask start` 时硬拒 |
| **全局 subtask** | 所有可调度 task (进行中 + 就绪) 加起来的 running subtask 数 ≤ max_active | `skein claim exec` 全局认领时截断 |

### 4.3 两套独立槽

- **task 级 active 槽**：控制同时几个 task 在跑 (占 worktree)
- **subtask 级 running 槽**：控制同时派几个 agent (占计算资源)

两套计数独立，互不影响。task 级占槽的是「进行中」态，subtask 级占槽的是「运行中」态。

---

## 5. 完成即派 (Done → Claim Next)

### 5.1 调度循环

```
while skein claim exec 返回非空:       # 全局跨 task 合池竞争
    对认领到的每个 (task, subtask): 派 agent 执行  # ≤ max_active
    等任一 subagent 返回
    → skein subtask done/fail <tid> <sid> → 回到 skein claim exec
```

### 5.2 核心规则

- **不等一批跑完**：任一 subtask 返回 → 立即 `done`/`fail` → 立即 `claim exec` 补下一个
- **槽位不空转**：释放一个槽位，立刻填一个新的 ready subtask
- **脚本一步到位**：就绪判定 + 占槽由 `claim exec` 原子完成，main 不逐个 `subtask start`

### 5.3 claim 命令族

| 命令 | 范围 | 用途 |
|---|---|---|
| `skein claim exec` | 全局跨 task | **主路径**：所有可调度 task (进行中 + 就绪, 前置已清) 的 ready subtask 合池竞争; 就绪 task 首个 subtask 被认领时自动启动 |
| `skein subtask claim <tid>` | 单 task 内 | 兼容模式：仅指定 task 内截断，不跨 task 竞争 |
| `skein claim exec --dry-run` | 全局只读 | 预览就绪批，不改态不占槽 |
| `skein subtask start <tid> <sid>` | 单个 subtask | 失败重派 / 定点补派 |

> **claim exec 默认改态占槽**：调用即把就绪批整批标 running + 占槽，无需额外参数。`--dry-run` 才只读。
> 各命令的源/目标状态、前置校验、副作用见 [subtask-state-machine.md §操作命令](subtask-state-machine.md)。

---

## 6. Plan-ahead 填空闲策略

### 6.1 优先级总纲: 派异步优先, 同步 plan 填余力

**铁律: 优先把槽位占满异步执行, 同步 plan 只在槽位已满 / 无可调度 subtask 时跑。** subagent 跑起来后是异步占槽, 同步 plan 不抢这个槽 —— 所以每回合先 `claim exec` 把能派的 subtask 派出去 (占满 `max_active` 槽), 槽位满或 `claim exec` 返回空时才做 plan-ahead, 用同步空档把 pending task 推到就绪, 保证一有槽位释放即有 ready task 接上, 流水线不断档。

```
每回合:
  1. skein claim exec  → 有就绪 subtask 就派, 占满 max_active 槽 (异步, 立即回手)
  2. 槽位满 OR claim exec 返回空 → 加载 plan-ahead 推 pending task 到就绪
  3. plan 每步间回探 claim exec → 有 subtask 可派立即中断 plan 回去派
```

- **派 subtask 是异步动作** (派出即占槽, 不阻塞 main), plan 是同步动作 —— 同回合内先做异步占槽, 再做同步 plan, 两不耽误。
- **只要还有 pending task 未就绪, plan-ahead 就不停** (前提是槽位已满 / 无可派 subtask), 不能 idle 干等 subagent 回传。

### 6.2 Plan-ahead 做什么

```
skein list --status open --json
  → 找 status=待处理 且 subs 全 0 (无 subtask = plan 未完成) 的 task
  → 加载 /skein-flow plan 阶段 推到 planning-ready
```

- **目标**：用 exec 空闲窗口把排队 task 备到「一有 slot 即可 start」，流水线不断档
- **推到哪里停**：至多推到 `skein confirm`/`start` 门前 (planning-complete 待处理态)
- **不自动过用户门**：confirm 是用户确认门，plan-ahead 不自动 confirm。**注**: 这条只约束 plan-ahead 预备的**非焦点 pending task** (exec 空闲时顺手推进的排队 task)。循环当前焦点 task 的 confirm 行为以 [flow-loop.md](flow-loop.md) 为准 (flow 主循环视 confirm 为非阻塞门, 判据勾满自动过); 该 pending task 一旦被 claim/exec 选为焦点, 即按 flow-loop.md 自动过 confirm, 不再受本条限制。

### 6.3 必让位 subtask

- 每步 planning 前/后回探 `claim exec`
- 一旦有 subtask 可派 (subagent 回传腾槽 / 新 ready) → 立即放下 planning 回去派 subtask
- plan-ahead 可被随时打断，subtask 调度优先级永远更高

### 6.4 死锁判定

- 无未 plan 的 pending task，且 `claim exec` 持续返回空 → 检查 depends_on 是否有环
- 有环 → 停手回 skein-flow plan 阶段 改 DAG，禁空转轮询

---

## 7. 子任务自愈逻辑 (失败 → 根因判断 → 插修复 subtask)

### 7.1 触发条件

subtask 失败 / 报错 / 验收不过 → `subtask fail <tid> <sid> --note <原因>` → 进入自愈判断。

**禁失败即停摆**：必须先尝试自愈，兜底才回传人工。

### 7.2 自愈二选一（均在本 task scope 内）

#### ① 定点小缺陷 → 原地重派

**适用场景**：实现 bug / 局部漏改 / 小范围调整。

```
skein subtask start <tid> <失败sid>   # 重启 failed 态 subtask
```

- bounded ≤ **2 轮**
- 缩范围重派，不新增 subtask

#### ② 根因是独立可修单元 → 插修复 subtask

**适用场景**：缺前置产物 / 共享依赖坏 / 需单独定点修。

```
skein subtask add <tid> <fix-sid> \
  --name "修复<根因>" \
  --desc "定点修<失败sid>根因" \
  --estimate <小时数> \
  --deps <失败sid的前置>   # 挂到失败 subtask 的前置位置
```

流程：
1. 插修复 subtask (挂失败 sid 的前置，即修复 done 后失败 subtask 才 ready)
2. 派 executor 定点修根因
3. fix done 后 `skein subtask start <tid> <失败sid>` 重派原 subtask

### 7.3 自愈前置要求 (tight feedback loop)

自愈重派前, 修复 subtask 的 `--desc`/`--check` **MUST 含「先复现」指令** (exec dispatch 已简化为 tid+sid+workdir 三参数, 不再自包含 prompt, 该要求改落在 `subtask add` 的 desc/check 文本里, executor 自读 `subtask show` 时自会看到)：

- executor 回传必须含**一条就红的复现命令** (one command that goes red on this bug)
- 修复后该命令转绿
- 无复现 = 修了也无法验证，是猜

### 7.4 兜底出口

以下情况停止自愈，回传 main 走根因协议或转人工：

- 修复 subtask 也失败
- 同一 subtask 累计 > 2 轮无进展
- 根因超本 task scope (需求·设计缺陷)

> **禁跳过该 subtask 放行下游**。失败 subtask 不 done，下游永远不 ready。

---

## 8. 全局单池模型

### 8.1 跨 task 合池

所有可调度 task (进行中 + 就绪) 的 ready subtask 竞争**同一 `max_active` 槽**，不是 per-task 各占 max_active。task 级 max_active 同时限制能有多少个 task 处于进行中 —— 满槽时就绪 task 不会被自动启动。

```
总并发 = task1.running + task2.running + ... ≤ max_active
```

### 8.2 排序

全局 claim 时排序键：
1. 拓扑深度降序
2. task 登记序 (先创建的 task 优先)
3. subtask 登记序 (先 add 的 subtask 优先)

### 8.3 隔离

- 各 active task 各占各 worktree，改动天然隔离
- 派出的 subagent 改各自 task worktree，互不干扰

---

## 9. dispatch 参数 (exec 统一 3 参数, 不再自包含 prompt)

**执行者一律 `skein-executor`** — exec 不再按 subtask 挑 agent。dispatch 只给 **tid + sid + 工作目录** 三参数, executor 自读 `skein subtask show <tid> <sid>` 拿全字段 (验收/deps/skills)、自跑 `subtask done/fail` 收尾。递归护栏 (Recursion Guard) 靠 `skein-executor` 工具面本身剔除 Agent/Task 强制, 不再靠 dispatch prompt 文字禁止。6 字段自包含 prompt 规则 (见 [carrier-rules.md](carrier-rules.md)) 对 exec 派发**例外**, 其余阶段 (check/finish) 不受影响, 详见对应 agent md。

- **验收标准来自 planning 的 `--check`** — 每个 subtask 登记时带一份可验断言 checklist (存 per-task task.json 的 `验收[]`)，executor 自读后逐条自检、回传时对照。这份 checklist 的正式核对归 skein-flow check 阶段 checkpoint 核对，exec 只是 agent 自检用。
- **exec 只 done/fail，验收勾选归 check** — executor 自跑 `subtask done/fail`，不跑 `subtask check` 勾验收。看板 (task.md/task.html) 逐 subtask 渲染进度条，task 综合完成率 = 各 subtask 百分比均值。
- **Recursion Guard 靠 dispatch prompt 硬性禁止** — 通用 agent 有 Agent/Task 工具，故不靠工具面而靠上面 prompt 的硬性指令挡住递归：执行 agent 只做这一个 subtask，禁再派 subagent，自己动手做完；也不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。
