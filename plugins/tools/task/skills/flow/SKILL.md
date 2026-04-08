---
description: 任务流程，协调任务在各状态间的流转和调度
memory: project
color: purple
model: opus
permissionMode: plan
background: false
---

# Flow Skill

## Overview

任务流程技能，协调任务在各状态间的流转。根据状态转换图调度相应的 skill 执行任务。

## State Flow

```
[*] → pending → explore → align → plan → exec → verify → adjust → (explore | align | plan | done)
                                        ↑              ↓
                                        └──────────────┘
new_input → align
user_cancel → cancel → done
```

## Process

### 1. 初始化 (pending)

- 创建任务索引记录
- 设置初始状态为 pending
- 触发进入 explore

### 2. 现状探索 (explore)

- 调用 explore skill 收集上下文
- 完成后进入 align

### 3. 范围对齐 (align)

- 调用 align skill 与用户确认
- 用户确认后进入 plan
- 新输入可从任意状态进入 align

### 4. 任务规划 (plan)

- 调用 plan skill 制定执行方案
- 规划确认后进入 exec
- 上下文缺失可返回 explore

### 5. 任务执行 (exec)

- 按计划执行子任务
- 处理自我修复和重试
- 执行完成进入 verify

### 6. 结果校验 (verify)

- 调用 verify skill 验证结果
- 通过进入 done
- 失败进入 adjust

### 7. 调整修正 (adjust)

- 分析失败原因
- 上下文缺失 → explore
- 需求偏差 → align
- 其他原因 → plan
- 放弃 → done

### 8. 终结 (done)

- 调用 done skill 清理资源
- 归档任务记录

## State Transitions

| 当前状态 | 触发事件 | 下一状态 | 调用的 Skill |
|---------|---------|---------|-------------|
| pending | 初始化完成 | explore | pending |
| explore | 探索完成 | align | explore |
| align | 对齐确认 | plan | align |
| plan | 规划确认 | exec | plan |
| exec | 执行完成 | verify | exec |
| verify | 校验通过 | done | verify |
| verify | 校验失败 | adjust | verify |
| adjust | 上下文缺失 | explore | adjust |
| adjust | 需求偏差 | align | adjust |
| adjust | 其他原因 | plan | adjust |
| adjust | 放弃 | done | adjust |
| any | 用户取消 | cancel | cancel |

## Entry Points

- `[*] → pending`: 新建任务
- `new_input → align`: 用户新输入
- `user_cancel → cancel`: 用户取消

## Output

- 任务状态更新
- 状态转换记录
- 调用的 skill 结果
