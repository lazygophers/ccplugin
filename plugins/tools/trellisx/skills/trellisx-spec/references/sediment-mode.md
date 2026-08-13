# sediment 模式 (任务收尾沉淀)

trellis task 完成 Phase 3 收尾时, 把"本任务学到的非平凡规则"沉淀回 `.trellis/spec/`。由 `trellisx-orchestrate` Phase 3 触发, 或用户显式调用。

## 何时跑

- `task.py complete` 前
- 任务 quality check 全通过后, commit 前
- 用户说 "沉淀这个任务" / "把这次学到的写进 spec" / "记住这次教训"

## 输入

读 active task 的:

- `prd.md` — 任务目标与约束
- `design.md` — 技术决策与取舍
- `implement.md` — 执行清单与验证
- `subtask/*.md` — 各 subtask 文件 (含历史 / 风险 / 回滚)
- `journal-*.md` — 开发流水账 (踩坑 / 教训 / 反复)
- `research/*.md` — 调研结论

提炼**非平凡发现**, 不沉淀已知常识。

## 非平凡发现判定

| 该沉淀 | 不沉淀 |
| --- | --- |
| 踩了坑后才发现的隐藏约束 | 任务目标本身 |
| 跨任务可复用的契约 | 单任务具体技术细节 |
| 反复犯的同类错误 | 一次性偶发错误 |
| 文档没写但必须遵守的隐规 | 文档已写的明规 |
| "下次不能再 X" 的教训 | "这次幸运没踩雷" |
| 调研得出的最佳实践 | 调研得出的方案对比 |

## 增量提案模板

阶段 2 propose 输出:

```
sediment 模式增量提案 (来自 task: <task-dir>)

#1 PATCH .trellis/spec/guides/core-contracts.md
   位置: ## 跨层调用 节末
   增量: + 跨层共享对象必须用 readonly / immutable, 禁可变共享 (本任务踩坑: SubtaskS3 因可变共享导致并发污染)
   验证: `grep -rE '\b(let|var)\s+\w+\s*=\s*\{[^}]*shared' src/` 必须 0 行

#2 NEW .trellis/spec/guides/concurrency.md (~30 行)
   理由: 本任务踩了 3 次并发坑 (S3 / S5 / S7), 已有 spec 无并发节
   首版内容: 不可变共享 / 锁顺序 / 死锁检测 3 条 MUST

#3 PATCH .trellis/spec/guides/testing.md
   位置: ## 边界值 节
   增量: + 并发任务必须含 ≥ 1 stress 测试 (并发数 ≥ 10, 持续 ≥ 5s)
   理由: 本任务无 stress 漏过 race condition

预计影响: 后续任务遇并发场景时按新规处理
```

## 与 optimize 模式的差异

| 维度 | optimize | sediment |
| --- | --- | --- |
| 触发 | 用户抱怨 / 主动重构 spec | 任务收尾自动或手动 |
| 阶段 1 诊断 | 必跑 (体检报告) | 跳过 |
| 阶段 2 输入 | 诊断结果 | 本任务学习 |
| 阶段 2 输出 | DELETE / REWRITE / MERGE 为主 | NEW / PATCH 为主 |
| 阶段 3 审批 | 同 | 同, 但风险通常低 (增量为主) |
| 阶段 4 执行 | 同 | 同 |

## journal 摘取要点

```bash
# 查 "踩坑" / "教训" / "反复" / "下次不能" / "没想到" 等关键词
grep -nE '踩坑|教训|反复|下次不能|没想到|漏了|忘了|又一次' .trellis/workspace/<dev>/journal-*.md

# 查带"!!" / "!!!" 标记的强调点
grep -nE '!{2,}' .trellis/workspace/<dev>/journal-*.md

# 查 "应该" / "本来应该" / "其实可以" 之类反思
grep -nE '本来应该|其实可以|早知道|要是当时' .trellis/workspace/<dev>/journal-*.md
```

提炼时:
- 同类教训合并为一条
- 单次偶发不沉淀
- 用户 / 团队个人偏好不沉淀 (那是 memory 的事, 不是 spec)

## 与 trellisx-orchestrate 联动

orchestrate Phase 3 收尾流程:

```
3.1 quality verification
3.2 debug retrospective (按需)
3.3 spec update ← 调用 trellisx-spec (sediment 模式)
3.4 commit
3.5 wrap-up
```

3.3 步触发本 skill (sediment 模式), **main 直接按 5 步流程执行** (诊断→提案→AskUserQuestion 审批→写盘→自检), 走 propose → approve → execute。**非 fork subagent** —— subagent 不能走 AskUserQuestion 审批门。

## 输出后跟进

execute 完成后:

- spec 改动随 task 收尾的 commit 一并提交 (用户决定)
- 受影响 task manifest 引用清单 → 用户决定是否在下次 task planning 时同步
- 若新增 NEW 文件, 提醒用户 "下次 planning 时考虑加进新 task 的 jsonl"
