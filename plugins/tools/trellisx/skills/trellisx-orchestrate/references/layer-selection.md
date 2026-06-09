# 执行层选择

design / implement 标注每块工作的执行层 (`main / sub-agent / agent-team / workflow`)。planning 阶段定层, dispatch 阶段直接读, 不重判。

## 4 层模型

| 层 | 协调者 | 上下文 | 通信 | 并发上限 | 适用 |
| --- | --- | --- | --- | --- | --- |
| main 直做 | — | 主对话 | 无 | 1 | ≤ 3 文件 / ≤ 3 query / 已知 file:line |
| sub-agent | main 逐轮决策 | 隔离 context window | 仅向 main 返回摘要 | 16 (机器上限) | 高量输出隔离 / 并行调研 / 强约束工具 |
| agent-team | leader 协调 + 共享任务列表 | 每 teammate 独立 | SendMessage 直接互发 | 3-5 推荐 | 多假设辩论 / 跨层协调 / 多视角审查 |
| workflow | 脚本 | 脚本变量持有中间结果 | 阶段串接 | 16 并发 / 1000 总 | 仓库级审计 / 大规模迁移 / 多源交叉验证 |

## 决策表

```
任务特征                                    → 选层
─────────────────────────────────────────────
≤ 3 文件 + 无并行 + 已知位置                → main 直做
辅助任务产高量输出 (调研/报告) + 摘要可用    → sub-agent
独立调研 + 多角度并行 + 摘要回流             → sub-agent 并行 (≤ 16)
teammate 需互相辩论 / 跨层协调               → agent-team (3-5)
≥ 5 同类文件改 / 仓库审计 / 500+ 文件        → workflow + ultracode
继承完整对话上下文 + 隔离副线探索             → fork (/fork)
```

## Trellis 特定

| 工作类型 | 推荐层 | 备注 |
| --- | --- | --- |
| 写 / 改 PRD / design / implement 本身 | main | planning 阶段属主线决策 |
| 调研 (外部文档 / 库选型 / 历史变更) | sub-agent (`trellis-research`) | 报告写入 `research/<topic>.md` |
| 实施 + 检查闭环 | sub-agent (`trellis-implement` → `trellis-check`) | 顺序; 由 trellis workflow 编排 |
| 多角度并行调研 | sub-agent ×N 并行 | 不同 `research/<topic-N>.md` |
| 多 child 同步推进 | 各 child 独立 (按其 implement.md) | child 间通信走 main coordinator |
| ≥ 5 同类文件批量改 / 全仓审计 | workflow | 用户显式同意才启 |

## Isolation 决策

| 场景 | isolation: worktree | 备注 |
| --- | --- | --- |
| sub-agent 只读探索 | 否 | 无写冲突 |
| sub-agent 单独改文件且与其他并行 sub-agent 改文件不交 | 否 | 直接共享工作树 |
| ≥ 2 sub-agent 并行改文件且文件集相交 | 是 | 避免脏写 |
| ≥ 2 sub-agent 并行改不同 deliverable 但同一 task 目录 | 是 | 避免 .trellis/tasks/<dir>/ 写竞争 |
| workflow 各 agent 并行写 | 是 (脚本设 `isolation: "worktree"`) | 开销 ~200-500ms/agent, 必要时才开 |
| agent-team teammate | 不支持 worktree | 按文件集分区任务 |

## Trellis 复杂度 → coordinator + 执行层 自动判定

trellis task 进 planning 时按以下表选 coordinator (谁负责调度 + 进度回传):

| 复杂度信号 | Coordinator | 执行层 | 通信机制 |
| --- | --- | --- | --- |
| ≤ 3 subtask + 单视角 | main 自身 | sub-agent (并行) | sub-agent 摘要 → main → 用户 |
| ≥ 4 subtask 或 多视角 / 跨层 / 假设辩论 | agent-team leader | teammate 池 (3-5 人) | SendMessage 互发 + leader 综合 |
| 仓库级审计 / ≥ 100 调用站点 / 500+ 文件迁移 | main + workflow | workflow agent (脚本编排) | 脚本变量串接 + 阶段摘要 |

**自动判定输入**:
- subtask 数: 从 PRD subtask 表 + `subtask/*.md` 文件数计 (> 3 升级 agent-team)
- 视角数: PRD 含 "对比 / 辩论 / 假设验证 / 跨前后端" 语义即升级 agent-team
- 规模: 改动 ≥ 5 同类文件 / 跨包 / 仓库级即升级 workflow

## Coordinator 单线程硬规

- coordinator 禁同时跑多个 subtask (失去调度视角 + 上下文污染)
- 即使 main 自身做某 subtask 也必须串行处理, 完成再启下一个
- subtask 必须派给 sub-agent / teammate / workflow agent 执行, coordinator 仅负责调度 + 进度回传 + 决策
- coordinator 派 subtask 后禁转去做无关事 (失去监督)

## 标注格式

implement.md 每条 subtask 一行:

```
执行层: sub-agent (trellis-implement, isolation: worktree)
```

design.md 模块表:

| 模块 | 执行层 | 备注 |
| --- | --- | --- |
| M1 | sub-agent | trellis-implement |
| M2 | workflow | 全 model lint, 用户授权后启 |

## 错层信号

| 现象 | 错在哪 | 修正 |
| --- | --- | --- |
| sub-agent 改 1 文件 1 函数 | 应 main 直做 | 改 main |
| main 顺序改 ≥ 5 同类文件 | 应 workflow + ultracode | 改 workflow, 让用户授权 |
| 顺序 spawn N 个 sub-agent 各做独立调研 | 应并行 | 一次 spawn N 并行 |
| 单视角任务用 agent-team | 协调成本 > 收益 | 改 sub-agent |
