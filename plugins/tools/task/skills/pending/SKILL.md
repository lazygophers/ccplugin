---
description: 任务初始化，处理任务创建和上下文准备
memory: project
color: cyan
model: sonnet
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:pending
---

# Pending Skill

## Process

1. 接收并解析用户任务描述
2. 提取关键信息：目标、约束、上下文
3. 检查任务描述完整性
4. 识别缺失信息并标记
5. 准备初始上下文
6. 确定任务优先级
7. 记录任务元数据

## Output

- 初始上下文摘要
- 缺失信息清单
- 任务优先级评估
