# ADR 0002 · child 两层调度器同构

- 状态: Accepted (2026-06-29)
- 分支: D (parent/child 任务级调度)
- 相关 commit: 23cd0210

## 背景 (Context)

child 是独立 task (完整生命周期)。原设计: child **依次执行** (按依赖顺序, 一个 archive 再启下一个, 非并行)。

这与 subtask 层动态 DAG (并发2, 完成即派) 的 "尽可能快" 哲学不一致。且 child 各自独立 worktree (每 task 1 worktree), 独立 child 间无文件冲突, 技术上可并行。

## 决策 (Decision)

**两层调度器同构**:
- **subtask 层** (任务内): main 跑 subtask DAG, 并发上限 2, **共享 task worktree** (subtask 与 worktree 无绑定)
- **child 层** (任务级): parent 跑 child DAG, 并发上限 2, **各 child 各 worktree** (隔离单位 = task)

child 调度: 独立 child (无依赖) **可并行**; 有依赖 (child B 依赖 child A 产出) 才串行; 并发上限 2; 完成即派下一个。

## 冲突判定差异

| 层 | 隔离单位 | 冲突判定 |
| --- | --- | --- |
| subtask | 共享 task worktree | write-files glob 相交 + exec-scope 相交 + 显式 depends-on |
| child | 各 child 各 worktree | 显式 depends-on + 跨 child 共享产物文件 (各 worktree 故无 worktree 内冲突) |

## 后果 (Consequences)

- ✅ 两层调度哲学一致 (动态 DAG, 不死板依次)
- ✅ 独立 child 并行, 提速
- ✅ parent 持 child DAG (调度权归 parent)
- ⚠️ child 冲突判定简化 (主要靠显式依赖, 因各 worktree 隔离)
- ⚠️ 并发上限 2 同 subtask 层 (防上下文爆炸)

## 备选 (Alternatives)

| 方案 | 否决理由 |
| --- | --- |
| child 一律依次 (原设计) | 牺牲速度; 独立 child 各 worktree 无冲突, 并行安全; 与 subtask 层哲学不一致 (用户否决) |
| child 无并发上限 | 上下文爆炸风险; 与 subtask 层 (并发2) 不对称 |

## 关联

- [ADR 0001](0001-scheduler-is-main.md) (subtask 层调度器 = main; child 层调度器 = parent, 同构)
