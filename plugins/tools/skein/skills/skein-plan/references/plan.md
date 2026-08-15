# plan — planning 工件写法

plan 的状态推进、research 分流、confirm、人审门、plan-ahead、出口规则见 [skein-flow/references/flow-loop.md](../../skein-flow/references/flow-loop.md#plan)。本文件只写三件工件各自怎么落。

## prd.md (TaskSpec)

TaskSpec 四要素存 prd.md 的 YAML frontmatter（单一真值，task.json 不存）：`desc` / `boundary.should` / `boundary.should_not` / `acceptance` / `estimate`。正文散文区人读，不参与校验。

- 读写一律走 CLI，禁直接编辑：`Bash("skein task spec <tid> --desc <str> --should <a;b> --not <a;b> --acceptance <a;b>")`，只读回显 `Bash("skein task spec <tid>")`。
- `Bash("skein task confirm <tid> --approved")` 硬校验：desc 非空、boundary 有内容、acceptance 非空、estimate > 0，缺一即拒。
- confirm 后 spec 锁定（仅 `pending` / `research` 可改）。

## design.md

只写当前方案：架构、数据流、取舍、技术选型、测试接缝、可能性分支。

- 当前方案保持精简，禁把未来扩展点塞进正文。
- 可能性分支必须标触发条件，且不生成 subtask。
- 难逆决策写进取舍或可能性分支。
- `## 测试接缝 (seam)` 必须填实（confirm 校验）：`Bash("skein design seam <tid> --list '接缝一\\n接缝二'")`，读回显 `Bash("skein design read <tid>")`。

## subtask DAG 与 estimate

拆分原则、登记模板、挂边约束见 [dag.md](dag.md#1-依赖模型)。每个 subtask 必有 sid/name/desc/estimate/check：`Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时> --check '<验收a;验收b>'")`。

### 预计工时硬门 (estimate)

task 与 subtask 各有 `estimate` 字段（小时，浮点，未填为 `null`）。`Bash("skein task confirm <tid> --approved")` 硬校验，缺失或非正数一律拒绝开工。填值：`Bash("skein task estimate <tid> --set <小时>")`。

#### 铁律

- **plan 阶段必填**：task 工时须在 `Bash("skein task confirm <tid> --approved")` 前填实，与 TaskSpec 齐备、subtask 拆分同为 confirm 硬门。
- **subtask 逐个必填**：`Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时数>")` 必带 `--estimate`，缺失或非正数直接拒。
- **自下而上累加**：task 工时 ≥ Σ subtask 工时。差额 = task 自身开销（plan 规划 / grill 审查 / check 验收 / finish 收尾），不是缓冲余量。
- **🔒 纯 AI 估，禁问用户**：工期估算归 main 自主完成 —— 用户不知实际工作量，问工期既问不出准数又拖规划。**禁用 `AskUserQuestion` 或任何形式问「这要多久 / 预估几小时」**。估不准可接受，把球踢给用户不可接受。
- **改动窗口**：仅 `pending` / `research` 可 `Bash("skein task estimate <tid> --set <小时>")`；confirm 后锁定（工时是规划期决策，执行期不回改）。

#### 怎么估准

**唯一合法姿势：先拆再估，逐项累加。** 禁整体拍脑袋。

1. 先把 task 拆成 subtask（confirm 硬门已强制 ≥1 个）。
2. 每个 subtask 按它**实际要做的事**独立估 —— 要改哪几个文件、要不要写测试、要不要先调研。
3. task 工时 = Σ subtask + 自身 plan/check/finish 开销。

禁：未拆 subtask 先填 task estimate；填占位整数（`1`/`2`/`8` 之类图省事的默认值）；「大概几小时」式整体估。

**自查**：报数前须能逐条说出每个 subtask 估了多少、依据是什么。说不出 = 没估，是猜。

#### 在 confirm 硬门中的位置

`Bash("skein task confirm <tid> --approved")` 依次校验：① subtask ≥1 → ② TaskSpec 齐备（desc 非空 / boundary 有内容 / acceptance 非空）+ design 接缝填实 → ③ 工时已填实且 ≥ Σ subtask。任一不满足即报错阻断。

subtask 工时在 `Bash("skein subtask add <tid> <sid> ... --estimate <小时>")` 时已必填，走到 confirm 时 Σ 一定齐 —— ③ 只查 task 自身有没有漏算 plan/check 开销。

## 收敛不了时

只产出可行动问题：缺什么信息、影响哪个工件、推荐选项是什么。是否停顿以 [skein-flow/references/flow-loop.md](../../skein-flow/references/flow-loop.md#终止条件) 为准。
