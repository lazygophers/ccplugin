# for-plan — planning 工件写法

plan 的状态推进、research 分流、confirm、人审门、plan-ahead、出口规则见 [flow-loop.md §4](flow-loop.md#4-plan-过程)。本文件只写四件工件各自怎么落。

## prd.md

标准七段（顺序固定，`skein confirm` 硬校验）：`目标` / `边界` / `User Stories` / `验收标准` / `验证方式` / `Testing Decisions` / `索引`。

- 占位 `- [ ] TODO: 填X` 必须整行替换为真实内容，留一条即被 confirm 拒。
- planning 期 `目标` / `验收标准` 条目保持 `- [ ]`，勾选归 check。
- `目标` / `边界` / `验收标准` 优先用 `skein prd write` / `prd add` / `prd check`；无脚本覆盖的段落可直接编辑。

## design.md

只写当前方案：架构、数据流、取舍、技术选型、测试接缝、可能性分支。

- 当前方案保持精简，禁把未来扩展点塞进正文。
- 可能性分支必须标触发条件，且不生成 subtask。
- 难逆决策写进取舍或可能性分支。
- `## 测试接缝 (seam)` 必须填实（confirm 校验）。

## contracts

brainstorm / grill 得到的不变量逐条落盘：

```bash
skein contract <id> --add "契约文本"
skein contract <id>
```

## subtask DAG 与 estimate

拆分原则、登记模板、挂边约束见 [dag-scheduling.md §2](dag-scheduling.md#2-拆分与落盘)；工时规则见 [estimate-gate.md](estimate-gate.md)。每个 subtask 必有 sid/name/desc/estimate/check。

## 收敛不了时

只产出可行动问题：缺什么信息、影响哪个工件、推荐选项是什么。是否停顿以 [flow-loop.md §10](flow-loop.md#10-停顿白名单) 为准。
