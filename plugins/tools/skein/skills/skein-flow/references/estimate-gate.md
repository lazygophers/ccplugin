# 预计工时硬门 (estimate)

SKEIN task 的预计工时 (小时, 浮点数) 是 plan 阶段必填项, `skein confirm` (待处理→就绪) 硬校验, 缺失或非正数一律拒绝进就绪。

---

## 铁律

- **plan 阶段必填**: task 的预计工时须在 `skein confirm` 前填实, 与 prd 四章节、subtask 拆分同为 confirm 硬门条件 (见 `plan 阶段完成判据`)。
- **subtask 逐个必填**: 每个 subtask 有独立 `estimate` 字段, `skein subtask add` 时必带 `--estimate <小时数>`, 缺失或非正数直接拒。
- **自下而上累加**: task 工时 ≥ Σ subtask 工时。差额 = task 自身开销 (plan 规划 / grill 审查 / check 验收 / finish 收尾), 不是缓冲余量。
- **存储**: task 与 subtask 各自 `estimate` 字段 (数字, 单位小时; 未填为 `null`)。
- **不通过**: `skein confirm` 检出未填或低于 subtask 合计即报错退出, 阻断进就绪。

---

## 怎么估准

**唯一合法姿势: 先拆再估, 逐项累加。** 禁整体拍脑袋。

1. 先把 task 拆成 subtask (confirm 硬门已强制 ≥1 个)。
2. 每个 subtask 按它**实际要做的事**独立估 — 要改哪几个文件、要不要写测试、要不要先调研。
3. task 工时 = Σ subtask + 自身 plan/check/finish 开销。

**禁**:
- 未拆 subtask 先填 task estimate。
- 填占位整数 (`1` / `2` / `8` 之类图省事的默认值)。
- 「大概几小时」式整体估, 说不清哪部分占多久。

**自查**: 报数前须能逐条说出每个 subtask 估了多少、依据是什么。说不出 = 没估, 是猜。

---

## 填写方式

| 方式 | 命令 | 阶段 |
|---|---|---|
| subtask 登记时必填 | `skein subtask add <id> <sid> --name .. --desc .. --estimate 2` | plan (必填, 缺则拒) |
| task 创建时指定 | `skein create <id> --name .. --desc .. --estimate 4` | create |
| task 规划时补填/修改 | `skein estimate <id> --set 6` | pending / ready (start 后不可再改) |
| 查看当前值 + 分解 | `skein estimate <id>` (省略 `--set`, 附出 subtask 合计与自身开销) | 任意阶段, 纯读 |
| 默认值 | 无默认, 缺省即未填 (`null`), confirm 会拒绝 | - |

---

## 与 prd/subtask 硬门的关系

`skein confirm` 一次校验三项 (顺序): ① subtask ≥1 (`subtask add` 已落 DAG) → ② prd 四章节齐备无 TODO 占位 → ③ 预计工时已填实且 ≥ Σ subtask。任一不满足即报错阻断, 不进就绪。

subtask 工时在 `subtask add` 时就已必填, 所以走到 confirm 时 Σ 一定齐 — ③ 只查 task 自身有没有漏算 plan/check 开销。

`skein start` (就绪→进行中) 不重复校验预计工时 — 工时估算只影响 plan/confirm 阶段的规划质量把关, 不像 prd 那样需要 double-check 防中途改空 (预计工时填后极少被回改)。

---

## 编辑限制

- 仅 `pending`(待处理) / `ready`(就绪) 状态可 `skein estimate --set` 改动; `start` 后 (进行中及以后) 状态锁定, 拒绝修改 (工时估算是规划期决策, 执行期不应回改)。
- 与 `repos`/`deps` 命令同构: 省略 `--set` 即查看当前值, 纯读不加写锁。
