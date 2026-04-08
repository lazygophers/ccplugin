---
description: 调整修正，分析失败原因并制定修正策略
memory: project
color: yellow
model: sonnet
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:adjust
---

# Adjust Skill

## Process

1. 分析失败根本原因
2. 分类失败类型
3. 上下文缺失 → 指引 explore
4. 需求偏差 → 指引 align
5. 其他原因 → 指引 plan
6. 制定修正策略
7. 评估修正可行性
8. 不可行时建议放弃

## Output

- 失败原因分析
- 失败类型分类
- 修正策略
- 后续流向决策
