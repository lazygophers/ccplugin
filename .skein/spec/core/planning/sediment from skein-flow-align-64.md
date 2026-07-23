---
title: task 状态流转规则（单 task 全 done → check）
layer: core
category: planning
keywords: [task,状态机,done,check,状态转移,多task协调]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822937
status: active
related: []
updated: 1784822937
---

## 铁律

- MUST：单个 task 中所有 subtask 状态为 done → 该 task 自动进 check 阶段
- MUST：多 task 场景下，全部 task 都完成才标记 exec 暂停（等待用户启动下一 task）
- MUST：task 进 check 不需等待同批其他 task 完成（每个 task 独立流转）
- MUST：exec → check 的状态转移必须在 skein.py 中明确处理（非隐式逻辑）

## 反例表
| 禁 | 改为 |
|---|---|
| 等所有 task 完成才进 check | 单 task 全 subtask done 立即进 check |
| task 之间相互阻塞等待 | 各 task 独立流转，无依赖则并行进 check |
| exec 无明确状态转移逻辑 | skein.py 明确处理 done→check 转移 |

## 触发场景
- task 中最后一个 subtask 完成时
- 多 task workflow 中的状态协调
- exec 到 check 的自动流转

## 关联
- 铁律: exec 阶段无验收勾选
- 铁律: skein-check 两步法
- 铁律: skein-finish 四步序
