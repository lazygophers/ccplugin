# task 生命周期时间线 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] task 生命周期时间线成为可回溯的**事件日志**, 落在 per-task 的 `task.json` 独立字段里, 不再由前端从几个扁平时间戳猜阶段。
- [ ] **状态回滚被如实记录并展示** —— check 打回、research⇄规划往返、redo 复位, 每一次都留痕, 看板能看出"这个 task 卡在验收跑了 3 轮"。
- [ ] 详情页时间线同时呈现**预规划骨架**(还剩哪些阶段)与**已发生的真值**(什么时候到的、跑了几轮), 已发生的一律以事件日志为准。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 范围内: timeline 字段的数据模型与写入、task 状态迁移与 subtask 状态迁移两类事件、后端输出、详情页渲染。
- 范围外: 归档 task 的历史回填 (无原始事件, 不臆造); 时间线的编辑/删除 (只追加, 不可改); 甘特图与工时预测。
- 约束: 事件**只追加不修改**, 已落盘的历史不因后续状态变化而重写。
- 约束: 老 task 无 timeline 字段, 读取端必须容错 (缺失视为空列表, 退回既有扁平时间戳渲染), 禁数据迁移脚本。
- 约束: 单事件体积要小 —— timeline 随 task.json 每次 save 全量重写, 长 task 会累积上百条。

## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a 用户, I want 在详情页一眼看出 task 现在走到哪个阶段、还剩哪些阶段, so that 不用去读 task.json 猜进度。
2. As a 用户, I want 看到 check 被打回过几轮, so that 判断这个 task 是不是在反复返工。
3. As a 用户, I want 看到每个阶段的真实进入时间, so that 知道卡在哪一段最久。
4. As a 用户, I want 看到 subtask 的 running/done/failed 与 task 阶段混在同一条流水里, so that 理解"为什么这个 task 在进行中待了两天"。
5. As a 用户, I want 某个 subtask 失败重跑时能看到失败原因, so that 不用翻 note 字段。
6. As a main (编排层), I want 状态迁移自动记事件, so that 不需要在每个命令里手写一遍时间线维护。
7. As a main, I want 回滚事件带 rollback 标记, so that 能机读地统计返工率。
8. As a 开发者, I want 老 task (无 timeline) 打开详情页不报错, so that 不必为此写迁移脚本。
9. As a 开发者, I want research⇄规划往返被记成两条独立事件, so that 调研轮次可数。
10. As a 用户, I want 时间线里未发生的阶段置灰占位, so that 区分"没到"和"跳过了"。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] `TaskData` 有 `timeline` 字段, 元素含 `kind`(task|subtask) / `status` / `at` / `sid`(subtask 事件) / `note` / `rollback`。
- [x] 6 处 task 状态迁移 (research/plan/confirm/check/finishing/finish) 与 create 各自追加一条 task 事件。
- [x] subtask 的 claim·start / done / fail 各自追加一条 subtask 事件, fail 事件带 note。
- [x] 状态序号回退时事件带 `rollback: true` (research→规划中、check→进行中 均命中)。
- [x] 事件只追加: 同一 task 连续多次进入 `check` 产生多条 `check` 事件, 不覆盖。
- [x] 后端 task 详情输出携带 timeline 原样数组。
- [x] 详情页渲染完整阶段骨架, 已发生节点取 timeline 真实时间并实心高亮, 未发生置灰占位。
- [x] 同一阶段出现 ≥2 次时该节点显示 `↺ N 轮` 角标。
- [x] 无 `timeline` 字段的老 task 详情页正常渲染不报错。

## 验证方式
每条验收标准的验证手段与通过标准 (plan 阶段必填):
- 数据模型与写入: `uv run pytest plugins/tools/skein/scripts/tests/test_timeline.py` —— 通过标准: 全绿, 覆盖追加语义、rollback 标记、老数据缺字段容错。
- 全量回归: `uv run pytest plugins/tools/skein/scripts/tests/` —— 通过标准: 失败数不超过改前基线 (当前基线 1 failed = .venv 缺 mypy 的环境问题)。
- 类型: `mypy --strict` 对 `scripts/` —— 通过标准: 不新增错误。
- 前端类型与构建: `npx tsc --noEmit` + `npm run build` —— 通过标准: 0 error, 构建产出 dist。
- 端到端人工核对: 对一个真实跑过 check 打回的 task 打开详情页 —— 通过标准: 时间线出现两条"检查中"且带 `↺ 2 轮`, 未到的阶段置灰。

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- 只测**外部可观察行为**: 跑 CLI 命令 → 读回 task.json 断言 timeline 内容。不测写入 helper 的内部签名 (那是实现细节, 会随重构碎)。
- 先例: `tests/test_dag.py` 的 `skein_cli` fixture 跑真命令 + 解析 JSON 输出, 本任务沿用同一套 fixture, 不新造 harness。
- 反面教材: 上一轮的 `test_agent_routing_by_phase` 直接 import 私有 `_agent_for`, 内部一改就红。本任务禁 import 私有函数。
- 前端渲染不写单测 (无现成组件测试基建, 为此搭一套不划算), 靠 `tsc` + 人工核对兜底。

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein subtask list task-timeline`)
