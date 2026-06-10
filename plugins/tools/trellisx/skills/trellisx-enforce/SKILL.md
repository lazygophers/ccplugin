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
| **实施** | 写代码 / 改文件 / 跑会改动状态的命令 — **任何会落盘的工作** | **无条件建 task 走 planning + 拆 ≥ 2 subtask + 派 agent 执行** (main 不直接写源码) |
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
  → ② planning              (加载 trellisx-orchestrate, 拆 ≥ 2 subtask, 写 PRD/design/implement/subtask)
  → ③ 每 subtask 派执行者    (sub-agent: isolation:worktree / agent-team 成员: 指定 .trellis/worktrees/<subtask>)
  → ④ main 收集结果 + 协调   (main 禁自己写源码 / 禁自己切 worktree)
```

**main = 纯协调者** (硬规):
- main 只做: 拆 subtask / 写 `.trellis/` 文档 (PRD/design/implement/subtask) / 派发 / 收结果 / 合并 / 决策
- main **禁直接写源码** — 任何源码实施必须派 sub-agent 或 agent-team 成员执行
- main **禁自己 cd / EnterWorktree 进 worktree 操作** — worktree 是执行者 (agent) 的, 不是 main 的

**subtask 拆分 (硬规)**:
- task 必须拆 **≥ 2 subtask** (即使看起来单一, 也按 实施 / 验证 / 文档 等维度拆)
- 每 subtask 独立可验收, 交给一个执行者 (agent)

**严禁**:
- 收到实施需求后直接 Read 分析 → 写代码 → 撞拦截才回头补 task (**打补丁式往回锤**)
- 草草建个空 task 就继续 (跳过 planning / 不拆 subtask)
- **main 自己写源码 / 自己进 worktree 干活** (该派 agent)
- "先做着, 出问题再说" — 顺序错 = 流程失败, 立即停回 ① 重走

## 2. 任务归属判定 (建 task 前必判)

判断本轮输入是**新任务**还是**对现有 task 的补充**:

| 归属 | 判定 | 动作 |
| --- | --- | --- |
| 现有任务补充 | 对当前 active task 的扩展 / 修改 / 细化 / 边界调整 | 回复以 `[trellisx-continue-{task-name}]` 开头; 补充该 task (更新 PRD / 调度图 / 受影响 subtask 文件); 重新评估调度; **禁新建 task** |
| 新任务 | 与当前 active task 无关, 或无 active task, 或用户显式说"新任务/新需求/换一个" | 回复以 `[trellisx-new-task]` 开头; `task.py create` → 走 planning 拆 subtask → 派 agent (各自 worktree) |

## 3. Worktree 隔离 (subtask/agent 级, 非 task 级)

**worktree 绑定执行者 (agent), 不绑定 task。每个 subtask 的执行者在自己的 worktree 内干活, main 永不进 worktree。**

| 执行者 | worktree 来源 | 路径 | 生命周期 |
| --- | --- | --- | --- |
| **sub-agent** | `Agent` 工具 `isolation: worktree` | Claude Code 自动 (`.claude/worktrees/`) | Claude Code 自动建 + 完成自动销 |
| **agent-team 成员** | main 手动指定 | `.trellis/worktrees/<subtask>` | main 派发前 `git worktree add`, 成员完成后 main 合并 + `git worktree remove` |

**硬规**:
- 任何写源码的 subtask **必须**在某 worktree 内执行 (sub-agent isolation / agent-team 指定路径)
- **main 不写源码、不进 worktree** — main 在主工作区只写 `.trellis/` 文档 + 协调
- agent-team 成员 worktree 用完, main 必须合并 (或丢弃) + 移除; 残留 = 环境污染, 禁宣告 task 完成
- `.trellis/worktrees/` 已被 `.trellis/.gitignore` 排除, 不进主仓库追踪

为何: worktree 隔离保证每个 subtask 改动落独立树, main 合并前可 review diff, 失败整树丢弃零污染; main 纯协调避免主工作区被污染。

## 4. 派执行者 (sub-agent / agent-team) 规则

| 执行者类型 | 何时用 | worktree |
| --- | --- | --- |
| sub-agent | 单 subtask 隔离执行 (实施/调研/检查) | 写盘 → **MUST `isolation: worktree`**; 纯只读可省 |
| agent-team 成员 | 多 subtask 需互相协调 / 辩论 | main 派发前给每成员指定 `.trellis/worktrees/<subtask>` |
| workflow | 仓库级批量 (≥ 5 同类文件) | 脚本设 `isolation: "worktree"` |

- 写盘执行者**无 worktree → 不派** (PreToolUse 会拦 `Agent` 无 isolation:worktree)
- ≥ 2 并行写盘执行者 → 各自独立 worktree, 避免脏写
- 派发 prompt 必须含 6 字段 (目标/已知/工作目录与范围/输出格式/验收标准/失败处理) + `Active task:` 前缀

## 5. 完成判定

task 宣告完成前必须全部满足:

- [ ] 全部 subtask done + 验收通过
- [ ] trellis-check 综合验证通过
- [ ] spec 沉淀 (走 `trellisx-spec` sediment 模式, 按需)
- [ ] commit
- [ ] **全部 agent worktree 已合并 + 移除 (sub-agent 自动; agent-team 成员 .trellis/worktrees 手动清理)**
- [ ] 非平凡发现落 cortex

任一未满足 → 禁宣告完成。

## 自检 (每个实施轮次开始时)

1. 本轮回复加了 `[trellisx-*]` 前缀? (§0)
2. 实施类? 一律建了 task? 探索类? 按复杂度判过? (§1)
3. 判过归属? 新任务 vs 补充? (§2)
4. 每 subtask 派给 agent 在其 worktree 执行? main 没自己写源码? (§3)
5. 写盘执行者带 worktree (isolation / .trellis/worktrees)? (§4)
6. 完成前 worktree 已清理? (§5)

