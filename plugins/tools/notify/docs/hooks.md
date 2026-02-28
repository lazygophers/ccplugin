# Hook 事件

Notify 插件支持的 Hook 事件。

## 事件列表

| 事件 | 触发时机 | 通知类型 |
|------|----------|----------|
| `SessionStart` | 会话开始 | 初始化通知 |
| `SessionEnd` | 会话结束 | 结束通知 |
| `UserPromptSubmit` | 用户提交提示 | 提交通知 |
| `PreToolUse` | 工具使用前 | 工具通知 |
| `PostToolUse` | 工具使用后 | 完成通知 |
| `Notification` | 系统通知事件 | 权限/空闲通知 |
| `Stop` | 会话停止 | 统计通知 |
| `SubagentStop` | 子代理停止 | 代理通知 |

## 事件详情

### SessionStart

会话开始时触发，初始化配置。

```yaml
events:
  SessionStart:
    notify: true
    voice: false
```

### SessionEnd

会话结束时触发，发送结束通知。

```yaml
events:
  SessionEnd:
    notify: true
    voice: true
```

### UserPromptSubmit

用户提交提示时触发。

```yaml
events:
  UserPromptSubmit:
    notify: true
    voice: false
```

### PreToolUse

工具使用前触发，支持按工具过滤。

```yaml
events:
  PreToolUse:
    tools:
      Task:
        notify: true
        voice: false
      Bash:
        notify: true
        voice: false
```

### PostToolUse

工具使用后触发。

```yaml
events:
  PostToolUse:
    tools:
      Task:
        notify: true
        voice: true
```

### Notification

系统通知事件，包括权限请求和空闲提示。

```yaml
events:
  Notification:
    types:
      permission_prompt:
        notify: true
        voice: true
      idle_prompt:
        notify: true
        voice: false
```

### Stop

会话停止时触发，显示统计信息。

```yaml
events:
  Stop:
    notify: true
    voice: false
    stats: true
```

### SubagentStop

子代理停止时触发。

```yaml
events:
  SubagentStop:
    notify: true
    voice: false
```
