# DAG 调度算法

SKEIN 双层同构调度 (subtask 级 + task 级) 的核心算法：依赖模型、就绪判定、分层布局、并发控制、完成即派、plan-ahead 填空闲、子任务自愈。

---

## 1. DAG 依赖模型

### 1.1 依赖字段

SKEIN 的调度完全基于显式依赖边，无隐式依赖推测。

| 层级 | 字段 | 登记位置 | 登记命令 |
|------|------|---------|---------|
| **subtask 级** | `depends_on` (简称 `deps`) | per-task `task.json` 的 `subtasks[].depends_on` | `skein subtask add --deps <sid1>,<sid2>` |
| **task 级** | `deps` | `.skein/tasks.json` 的 `tasks[].deps` | `skein create --deps <tid1>,<tid2>` |

依赖为**有向边**：`A --deps B` 表示 A 依赖 B，即 B 必须先 done，A 才能 ready。

### 1.2 唯一边源原则

- 并行与否**只看显式 DAG**，不靠脚本猜写文件重叠
- 有序关系必须在 planning 阶段写进 `depends_on`，exec 阶段不补
- 无写文件冲突自算 — 发挥 AI 自主性，拆分时靠人/AI 判断真实有序关系

---

## 2. 就绪判定 (Ready = 所有前置 done)

### 2.1 判定公式

```
subtask.ready = (∀ dep ∈ subtask.depends_on: dep.status == done)
              AND (有空闲并发槽)
```

- **前置全 done**：所有被依赖的 subtask 都处于 `已完成` 态
- **有空闲槽**：全局 running subtask 数 < `max_parallel`

### 2.2 deps 阻塞的范围

| 操作 | 是否被 deps 阻塞 | 说明 |
|------|----------------|------|
| `skein create` / `subtask add` | ❌ 不阻塞 | pending task 不论前置是否 plan/finish，一律提前 plan |
| `skein confirm` | ❌ 不阻塞 | planning 正常推进到就绪 |
| `skein start` (task 级) | ✅ 阻塞 | 前置 task 未 done，start 硬拒 |
| `skein claim` (subtask 级) | ✅ 阻塞 | 前置 subtask 未 done，不算 ready |

> **核心原则**：plan/confirm 不阻塞，仅 start/claim 等。前置未完成也照常把规划做完，等 start 时才等前置。

---

## 3. 层级布局算法 (BFS 分层 + 拓扑深度)

### 3.1 拓扑深度计算

每个 subtask 的权重 = 最长下游链长度 + 1 (每步等权，纯拓扑深度)。

```
crit_weight(node) = 1 + max(crit_weight(child) for child in children(node))
                   (叶子节点 crit_weight = 1)
```

脚本内部字段为 `_crit_weight`，由 `claim` 时自动计算，planning 无需手动指定。

### 3.2 就绪批排序

就绪数 > 空闲槽时，`claim` 按以下优先级截取：

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

## 4. 并发上限 (max_active / max_parallel)

### 4.1 配置项

- **配置名**：`max_active`
- **默认值**：`2`
- **查询方式**：`skein config --json | jq -r '.max_active'`

### 4.2 三层并发约束

`max_active` 同时作用于三个层面，是同一个配置值：

| 层面 | 约束 | 校验位置 |
|------|------|---------|
| **task 级** | 同时「进行中」的 task 数 ≤ max_active | `skein start` 时硬拒 |
| **单 task 内 subtask** | 单 task 内同时「运行中」的 subtask 数 ≤ max_active | `skein subtask start` 时硬拒 |
| **全局 subtask** | 所有 active task 加起来的 running subtask 数 ≤ max_active | `skein claim` 全局认领时截断 |

### 4.3 两套独立槽

- **task 级 active 槽**：控制同时几个 task 在跑 (占 worktree)
- **subtask 级 running 槽**：控制同时派几个 agent (占计算资源)

两套计数独立，互不影响。task 级占槽的是「进行中」态，subtask 级占槽的是「运行中」态。

---

## 5. 完成即派 (Done → Claim Next)

### 5.1 调度循环

```
while skein claim 返回非空:       # 全局跨 task 合池竞争
    对认领到的每个 (task, subtask): 派 agent 执行  # ≤ max_parallel
    等任一 subagent 返回
    → skein subtask done/fail <tid> <sid> → 回到 skein claim
```

### 5.2 核心规则

- **不等一批跑完**：任一 subtask 返回 → 立即 `done`/`fail` → 立即 `claim` 补下一个
- **槽位不空转**：释放一个槽位，立刻填一个新的 ready subtask
- **脚本一步到位**：就绪判定 + 占槽由 `claim` 原子完成，main 不逐个 `subtask start`

### 5.3 claim 命令族

| 命令 | 范围 | 用途 |
|------|------|------|
| `skein claim` | 全局跨 task | **主路径**：所有 active task 的 ready subtask 合池竞争 |
| `skein subtask claim <tid>` | 单 task 内 | 兼容模式：仅指定 task 内截断，不跨 task 竞争 |
| `skein claim --dry-run` | 全局只读 | 预览就绪批，不改态不占槽 |
| `skein subtask start <tid> <sid>` | 单个 subtask | 失败重派 / 定点补派 |

> **claim 默认改态占槽**：调用即把就绪批整批标 running + 占槽，无需额外参数。`--dry-run` 才只读。

---

## 6. Plan-ahead 填空闲策略

### 6.1 优先级顺序

**subtask 调度优先，plan-ahead 是次级填充器**：

1. **有可调度 subtask** → 一律先 `claim` 派 subtask (尽早完成在飞 task)
2. **claim 返回空** (满槽等回传 / 无就绪 subtask) → 才做 plan-ahead

### 6.2 Plan-ahead 做什么

```
skein list --status open --json
  → 找 status=待处理 且 subs 全 0 (无 subtask = plan 未完成) 的 task
  → 加载 skein-plan --continue 推到 planning-ready
```

- **目标**：用 exec 空闲窗口把排队 task 备到「一有 slot 即可 start」，流水线不断档
- **推到哪里停**：至多推到 `skein confirm`/`start` 门前 (planning-complete 待处理态)
- **不自动过用户门**：confirm 是用户确认门，plan-ahead 不自动 confirm

### 6.3 必让位 subtask

- 每步 planning 前/后回探 `claim`
- 一旦有 subtask 可派 (subagent 回传腾槽 / 新 ready) → 立即放下 planning 回去派 subtask
- plan-ahead 可被随时打断，subtask 调度优先级永远更高

### 6.4 死锁判定

- 无未 plan 的 pending task，且 `claim` 持续返回空 → 检查 depends_on 是否有环
- 有环 → 停手回 skein-plan 改 DAG，禁空转轮询

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
  --deps <失败sid的前置>   # 挂到失败 subtask 的前置位置
```

流程：
1. 插修复 subtask (挂失败 sid 的前置，即修复 done 后失败 subtask 才 ready)
2. 派 executor 定点修根因
3. fix done 后 `skein subtask start <tid> <失败sid>` 重派原 subtask

### 7.3 自愈前置要求 (tight feedback loop)

自愈重派前 dispatch prompt **MUST 含「先复现」指令**：

- subagent 回传必须含**一条就红的复现命令** (one command that goes red on this bug)
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

所有 active task 的 ready subtask 竞争**同一 `max_parallel` 槽**，不是 per-task 各占 max_parallel。

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
