---
name: trellisx-enforce
description: Trellis 任务执行的强制规范 (硬约束, 不可绕过)。覆盖任务门禁 (subtask ≥ 2 强制建 task)、worktree 生命周期 (start 创建 / 结束合并+移除)、任务归属判定 (新任务 vs 现有补充)、回复前缀标记、完成判定。**trellis 项目内每次用户输入都必须立即加载本 skill 阅读并逐条遵守**, 不论输入类型。hook 每轮要求加载本 skill。
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

动手写代码 / 改文件 / 系统搜索后准备改动前, **必须先判断任务复杂度**:

| 复杂度 | 判定 | 动作 |
| --- | --- | --- |
| subtask ≤ 1 | 单步 / 单文件 / 无独立子目标 | 可 main 直做 (仍需 worktree, 见 §2) |
| subtask ≥ 2 | 多步 / 多文件 / 多独立目标 / 需调度 / 一个 prompt 含 ≥ 2 独立问题 | **禁直接动手**, 必须先建 trellis task 走 planning (加载 `trellisx-orchestrate` skill) |

判定准则:
- 按"是否拆得出 ≥ 2 个独立可验收 subtask"判定, **不是**按"任务看起来复不复杂"
- 一个 prompt 内含 ≥ 2 个独立问题 / 目标 = 必建 task (可拆 parent + child)
- 判定靠不准 → 倾向建 task (建 task 成本 < 绕过返工成本)
- 已绕过 task 开始实施后才发现复杂 → **立即停**, 补建 task 重走 planning

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
2. 判过复杂度? subtask ≥ 2 走了 task? (§1)
3. 判过归属? 新任务 vs 补充? (§2)
4. task 在 worktree 内执行? (§3)
5. 写盘 sub-agent 带 isolation: worktree? (§4)
6. 完成前 worktree 已清理? (§5)

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD / design / implement / subtask
- `trellisx-spec` — spec init / optimize / sediment
