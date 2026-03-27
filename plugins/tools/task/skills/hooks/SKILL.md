---
name: hooks
description: Task插件Hook系统 - 2个官方生命周期钩子（SessionStart, SessionEnd）
---

# Hooks - 生命周期钩子系统

Task插件提供2个官方hooks用于会话级事件处理。内部生命周期事件(任务启动/完成/迭代)通过Agent内部逻辑处理，不使用hooks系统。

## 可用Hooks

### SessionStart

触发：会话启动/恢复时。用途：初始化环境变量/加载配置/设置资源。

```json
{"SessionStart": [{"hooks": [{"type": "command", "command": "echo 'export ...' >> \"$CLAUDE_ENV_FILE\"", "async": true}]}]}
```

### SessionEnd

触发：会话结束时。环境变量：`SESSION_ID`。用途：清理临时文件/归档日志/生成报告。

日志：`.claude/logs/task-hooks-{session_id}.jsonl`

## 迁移说明(v0.0.184)

移除6个不受官方支持的hooks(TaskStart/IterationStart/IterationEnd/TaskComplete/TaskFailed/CheckpointSave)。替代方案：

| 原Hook | 新方案 |
|--------|--------|
| TaskStart | Loop skill输出`[MindFlow] 任务启动` |
| IterationStart/End | Loop skill迭代日志 |
| TaskComplete | Finalizer生成报告 |
| TaskFailed | Adjuster记录失败 |
| IterationEnd(指标) | Observability skill |
| CheckpointSave | Checkpoint skill日志 |

## Hook开发指南

- 输入：环境变量(SESSION_ID等) + stdin JSON
- 输出：stdout日志 | stderr错误 | exit 0=成功, 2=阻塞, 其他=非阻塞
- 最佳实践：<1秒执行 | async:true | 健壮错误处理 | 幂等 | 超时默认600s

## 故障排查

未触发：检查hook名在官方列表/plugin.json配置/脚本可执行/路径正确。失败：检查语法/环境变量/stderr/超时/权限。
