---
description: 用户取消，处理取消请求并清理资源
memory: project
color: red
model: sonnet
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:cancel
---

# Cancel Skill

## Process

1. 确认用户取消意图
2. 停止当前任务
3. 保存部分进度（如有）
4. 清理临时文件
5. 清理检查点
6. 更新任务状态
7. 生成取消报告
8. 通知用户

## Output

- 取消报告
- 保存的进度（如有）
- 清理确认
