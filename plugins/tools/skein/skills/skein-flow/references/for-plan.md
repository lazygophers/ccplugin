# for-plan — plan 阶段产物边界

plan 的状态推进、research 分流、confirm、人审门、plan-ahead、出口规则统一见 [flow-loop.md §4](flow-loop.md#4-plan-过程)。本文件只保留 planning 产物职责和局部写法。

## main 保留职责

- 拆用户诉求，判定新建 task 或并入现有 task。
- 必要时派 `skein-researcher` 只读调研；调研结论落 `.skein/task/<id>/research/` 与 `findings.md`。
- 用 `AskUserQuestion` 处理 brainstorm、关键取舍、grill、人审门。
- 写/维护 planning 工件：`prd.md`、`design.md`、task contracts、subtask DAG、estimate。
- planning 完成后按 [flow-loop.md](flow-loop.md) 决定停在 confirm 前或继续 exec。

## planning 工件

### PRD

标准六段：

- `目标`
- `边界`
- `User Stories`
- `验收标准`
- `Testing Decisions`
- `索引`

规则：

- 占位 `- [ ] TODO: 填X` 必须整行替换为真实内容。
- planning 期 `目标` / `验收标准` 条目保持 `- [ ]`，勾选归 check。
- `目标` / `边界` / `验收标准` 优先用 `skein prd write` / `skein prd add` / `skein prd check`；无脚本覆盖段落可直接编辑。

### design

`design.md` 只写当前方案：架构、数据流、取舍、技术选型、测试接缝、可能性分支。

规则：

- 当前方案保持精简，禁把未来扩展点塞进正文。
- 可能性分支必须标触发条件，不生成 subtask。
- 难逆决策写入取舍或可能性分支。
- `## 测试接缝 (seam)` 必须填实。

### contracts

brainstorm / grill 得到的不变量用命令逐条落盘：

```bash
skein contract <id> --add "契约文本"
skein contract <id>
```

### subtask DAG

- 共享契约先行：接口、类型、协议、schema 等共享面优先抽成前置 subtask。
- 下游实现只依赖共享契约 subtask，彼此不互挂，除非确有真实顺序依赖。
- 每个 subtask 必有 sid/name/desc/estimate/check。
- 登记模板见 [dispatch-graph.md](dispatch-graph.md)，参数表见 [subtask-operations.md](subtask-operations.md)。

### estimate

预计工时必须填实，规则见 [estimate-gate.md](estimate-gate.md)。

## 局部失败信息

planning 阶段若无法收敛，只产出可行动问题：缺什么信息、影响哪个工件、推荐选项是什么。流程是否停顿、如何继续，以 [flow-loop.md §10](flow-loop.md#10-停顿白名单) 为准。
