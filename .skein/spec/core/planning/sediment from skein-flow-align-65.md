---
title: skein-check 两步法（checkpoint + 场景自适应）
layer: core
category: planning
keywords: [check,验收,checkpoint,场景自适应,编程任务,文案任务]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822942
status: active
related: []
updated: 1784822942
---

## 铁律

- MUST：skein-check 阶段分两步法：①checkpoint 核对 ②场景自适应内置 check
- MUST：step1（checkpoint 核对）= 逐条核对 task+subtask 的 `--check 项`，标记完成
- MUST：step2（场景自适应 check）= 根据 task 类型执行内置校验：
  - 编程 task → build/test/lint/type/架构一致性
  - 小说/文案 task → 逻辑/设定/伏笔一致性
  - 其他 task → domain-specific checks
- MUST：两步都通过才能进 finish 阶段

## 反例表
| 禁 | 改为 |
|---|---|
| check 阶段只核对 checkpoint，不做质量检查 | 加 step2 场景自适应 check |
| 所有 task 用同一套 check 标准 | 按类型自适应检查规则 |
| 质量检查分散在 exec 阶段 | 集中在 check 阶段两步法处理 |

## 触发场景
- task 进入 check 阶段
- skein-check skill 改进
- 验收标准明确化

## 关联
- 铁律: exec 阶段无验收勾选
- 铁律: task 状态流转规则
- 铁律: skein-finish 四步序
