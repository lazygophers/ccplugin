# 执行层选择

design / implement 标注每块工作的执行层 (`main / sub-agent / agent-team`)。planning 阶段定层, dispatch 阶段直接读, 不重判。

**硬规 (worktree 约束 + main 写源码默认禁)**: **main 写源码 = 默认禁** (优先派 subagent); 仅特别情况 (≤3 文件微改 / subagent 难处理的上下文密集决策 / 用户显式要求) 例外, 且**必在 task worktree 内写**。实施类 (写源码/落盘) **必须在 task worktree 内执行** — sub-agent / agent-team **共享 task worktree** (不开 per-subagent 子 worktree, subtask 与 worktree 无绑定)。禁在主工作区写源码。

## 3 层模型

| 层 | 协调者 | 上下文 | 通信 | 并发上限 | 适用 |
| --- | --- | --- | --- | --- | --- |
| main 直做 | — | 主对话 | 无 | 1 | **默认禁** (优先派 subagent); 仅特别情况例外 (≤3 文件微改 / subagent 难处理的上下文密集决策 / 用户显式要求), 必在 task worktree 内写 |
| sub-agent | main 逐轮决策 | 隔离 context window | 仅向 main 返回摘要 | 16 (机器上限) | 高量输出隔离 / 并行调研 / 强约束工具 / 大规模同类文件批量改 (并行派) |
| agent-team | leader 协调 + 共享任务列表 | 每 teammate 独立 | SendMessage 直接互发 | 3-5 推荐 | 多假设辩论 / 跨层协调 / 多视角审查 |

## 决策表

```
任务特征                                    → 选层
─────────────────────────────────────────────
≤ 3 文件 + 无并行 + 已知位置 (仅只读探索或特别例外) → main 直做 (实施类默认派 subagent)
辅助任务产高量输出 (调研/报告) + 摘要可用    → sub-agent
独立调研 + 多角度并行 + 摘要回流             → sub-agent 并行 (≤ 16)
teammate 需互相辩论 / 跨层协调               → agent-team (3-5)
≥ 5 同类文件改 / 仓库审计 / 500+ 文件        → sub-agent 并行 (≤ 16) + ultracode
继承完整对话上下文 + 隔离副线探索             → fork (/fork, sub-agent 子选项, 继承对话上下文; 非独立层)
```

## Trellis 特定

| 工作类型 | 推荐层 | 备注 |
| --- | --- | --- |
| 写 / 改 PRD / design / implement 本身 | main | planning 阶段属主线决策 |
| 调研 (外部文档 / 库选型 / 历史变更) | sub-agent (`trellis-research`) | 报告写入 `research/<topic>.md` |
| 实施 + 检查闭环 | sub-agent (`trellis-implement` → `trellis-check`) | 顺序; **main 调度** (动态 DAG 派 trellis-implement 各执行 1 subtask, 见 `scheduling.md`) |
| 多角度并行调研 | sub-agent ×N 并行 | 不同 `research/<topic-N>.md` |
| 多 child 动态调度 | parent 跑 child DAG (并发上限 2, 各 child 各 worktree) | child 间依赖走 parent coordinator (显式 depends-on); 独立 child 可并行 |
| ≥ 5 同类文件批量改 / 全仓审计 | sub-agent 并行 | 文件集不相交, 主 DAG 调度 (见 `scheduling.md`) |

## Isolation 决策 (隔离单位 = task)

隔离单位是 **task**, 不是 subagent: `task.py start` 时 after_start hook 自动建本 task 的 worktree, 该 task 全部执行层 (main / sub-agent / agent-team) **共享**它。subtask 与 worktree **无绑定** — 并行 subagent 在同一 task worktree 内改不相交文件集即可, 不传 `isolation:worktree`。多 worktree 属 opt-in (用户显式同意), 非自动, 非由 subtask 触发。

> 写盘 sub-agent / agent-team 都在**本 task worktree 内**执行 (共享), 禁在主工作区写盘。唯一例外: 纯只读 sub-agent (探索 / 调研 / 审查, 不改盘) 不需 worktree。

| 场景 | worktree | 备注 |
| --- | --- | --- |
| sub-agent 只读探索 / 调研 / 审查 | 共享 task worktree (只读无副作用) | 无写盘则无需关心 |
| sub-agent 写盘 (单文件 / 多文件 / 任意改动) | 共享 task worktree | 与其他并行 subtask 改不相交文件集 |
| ≥ 2 sub-agent 并行写盘 | 共享 task worktree | 文件集不相交 (PRD 调度图保证); 共享文件走串行 |
| agent-team teammate | 共享 task worktree | 按文件集严格分区 + 串行化共享文件 |
| 多 worktree (opt-in) | 用户显式同意一 task 多 worktree 才开 | finish 经映射合并各分支 |

**为何 task 级隔离**: worktree 防并发多 task 互相冲突; 同 task 内并行 subagent 共享 worktree 改不相交文件集即可 (无脏写)。多 worktree 是大并行隔离的 opt-in 能力, 非 subtask 自动触发。

**完成后**: task check 通过 + commit 后, 合并 worktree 改动 → 当前分支 → `git worktree remove` 清理 (after_finish hook 自动跑; 多 worktree 时合并各分支)。

## Trellis 复杂度 → coordinator + 执行层 自动判定

trellis task 进 planning 时按以下表选 coordinator (谁负责调度 + 进度回传):

| 复杂度信号 | Coordinator | 执行层 | 通信机制 |
| --- | --- | --- | --- |
| ≤ 3 subtask + 单视角 | main 自身 | sub-agent (并行) | sub-agent 摘要 → main → 用户 |
| ≥ 4 subtask 或 多视角 / 跨层 / 假设辩论 | agent-team leader | teammate 池 (3-5 人) | SendMessage 互发 + leader 综合 |
| 仓库级审计 / ≥ 100 调用站点 / 500+ 文件迁移 | main | sub-agent 并行 (≤ 16, 主 DAG 调度) | sub-agent 摘要 → main 汇总 |

**自动判定输入**:
- subtask 数: 从 PRD subtask 表 + `subtask/*.md` 文件数计 (> 3 升级 agent-team)
- 视角数: PRD 含 "对比 / 辩论 / 假设验证 / 跨前后端" 语义即升级 agent-team
- 规模: 改动 ≥ 5 同类文件 / 跨包 / 仓库级即拆并行 sub-agent (文件集不相交)

## Coordinator 单线程硬规

- coordinator 禁同时跑多个 subtask (失去调度视角 + 上下文污染)
- 即使 main 自身做某 subtask 也必须串行处理, 完成再启下一个
- subtask 必须派给 sub-agent / teammate 执行, coordinator 仅负责调度 + 进度回传 + 决策
- coordinator 派 subtask 后禁转去做无关事 (失去监督)

## 标注格式

implement.md 每条 subtask 一行:

```
执行层: sub-agent (trellis-implement, 共享 task worktree)
```

design.md 模块表:

| 模块 | 执行层 | 备注 |
| --- | --- | --- |
| M1 | sub-agent | trellis-implement |
| M2 | agent-team | 多视角审查, leader 综合 |

## 错层信号

| 现象 | 错在哪 | 修正 |
| --- | --- | --- |
| sub-agent 改 1 文件 1 函数 | 应 main 直做 | 改 main |
| main 顺序改 ≥ 5 同类文件 | 应并行 sub-agent + ultracode | 拆不相交文件集并行派 |
| 顺序 spawn N 个 sub-agent 各做独立调研 | 应并行 | 一次 spawn N 并行 |
| 单视角任务用 agent-team | 协调成本 > 收益 | 改 sub-agent |
