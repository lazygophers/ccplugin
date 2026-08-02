# Subtask 状态机

SKEIN subtask 的 4 个状态、流转规则、操作命令及与 `pools.work` 并发槽的关系。
状态落盘值为中文，`skein subtask list <id>` 可查。

---

## 4 个状态

| 状态 (中文) | 英文别名 | 占并发槽 | 含义 |
|---|---|---|---|
| **待处理** | pending | 否 | 已登记 (`subtask add`)，依赖未全 done / 还没被认领，排队等待调度 |
| **运行中** | running | **是** | 已 claim / start，占 `pools.work` 槽，agent 正在执行 |
| **已完成** | done | 否 | 执行成功，验收全过，释放槽位，下游依赖可解锁 |
| **失败** | failed | 否 | 执行失败，释放槽位，等修复后重新 start / 重派 |

---

## 状态流转图

```
               subtask add
                    ↓
              ┌──────────┐
              │  待处理   │  (pending)
              └────┬─────┘
                   │ claim exec / subtask start
                   ↓
              ┌──────────┐
        ┌────→│  运行中   │←───┐
        │     └────┬─────┘    │
        │          │          │
        │     done │          │ fail
        ↓          ↓          ↓
   ┌──────────┐ ┌──────────┐
   │  已完成   │ │   失败   │  (failed)
   └──────────┘ └────┬─────┘
                      │ subtask start (重启)
                      └───────────┘
```

> **失败可重启**: failed 态 subtask 可通过 `subtask start` 重新回到 running，`started` 时间戳不覆盖（保留首次启动时刻）。

---

## 操作命令

> 🔒 **本节是 subtask 状态流转的单一真值源** (源/目标状态、前置校验、副作用) — dag-scheduling / dispatch-graph 只引用不另抄。
> **命令参数表** (必填/选填/默认值) 的单一真值源在 [subtask-operations.md §2.3](subtask-operations.md)。

### 1. `skein subtask add <tid> <sid>` — 新增

- **源状态**: (无)
- **目标状态**: 待处理 (pending)
- **前置校验**: sid 不重复; `--estimate` 为正数 (非数字或 ≤0 直接报错退出); task estimate 须 ≥ Σ subtask estimate
- **字段初始化**: `status=pending`、`created=now()`、`estimate=<--estimate 入参>`、`started=null`、`finished=null`

### 2. `skein claim exec` — 全局跨 task 批量认领

- **源状态**: 待处理 (且依赖全 done)
- **目标状态**: 运行中 (running)
- **范围**: 所有 active task 中 ready 的 subtask 竞争全局槽
- **排序**: 拓扑深度降序 → task 登记序 → subtask 登记序
- **数量**: 取前 `pools.work - 当前全局 running数` 个
- **副作用**: 置 `status=running`，首次认领置 `started=now()`

### 3. `skein subtask claim <tid>` — 单 task 批量认领

- **源状态**: 同 task 内待处理 (且依赖全 done)
- **目标状态**: 运行中 (running)
- **范围**: 仅指定 task 内的 ready subtask
- **其余同全局 claim exec**

### 4. `skein subtask start <tid> <sid>` — 单个启动

- **源状态**: 待处理 / 失败
- **目标状态**: 运行中 (running)
- **前置校验**:
  1. 状态必须是 pending 或 failed
  2. `depends_on` 列表中所有 subtask 必须全 done
  3. **同 task 内** running 数 < `pools.work` (单 task 并发不超上限)
- **副作用**: 置 `status=running`，首次 start 置 `started=now()`

### 5. `skein subtask done <tid> <sid>` — 完成

- **源状态**: 运行中 (running)
- **目标状态**: 已完成 (done)
- **前置校验**: (不卡，脚本不校验 running 态也能 done — 但流程上应只对 running 调用)
- **副作用**: 置 `status=done`、`finished=now()`、`验收done` 全标过 (100%)

### 6. `skein subtask fail <tid> <sid> [--note "..."]` — 失败

- **源状态**: 运行中 (running)
- **目标状态**: 失败 (failed)
- **前置校验**: (不卡)
- **副作用**: 置 `status=failed`、`finished=now()`，可选 `note` 存失败原因

---

## 与 pools.work 并发槽的关系 (task 级并发上限已取消)

### 槽位定义

task 级「同时几个 task 进行中」上限已删。并发约束只剩 `pools.work` (config 参数，默认 2)：

| 层面 | 约束 | 校验位置 |
|---|---|---|
| **单 task 内 subtask** | 单 task 内同时「运行中」的 subtask 数 ≤ `pools.work` | `skein subtask start` 时 |
| **全局 subtask** | 所有进行中 task 加起来的 running subtask 数 ≤ `pools.work` | `skein claim exec` 全局认领时 |

> 注：单 task 内 subtask 与全局 claim exec 共用同一个 `pools.work` 值。

### 占槽 / 释槽时机

| 事件 | 槽位变化 |
|---|---|
| `claim exec` / `subtask start` → running | **占** 1 个 work 池槽 |
| `subtask done` / `subtask fail` | **释** 1 个 work 池槽 |
| `skein confirm` (吸收 start) | 待处理→进行中, **不占任何池** (task 级并发上限已取消) |
| `skein finishing` | 检查中→收尾中, 占 1 个 **gate 池**槽 (与 work 池是两套) |

> **两套池独立**: work 池 (控制同时几个 subtask 在跑) 和 gate 池 (控制同时几个 task 在收尾) 是**两套独立计数**，互不影响。

### 调度规则 (claim exec 算法)

`skein claim exec` 全局调度：
1. 遍历所有「进行中」的 task
2. 对每个 task，找出所有 `status=pending` 且依赖全 done 的 subtask (= ready 池)
3. 按「拓扑深度降序 → task 登记序 → subtask 登记序」排序
4. 取前 `N = pools.work - 当前全局 running 数` 个
5. 批量标 running + 各 task 各自 _save

完成即派：每有一个 subtask done/fail → 立即 `skein claim exec` 补下一个，槽位不空转。

---

## subtask 完成百分比

- 每个 subtask 有 `验收` 字段 (字符串数组，分号分隔)
- `验收done` 记录已通过的序号 (1-based)
- 完成百分比 = `len(验收done) / len(验收) * 100%`
- `subtask done` 时自动把 `验收done` 置为全部 (100%)
- 可用 `skein subtask check <tid> <sid> --passed 1,3` 手动标记部分验收
