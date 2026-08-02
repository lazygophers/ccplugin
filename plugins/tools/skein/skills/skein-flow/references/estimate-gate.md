# 预计工时硬门 (estimate)

task 与 subtask 各有 `estimate` 字段（小时，浮点，未填为 `null`）。`skein confirm` 硬校验，缺失或非正数一律拒绝开工。命令用法查 `skein estimate --help`。

## 铁律

- **plan 阶段必填**：task 工时须在 `skein confirm` 前填实，与 prd 章节齐备、subtask 拆分同为 confirm 硬门。
- **subtask 逐个必填**：`skein subtask add` 必带 `--estimate <小时数>`，缺失或非正数直接拒。
- **自下而上累加**：task 工时 ≥ Σ subtask 工时。差额 = task 自身开销（plan 规划 / grill 审查 / check 验收 / finish 收尾），不是缓冲余量。
- **🔒 纯 AI 估，禁问用户**：工期估算归 main 自主完成 —— 用户不知实际工作量，问工期既问不出准数又拖规划。**禁用 `AskUserQuestion` 或任何形式问「这要多久 / 预估几小时」**。估不准可接受，把球踢给用户不可接受。
- **改动窗口**：仅 `pending` / `research` 可 `skein estimate --set`；confirm 后锁定（工时是规划期决策，执行期不回改）。

## 怎么估准

**唯一合法姿势：先拆再估，逐项累加。** 禁整体拍脑袋。

1. 先把 task 拆成 subtask（confirm 硬门已强制 ≥1 个）。
2. 每个 subtask 按它**实际要做的事**独立估 —— 要改哪几个文件、要不要写测试、要不要先调研。
3. task 工时 = Σ subtask + 自身 plan/check/finish 开销。

禁：未拆 subtask 先填 task estimate；填占位整数（`1`/`2`/`8` 之类图省事的默认值）；「大概几小时」式整体估。

**自查**：报数前须能逐条说出每个 subtask 估了多少、依据是什么。说不出 = 没估，是猜。

## 在 confirm 硬门中的位置

`skein confirm` 依次校验：① subtask ≥1 → ② prd 七段齐备无 TODO 占位 → ③ 工时已填实且 ≥ Σ subtask。任一不满足即报错阻断。

subtask 工时在 `subtask add` 时已必填，走到 confirm 时 Σ 一定齐 —— ③ 只查 task 自身有没有漏算 plan/check 开销。
