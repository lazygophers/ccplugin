---
name: trellisx-enforce
description: Trellis 任务执行的强制规范 (硬约束, 不可绕过)。覆盖任务门禁 (实施一律建 task, 探索按复杂度)、worktree 生命周期 (start 创建 / 结束合并+移除)、任务归属判定 (新任务 vs 现有补充)、回复前缀标记、完成判定。**trellis 项目内每次用户输入都必须立即加载本 skill 阅读并逐条遵守**, 不论输入类型。hook 每轮要求加载本 skill。
when_to_use: trellis 项目 (.trellis/ 存在) 内, **每次用户输入都强制加载**, 无条件、不论是否涉及开发。被 trellisx hook 每轮注入要求加载。
user-invocable: false
---

# trellisx-enforce — Trellis 任务执行强制规范

**本 skill 是硬约束, 不是建议。** trellis 项目内任何开发 / 实施任务, 动手前必须逐条核对本规范。违反任一条 = 流程错误, 立即停止纠正。

## 0. 回复前缀标记 (每条回复, 强制)

**任何回复**必须以 `[trellisx` 前缀开头, 不可遗漏 (Stop hook 会校验, 缺则打回重答):

- 有 active task: `[trellisx-{status}-{task-name}]`, `status` = planning / in_progress / check / done / blocked
  - 例: `[trellisx-in_progress-oauth-login]`
- 无 active task (闲聊 / 咨询 / 无任务): `[trellisx]`
- 前缀必须在回复最前面; 若有其他开头要求, `[trellisx...]` 仍排第一

## 1. 任务门禁 (动手前必判)

**第一轴: 先分 实施 vs 探索。**

| 类型 | 判定 (看意图 + 是否写盘) | 动作 |
| --- | --- | --- |
| **实施** | 写代码 / 改文件 / 跑会改动状态的命令 / 派写盘 agent — **任何会落盘的工作** | **无条件强制建 trellis task 走 planning** (加载 `trellisx-orchestrate` skill), **不看 subtask 数量**, 哪怕只改一行 |
| **探索** | 纯只读: 读文件 / grep / 搜索 / 分析 / 回答问题 / 调研, 不写盘 | **按复杂度决定** (见下) |

**探索类型的二级判定** (仅探索适用):

| 探索复杂度 | 动作 |
| --- | --- |
| 简单 (单点查询 / 读几个文件 / 直接回答) | 可不建 task, 直接做 |
| 复杂 (多源调研 / 系统性分析 / 跨多模块梳理 / 需落档报告) | 建 task 承载 (research/ 产物 + 进度追踪) |

判定准则:
- **实施一律建 task** — "只改一行 / 看起来简单"不是绕过理由; 落盘即建 task
- 探索靠不准 → 倾向建 task (复杂探索的报告需 task 承载)
- 一个 prompt 含 ≥ 2 独立实施目标 → 建 task 后拆 parent + child

### 执行顺序铁律 (实施类, 禁跳步 / 禁先做后补)

确认是实施需求后, **第一个工具调用就必须开始走以下顺序**:

```
确认实施需求
  → ① task.py create        (建任务)
  → ② planning              (加载 trellisx-orchestrate, 写 PRD/design/implement/subtask)
  → ③ git worktree add      (建 worktree)
  → ④ 在 worktree 内 execute (写盘目标用 worktree 路径)
```

**严禁**:
- 收到实施需求后直接 Read 分析 → 写代码 → 撞拦截才回头补 task (**打补丁式往回锤**)
- 草草建个空 task 就继续 (跳过 planning)
- 建了 task 却在主工作区写源码 (跳过 worktree)
- "先做着, 出问题再说" — 顺序错 = 流程失败, 立即停回 ① 重走

## 2. 任务归属判定 (建 task 前必判)

判断本轮输入是**新任务**还是**对现有 task 的补充**:

| 归属 | 判定 | 动作 |
| --- | --- | --- |
| 现有任务补充 | 对当前 active task 的扩展 / 修改 / 细化 / 边界调整 | 回复以 `[trellisx-continue-{task-name}]` 开头; 补充该 task (更新 PRD / 调度图 / 受影响 subtask 文件); 重新评估调度; **禁新建 task** |
| 新任务 | 与当前 active task 无关, 或无 active task, 或用户显式说"新任务/新需求/换一个" | 回复以 `[trellisx-new-task]` 开头; 先建 worktree (§3) → `task.py create` → 走 planning (加载 `trellisx-orchestrate`) |

## 3. Worktree 生命周期 (强制, 绑定整个 task)

**任何 task 执行必须在独立 worktree 内, 主工作区保持干净。**

| 时机 | 动作 |
| --- | --- |
| 新任务启动 (task.py start 前/后) | **立即创建 task 专属 worktree** (`git worktree add`), 后续所有改动落该工作树 |
| execute / check 期间 | 全部读写限于 worktree |
| check 通过 + commit 后 | 合并 worktree 改动 → 当前分支 |
| 合并完成 | **立即 `git worktree remove`** 移除, 确保环境干净 |
| task 失败 / 取消 | 丢弃改动 + `git worktree remove --force` 清理 |

**硬规**: task 结束 (done / cancelled) 前必须完成 worktree 合并 (或丢弃) + 移除。**残留 worktree = 环境污染, 禁宣告 task 完成**。

为何强制: worktree 隔离保证改动落独立树, main 合并前可 review diff, 失败整树丢弃零污染。隔离开销 (~200-500ms) 远低于脏写排查成本。

## 4. Sub-agent / workflow worktree 隔离

派写盘 sub-agent / workflow agent 时:

- 写盘 (改任何文件) → **MUST 带 `isolation: worktree`**, 缺则不派
- 仅纯只读 (探索 / 调研 / 审查, 不改盘) → 可省
- ≥ 2 并行写盘 sub-agent → 必须各自 worktree, 避免脏写
- agent-team teammate 引擎不支持 worktree → 退化: 按文件集严格分区 + 串行化共享文件

## 5. 完成判定

task 宣告完成前必须全部满足:

- [ ] 全部 subtask done + 验收通过
- [ ] trellis-check 综合验证通过
- [ ] spec 沉淀 (走 `trellisx-spec` sediment 模式, 按需)
- [ ] commit
- [ ] **worktree 已合并 + `git worktree remove` 移除 (环境干净)**
- [ ] 非平凡发现落 cortex

任一未满足 → 禁宣告完成。

## 自检 (每个实施轮次开始时)

1. 本轮回复加了 `[trellisx-*]` 前缀? (§0)
2. 实施类? 一律建了 task? 探索类? 按复杂度判过? (§1)
3. 判过归属? 新任务 vs 补充? (§2)
4. task 在 worktree 内执行? (§3)
5. 写盘 sub-agent 带 isolation: worktree? (§4)
6. 完成前 worktree 已清理? (§5)

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD / design / implement / subtask
- `trellisx-spec` — spec init / optimize / sediment
