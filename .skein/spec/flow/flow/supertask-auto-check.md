---
title: supertask-auto-check
category: flow
keywords: []
status: active
inclusion: auto
---

## supertask child 全 done 自动进 check

## supertask child 全 done 自动进 check

### 触发条件
- supertask 在 `active` 或更晚阶段（check/finishing/done）
- 全部 child task 状态已变为 `done`
- flow 主循环扫描状态发现转移条件满足

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
[[flow/flow-loop.md#状态先行硬门]]
[[flow/flow-loop.md#主循环骨架]]
