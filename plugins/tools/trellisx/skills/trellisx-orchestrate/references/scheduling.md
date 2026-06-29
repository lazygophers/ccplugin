# 动态 DAG 调度 (main 调度器)

> 本 reference 是 exec 阶段 subtask 调度的权威规程。**调度器 = main, 非 trellis-implement**。main 在 exec 阶段读各 subtask 文件的资源声明 + 依赖, 静态算冲突 → 建 DAG → 动态派 trellis-implement (并发上限 2) → 任一返回即更新态、立即派下一个 → 全 done 转 trellis-check。

## 0. 调度边界 (谁调度谁执行)

| 角色 | 职责 | 不做 |
| --- | --- | --- |
| **main (调度器)** | 读 subtask 文件 → 算冲突 → 建 DAG → 动态派 trellis-implement (并发≤2) → 收 notification 更新态 → 查新 ready → 立即派 → 全 done 转 trellis-check; failed 走 failure-recovery | 不直接写源码; 不一次性并行派所有 subtask; 不空等全部返回 |
| **trellis-implement (执行器)** | 接 1 个 subtask → 在本 task worktree 内执行 (Read/Write/Edit/Bash) → 返回产物 + 自验结果 | 不调度; 不派 subagent; 不递归; 不并行派其他 subtask |

**Recursion Guard (sub-agent 自防护)**: trellis-implement 的工具集仅 Read/Write/Edit/Bash, **无 Agent/Task 工具** —— 物理上不能派 subagent, 也不能递归派 trellis-implement/trellis-check。只有 main session 能派 trellis-implement / trellis-check agent。故「调度」必归 main, implement 纯执行。

## 1. 资源声明 (每 subtask 文件两字段)

planning 阶段每个 subtask 文件 frontmatter 必填:

| 字段 | 取值 | 用途 |
| --- | --- | --- |
| `write-files` | 写盘文件 glob 列表 (如 `["packages/api/src/auth/**", "packages/api/tests/auth.test.ts"]`) | 冲突判定①: 两 subtask 的 write-files glob 相交 (同文件) = 有依赖边 |
| `exec-scope` | `none` / `package:<pkg>` / `project` | 冲突判定②: 执行资源作用域。`none`=纯 Read 不跑命令(只读探索); `package:<pkg>`=包级测试/运行/lint/build (作用域限本包); `project`=项目级命令 (作用域全仓, 如全量 test/build/lint) |

**exec-scope 判定**: 包测试/包 lint/包 build = `package:<pkg>`; 项目级测试/全仓 build/跨包 lint = `project`; 纯探索审查不改不跑 = `none`。两 subtask 的 exec-scope 相交 = 有依赖边 (避免并行跑命令互相占用进程/锁/端口)。

**exec-scope 相交规则**:
- `none` 与任何 scope 不相交 (只读无副作用)
- `package:A` 与 `package:A` 相交 (同包命令并发会抢资源)
- `package:A` 与 `package:B` 不相交
- `project` 与任意 `package:*` 相交 (项目级命令作用全仓, 含所有包)
- `project` 与 `project` 相交

## 2. 冲突判定算法 (planning 末 main 静态算)

两 subtask (Si, Sj) 有**依赖边** ⟺ 满足任一:

1. **写盘相交**: `Si.write-files ∩ Sj.write-files ≠ ∅` (glob 相交 = 同文件)
2. **执行作用域相交**: `Si.exec-scope ∩ Sj.exec-scope ≠ ∅` (同包 or 任一为 project)
3. **显式依赖**: `Sj.depends-on` 含 Si (或 Si.blocks 含 Sj)

**无依赖边 = 可并行**。有依赖边 = 必串行 (上游 done 才解锁下游)。

伪代码:

```python
def has_dependency_edge(Si, Sj):
    # ① 写盘相交
    if glob_intersect(Si.write_files, Sj.write_files):
        return True
    # ② 执行作用域相交
    if exec_scope_intersect(Si.exec_scope, Sj.exec_scope):
        return True
    # ③ 显式依赖
    if Si.id in Sj.depends_on or Sj.id in Si.depends_on:
        return True
    return False

def build_dag(subtasks):
    edges = []
    for Si, Sj in pairs(subtasks):
        if has_dependency_edge(Si, Sj):
            edges.append((Si, Sj))   # 无向 → 拓扑序定方向
    return DAG(edges)
```

