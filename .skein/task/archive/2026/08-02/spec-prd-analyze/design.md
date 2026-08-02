# prd 六段 + seam 门 + analyze 一致性核查 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. prd 段落映射 (对齐 `/to-spec`)

| to-spec 段 | skein 现状 | 本轮 |
|---|---|---|
| Problem Statement | ≈ 目标 | 保持 (目标已含 problem + solution) |
| Solution | ≈ 目标 | 保持 |
| **User Stories** (极长编号列表) | **缺** | **新增** ← 最该补的 |
| Implementation Decisions | ≈ design.md | 保持在 design |
| **Testing Decisions** | **缺** | **新增** |
| Out of Scope | ≈ 边界 | 保持 |
| Further Notes | — | 不加 (索引段已够) |

**最终六段**: 目标 / 边界 / User Stories / 验收标准 / Testing Decisions / 索引

**为什么 User Stories 值得加**: to-spec 要求它「extremely extensive」不是冗余 —— **穷举 user story 是逼出边界情况的机械手段**。现在 skein 的验收标准是推导的**结果**, 缺了推导过程, 边界靠 AI「想想」, 想漏了没人知道。有了极长的 story 列表, 漏了哪个 actor / 哪条路径是**肉眼可见**的。

**禁写路径**: 模板内明确提示「禁具体文件路径与代码片段 (会很快过期)」, 例外同 to-spec —— prototype 产出的能精确编码决策的东西 (状态机 / schema / type shape) 可内联, 且注明来自 prototype。

## 2. seam 门

`/to-spec` 全流程只有一处停下来问用户: **测试接缝**。三条规则:

1. 优先复用现有接缝, 不新建
2. 取**最高**接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

进 `design.md` 脚手架 + `confirm` 硬门。

**为什么这一条比补 prd 段更重要**: `skein-checker` 的验证质量完全取决于有没有接缝 —— 没接缝就只能验「跑没跑起来」, 有接缝才能验「行为对不对」。skein 现在的 `confirm` 门确认需求但不确认接缝, 等于把 check 阶段的质量交给运气。

## 3. `analyze` 五类检查 (只读)

对齐 spec-kit 的 `/speckit.analyze` —— 「需求错配的最后一道防线」, 明确 read-only 不改任何东西。

| 检查 | 消费的源 | 实现 | 假阳性处置 |
|---|---|---|---|
| **验收覆盖率** | prd 验收标准 ↔ subtask `--check` | 机械: 逐条验收标准找有无 subtask check 项语义对应 | 关键词匹配, 报候选未覆盖项 |
| **硬规冲突** | design.md ↔ `inclusion: always` 页 | 启发式: 硬规的否定式关键词 (`禁` / `MUST NOT`) 在 design 里出现正向表述 | **报候选交人判**, 不断言违规 |
| **范围蔓延** | subtask 描述 ↔ prd | 机械: subtask 关键词在 prd 全文无对应 | 报候选 |
| **置信度** | design 引用的规则 ↔ `status: proposed` | 机械: 精确查 status 字段 | 无假阳性 |
| **接缝存在性** | design 接缝段 ↔ codebase | 走 `map` 骨架符号表或 grep | 报不存在的接缝 |

**输出**: 人可读 + `--json` (供 `skein-checker` 消费)。

**零问题时如实报「零冲突」** —— 硬凑问题会让这道门失去信号价值。

## 4. 为什么不建 `reqs` FTS 索引

原方案有一项「索引 `task/<id>/{prd,design,findings}.md` 建 `reqs` 表」。**本轮砍掉**:

- 用户已定: spec 是 wiki (state), 不是历史 delta 的集合。索引历史 prd 是在检索一堆过时的变更请求
- `analyze` 只需读**当前这一个 task** 的三个文件 —— 直接 open 即可, 建索引是为了跨库检索, 这里没有跨库需求
- 跨 task 查重归 `skein-dedup` (用户已定: 本轮不动)

**砍掉它同时消掉**: 索引更新时机、task 归档后索引残留、与 `.recall.db` 表结构耦合三个问题。

## 5. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 旧四段 prd 处置 | **只 warning 不阻断** | 已有 2 个完成 task + 本轮 8 个在途 task 全是四段, 硬校验会全部卡死 |
| analyze 判定强度 | **报候选交人判**, 不断言违规 | 硬规冲突/范围蔓延本质是语义判断, 脚本只能给启发式候选 |
| analyze 是否写盘 | **只读** | 与 spec-kit 的 analyze 一致; 核查工具一旦会改东西就不敢随便跑 |
| `reqs` FTS 表 | **砍掉** | 见 §4 |
| User Stories 是否进 `_prd_ready` 硬校验 | 校验段**存在**, 不校验条数 | 「极长」是质量要求, 脚本数不出来; 交 grill 与 analyze |
| golden 快照 | 同轮重生 | 模板改动必破快照, 拖到后面会污染其他 task 的测试结果 |

## 6. 测试接缝 (seam)

**唯一接缝 = `analyze` 命令方法 + `_prd_ready` 校验函数**, `tmp_path` 造 task 目录 (prd/design/task.json) 直调。

- 复用 `test_skein.py` 现有的 task 目录构造工具, 不新建 fixture
- `analyze` 五类检查各造一个命中样本 + 一个不命中样本
- 不写盘用例: 跑完断言临时目录文件 mtime 集合无变化

## 7. 已知风险

| 风险 | 缓解 |
|---|---|
| golden 快照重生掩盖真实回归 | 重生前先 diff 快照变更, 确认变更只来自模板段落而非渲染逻辑 |
| 硬规冲突检查假阳性过多 → 变噪声 | 只报候选且标「需人判」; 假阳性多则收紧关键词表, 不放宽到断言 |
| 六段模板拉长 prd, AI 填不满 | 段落含具体格式提示与例子; 填不满属 plan 未收敛, 由 grill 兜 |
| 与本轮在途 8 个 task 的四段 prd 冲突 | 旧 prd 只 warning; 本 task 完成后不回填改造这 8 个 task 的 prd (它们即将 finish) |
