---
title: flow
category: flow
keywords: [flow,strict,exec,四阶段,confirm,claim,check]
status: active
inclusion: auto
---

## skein 流程严格执行

## 流程严格执行四阶段约束

### plan 章节约束
- create 后必须按顺序完成：PRD → subtask → estimate → confirm
- 禁跳过 confirm 直接进入 claim
- 禁 claim 前不写 PRD/subtask

### exec 章节约束  
- claim 到 subtask 后必须立即 Agent(skein-executor) 派发
- 禁在 main 手动处理 subtask 的代码实现
- agent 返回 done/fail 后才继续下一条 subtask

### check 章节约束
- 全 subtask done 后必须立即 claim check
- 禁停在 exec 状态直接 claim finish
- check 必须跑完 lint/type-check/tests/契约合规
