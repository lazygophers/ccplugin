---
title: supertask-auto-check
category: flow
keywords: [supertask, child, 聚合, 自动推进, check, claim, 父任务, parent]
status: active
inclusion: auto
---

## supertask child 全 done 自动进 check

### 触发条件
- supertask 自身状态是 `active`（`scheduling.py:231` 只放行 `ACTIVE`/`CHECK`，且只有 `ACTIVE` 才进 to_check；`finishing`/`done` 不在候选内）
- 全部 child task 状态已变为 `done`（无 child 也不放行）
- 跑到一次 `skein claim`（转移由 claim 触发，不是后台轮询）

### 行为
当 supertask 的所有 child task 均已完成（done），flow 层在 `skein claim` 时自动将 supertask 推进入 `check` 阶段，等价于运行 `skein claim` 后 supertask 自动转移。

不需手动 `skein confirm` 或其他中间操作。该转移走 claim 状态机，遵循「状态先行硬门」铁律。

### 目标
减少用户手动干预步骤；supertask（通常是大功能组或里程碑）在组成的所有子任务完毕后立即推进检查，提升流程自动化程度。

### 实现细节
- 参考提交：18d9d3972 "fix(skein): supertask child 全 done 后自动进 check"
- 修改文件：plugins/tools/skein/scripts/skeinlib/scheduling.py
- 测试覆盖：plugins/tools/skein/scripts/tests/test_supertask.py

### 关联规则
`plugins/tools/skein/skills/skein-flow/references/flow-loop.md` — §2 状态先行硬门 / §3 主循环骨架。
写成路径而非 wikilink: flow-loop 是仓库 skill 文档, spec 库无同名条目, wikilink 解析不到。
