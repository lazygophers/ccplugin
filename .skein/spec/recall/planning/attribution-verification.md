---
title: attribution-verification
category: planning
keywords: [归因,git blame,checker,结论先行,反面工程,lint,ruff,验证纪律]
status: active
inclusion: auto
---

## 结论要跑命令验证, 不能凭『印象/推理』下断言

### 触发场景
checker/审查类 agent 需要对「本次改动是否引入新问题」下结论（如 lint 违规数、覆盖率变化）。

### 陷阱-正解
**陷阱**：凭对代码的整体印象或先有结论再找证据的方式判断（如「本 task 应该没有新增 lint 违规」），未实际跑校验命令。曾有 checker 报告「零新增 ruff 违反」，事后实跑发现 14 条 errors，逐条 `git blame` 才确认其中 2 条确系本 task 引入；checker 自陈其推理方式是「先有结论再填证据的反面工程」。
**正解**：涉及「是否新增/引入」类结论，一律先跑实际命令拿到当下数字，再用 `git blame`/`git log -p` 对每条差异做归因，而非凭代码阅读印象下结论。
