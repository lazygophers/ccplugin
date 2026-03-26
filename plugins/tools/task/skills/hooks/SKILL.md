---
name: hooks
description: Task插件Hook系统 - 2个官方支持的生命周期钩子（SessionStart, SessionEnd）用于会话级事件处理
---

# Hooks - 生命周期钩子系统

<overview>

Task插件提供2个官方支持的生命周期hooks，用于会话级事件处理。

**可用Hooks**：
- SessionStart - 会话启动时执行
- SessionEnd - 会话结束时执行

**用途**：
- 环境初始化（SessionStart）
- 会话清理和日志归档（SessionEnd）

**重要说明**：
Task的内部生命周期事件（任务启动/完成、迭代等）通过Agent内部逻辑处理，不使用hooks系统。这是因为Claude Code的hook系统只支持会话/工具/子代理级别的事件，不支持自定义task生命周期事件。

</overview>

## 可用Hooks

### SessionStart

**触发时机**：会话启动或恢复时

**当前用途**：设置环境变量

**配置**：
```json
{
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0' >> \"$CLAUDE_ENV_FILE\"",
          "async": true
        }
      ]
    }
  ]
}
```

**用途示例**：
- 初始化环境变量
- 加载项目配置
- 设置会话级资源
- 发送会话启动通知

---

### SessionEnd

**触发时机**：会话结束时

**环境变量**：
- `SESSION_ID` - 会话ID

**当前实现**：
```javascript
// session-end.js
const sessionId = process.env.SESSION_ID || 'unknown';
const logEntry = {
  hook: 'SessionEnd',
  session_id: sessionId,
  timestamp: new Date().toISOString()
};

// 保存到hook日志
const logDir = path.join(process.env.HOME, '.claude/logs');
const logPath = path.join(logDir, `task-hooks-${sessionId}.jsonl`);
fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n', 'utf8');

console.log(`[Hook:SessionEnd] 会话结束: ${sessionId}`);
```

**用途示例**：
- 清理临时文件
- 归档会话日志
- 生成会话报告
- 发送会话完成通知

---

## 迁移说明（v0.0.184）

### 变更概述

v0.0.184 移除了6个不受Claude Code官方支持的自定义hooks：
- TaskStart
- IterationStart
- IterationEnd
- TaskComplete
- TaskFailed
- CheckpointSave

### 移除原因

这些hooks不在Claude Code官方支持列表中，因此永远不会被触发。Claude Code的hook系统仅支持以下事件：

SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, Notification, SubagentStart, SubagentStop, Stop, StopFailure, TeammateIdle, TaskCompleted, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, Elicitation, ElicitationResult, SessionEnd

### 迁移路径

如果您需要类似的生命周期事件处理，请使用以下方案：

#### 任务启动日志 (TaskStart)
- **原方案**：TaskStart hook
- **新方案**：在Loop skill或Planner agent中通过SendMessage输出
- **示例**：Loop初始化阶段输出`[MindFlow] 任务启动: ${taskId}`

#### 迭代追踪 (IterationStart/IterationEnd)
- **原方案**：IterationStart/IterationEnd hooks
- **新方案**：在Loop skill的迭代开始/结束时输出日志
- **示例**：`[MindFlow·${task}·${phase}/${iteration}·${status}]`

#### 任务完成记录 (TaskComplete)
- **原方案**：TaskComplete hook
- **新方案**：在Finalizer agent中保存任务历史
- **示例**：Finalizer生成完成报告并保存到`.claude/task-history/`

#### 失败记录 (TaskFailed)
- **原方案**：TaskFailed hook
- **新方案**：在Adjuster agent中记录失败信息
- **示例**：Adjuster保存失败记录到`.claude/task-failures/`

#### 指标收集 (IterationEnd)
- **原方案**：IterationEnd hook收集指标
- **新方案**：使用Observability skill或在Verifier/Finalizer中收集
- **示例**：调用`task:observability`生成成本报告

#### 检查点保存 (CheckpointSave)
- **原方案**：CheckpointSave hook
- **新方案**：Checkpoint skill内部记录保存事件
- **示例**：`task:checkpoint`在保存时输出日志

---

## Hook配置

### 自定义Hook

虽然task插件只使用2个官方hooks，但您可以在项目的`.claude/settings.json`或`.claude/settings.local.json`中添加其他官方支持的hooks。

**示例：在工具使用后运行测试**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm test",
            "async": true,
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### 查看可用Hooks

在Claude Code中输入`/hooks`查看所有已配置的hooks。

---

## Hook开发指南

### 输入

**环境变量**：根据hook类型不同而变化
- SessionStart: `SESSION_ID`, `CLAUDE_ENV_FILE`, 等
- SessionEnd: `SESSION_ID`

**标准输入**：JSON格式的上下文数据（通过stdin传入）

### 输出

**标准输出**：日志消息（显示给用户）

**标准错误**：错误消息（调试用）

**Exit code**：
- `0` = 成功
- `2` = 阻塞错误（某些事件支持）
- 其他 = 非阻塞错误

### 最佳实践

1. **保持轻量**：执行时间<1秒，避免阻塞
2. **使用async**：对于非关键hooks使用`async: true`
3. **错误处理**：健壮的错误处理，不依赖外部服务
4. **日志清晰**：输出清晰的日志，便于调试
5. **幂等性**：Hook可能重复触发，确保幂等
6. **安全性**：验证和清理所有输入数据

### 超时保护

每个hook都有超时设置，默认为600秒。超时后hook会被终止，不影响主流程。

---

## Hook日志

SessionEnd hook的执行记录保存到：

`.claude/logs/task-hooks-{session_id}.jsonl`

**格式**：每行一个JSON对象

```json
{"hook": "SessionEnd", "session_id": "abc123", "timestamp": "2026-03-26T10:00:00Z"}
```

---

## 故障排查

### Hook未触发

1. 检查hook名称是否在官方支持列表中
2. 检查plugin.json配置是否正确
3. 检查脚本是否可执行（`chmod +x`）
4. 检查脚本路径中的`${CLAUDE_PLUGIN_ROOT}`是否正确
5. 查看hook日志：`.claude/logs/`

### Hook执行失败

1. 检查脚本语法错误（`node script.js`测试）
2. 检查环境变量是否正确传递
3. 查看stderr输出（使用`--verbose`模式）
4. 检查超时设置是否合理
5. 验证文件权限和路径

### Hook性能问题

1. 检查执行时间（使用`time`命令）
2. 优化脚本逻辑
3. 考虑使用`async: true`
4. 减少外部依赖
5. 避免同步I/O操作

---

## 参考资源

- [Claude Code官方Hooks文档](https://code.claude.com/docs/hooks)
- [Task插件完整文档](../../README.md)
- [Loop Skill文档](../loop/SKILL.md)
- [Checkpoint Skill文档](../checkpoint/SKILL.md)
- [Observability Skill文档](../observability/SKILL.md)