## 3. 5 态模型

每个 subtask 在调度循环中处 5 态之一:

| 态 | 含义 | 转入条件 |
| --- | --- | --- |
| `ready` | 无未完成依赖, 可立即派 | 所有上游依赖 done; 资源未被占用 |
| `blocked` | 有上游未 done 或资源被占用, 等待 | 初始态 (原 planned 并入); 上游未完成; exec-scope 冲突的并行 subtask 仍在跑 |
| `running` | 已派 trellis-implement, 未返回 | main 派发后 |
| `done` | trellis-implement 返回 + 自验通过 | 返回且验收命令过 |
| `failed` | trellis-implement 失败 / 自验不过 | 返回但失败, 转入 failure-recovery |

> 原 `planned` 态并入 `blocked` (已写文件但依赖/资源未就绪 = blocked); 新增 `failed`。

## 4. 动态调度循环 (main, 并发上限 2)

```
# main 在 exec 阶段循环
while exists(subtask not in {done, failed}):
    ready_set = { s | s.status == ready }              # 查 ready
    slots = 2 - count(s | s.status == running)          # 剩余并发槽
    to_dispatch = take(ready_set, min(len(ready_set), slots))
    for s in to_dispatch:
        s.status = running
        dispatch trellis-implement(s)                   # 共享 task worktree, 并行

    if no running and no ready:                          # 死锁检测
        break → failure-recovery (全部 blocked 无解锁)

    wait for any trellis-implement notification          # 不空等全部
    on notification(s):
        if s 自验通过:  s.status = done; 解锁下游 (blocked → ready if 上游全 done)
        else:           s.status = failed → failure-recovery

    loop (立即查新 ready, 立即派, 不等全部)

all done → dispatch trellis-check
```

**关键性质**:
- **并发上限 2**: 同一时刻最多 2 个 trellis-implement 在跑 (共享 task worktree 改不相交文件集)。
- **完成即派**: 任一 trellis-implement 返回 (notification) 即更新态、查新 ready、立即派下一个, **不空等所有 running 返回**。
- **notification 驱动**: 不轮询, 不 `sleep`; trellis-implement 返回触发下一轮派发。
- **死锁检测**: 若无 running 且无 ready 但仍有 blocked → 全部 blocked → failure-recovery (依赖环或资源死锁)。

## 5. 失败处理

| subtask 返回 | main 动作 |
| --- | --- |
| 自验通过 | → done, 解锁下游 |
| 失败 / 自验不过 | → failed → 走 `failure-recovery.md` (重派 ≤3 次 / 换执行者 / 回 planning 重拆); failed subtask 的下游保持 blocked 直至 failed 解决 |
| 全部重试耗尽 | 该 subtask 终态 failed, 上报, 不崩整体; 收尾时 trellis-check 会捕获缺失产物 |

> 同一 subtask 累计失败 3 次禁第 4 次盲目重试, 回 planning 重拆 (见 failure-recovery.md)。

## 6. 与 trellis-implement 的边界 (再强调)

- **main 是唯一调度器**: 算冲突、建 DAG、动态派、收态、转 check 全归 main。
- **trellis-implement 不调度不递归**: 每次只接 1 个 subtask, 执行完返回, 不派 subagent, 不并行派其他 subtask。
- **Recursion Guard**: trellis-implement 工具集无 Agent/Task, 物理上无法调度; 只有 main session 能派 trellis-implement/trellis-check。
- **共享 task worktree**: 并行的 ≤2 个 trellis-implement 在同一 task worktree 内改不相交文件集 (冲突判定保证); subtask 与 worktree 无绑定。

## 7. 自检

- [ ] 每 subtask 文件 frontmatter 含 `write-files` + `exec-scope`
- [ ] main 在 exec 前静态算了冲突 DAG (三类边)
- [ ] 并发不超过 2 个 trellis-implement
- [ ] 任一 trellis-implement 返回即触发下一轮派发 (不空等)
- [ ] failed subtask 走 failure-recovery, 下游保持 blocked
- [ ] trellis-implement 不派 subagent (Recursion Guard)
