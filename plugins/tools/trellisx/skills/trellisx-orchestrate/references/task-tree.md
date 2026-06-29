# Parent / Child Task Tree

1 task 含 ≥ 2 独立可验收 deliverable → 拆 parent + 多 child。Parent 持源需求集 + child map + 跨 child 验收 + 集成 review, **是 child 级调度器** (持 child DAG); child 持单 deliverable 完整生命周期 (plan / impl / check / archive), **各自独立 worktree**。

**child 动态调度 (非全串行)**: parent/child 是**任务级动态调度分解**。**parent 是 child 级调度器**: 持 child DAG (依赖图), 动态派发 child —— **独立 child (无依赖) 可并行** (各 child 各自 worktree, 并发上限 2); **有依赖才串行** (child B 依赖 child A 产出 → A archive 再启 B); 完成即派下一个 (不空等全部)。**两层调度器同构**: task 内 main 跑 subtask DAG (并发 2, 共享 task worktree); parent 跑 child DAG (并发 2, 各 child 各 worktree) —— 隔离单位不同, 调度模型一致, 见 `scheduling.md §8`。**child ≠ subtask**: child 是独立 task (任务级动态调度), subtask 是任务内执行单元 (共享 task worktree); child 本身是 task, 其 exec 也可再 subtask 拆分。

## 何时拆

| 信号 | 决策 |
| --- | --- |
| PRD 列 ≥ 2 deliverable 且各自可独立交付 | 必拆 |
| 单 deliverable 但内部模块 ≥ 5 个 | 不拆, 走 implement.md subtask |
| 不同 deliverable 共享 ≥ 80% 代码改动 | 不拆 (强行拆制造耦合) |
| 不同 deliverable 验收方式 / 时间窗 / owner 不同 | 必拆 |

## 不要把 parent 当依赖系统

Parent / child 是组织结构 + 动态调度。child 之间若有依赖: **在 child 的 prd.md / implement.md 内写显式 depends-on** (parent 读以建 child DAG), 不要靠目录树位置隐含。parent 据此判定: 无依赖边 = 可并行 (各 worktree); 有依赖边 = 串行。

## 操作 (trellis 命令)

```bash
# 新建 child (推荐)
python3 ./.trellis/scripts/task.py create "<child-title>" --slug <name> --parent <parent-dir>

# 关联已存在 task 为 child
python3 ./.trellis/scripts/task.py add-subtask <parent> <child>

# 解除 (错关时)
python3 ./.trellis/scripts/task.py remove-subtask <parent> <child>
```

## Parent task 内容

Parent 的 `prd.md` 必含:

```markdown
## Child Task Map

| Child | Slug | 交付物 | 验收 | depends-on | 状态 |
| --- | --- | --- | --- | --- | --- |
| C1 | <slug> | <D1 from parent PRD> | <如何独立验收> | — | planning / in_progress / done |
| C2 | <slug> | <D2> | <如何验收> | C1 | planning |

## 跨 Child 验收

- [ ] C1 + C2 集成场景 X
- [ ] C1 数据被 C2 正确消费
- [ ] 整体性能 / 兼容性指标

## 集成 Review

- 在所有 child 完成后, parent 跑一次端到端 review
- Review 命令: <列出>
```

Parent 通常**不直接**做 implementation 工作, 除非也有非 child 范围的直接交付 (e.g. 整体重构的脚手架)。

## Child task 内容

每个 child 独立的 prd / design / implement, 仿佛它是顶层 task。差别仅:
- `task.json` 含 parent 指针 (由 task.py 维护)
- child PRD 头部一句话引 parent 上下文: `Parent: <parent-slug> — <parent 目标摘要>`

## 拆分自检

- [ ] 每个 child 可独立 task.py start / complete
- [ ] 每个 child 验收不依赖其他 child 同步进度 (除非显式 depends-on)
- [ ] child 间依赖在 child 自己的 prd / implement 里写明 depends-on (不靠目录隐含)
- [ ] parent PRD 含 child map 表 (含 depends-on 列) + 跨 child 验收
- [ ] parent 知道自己是否要做直接工作 (默认不做)
- [ ] parent 持 child DAG: 独立 child 可并行 (并发上限 2, 各 child 各 worktree), 有依赖才串行

