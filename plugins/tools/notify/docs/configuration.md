# 配置指南

Notify 插件的配置选项。

## 配置文件

### 文件位置

- 用户级: `~/.lazygophers/ccplugin/notify/config.yaml`
- 项目级: `<project>/.lazygophers/ccplugin/notify/config.yaml`

### 配置示例

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

  PostToolUse:
    tools:
      Task:
        notify: true
        voice: true

  Notification:
    types:
      permission_prompt:
        notify: true
        voice: true
      idle_prompt:
        notify: true
        voice: false

  Stop:
    notify: true
    voice: false
    stats: true
```

## 配置选项

### 通知选项

| 选项 | 类型 | 描述 |
|------|------|------|
| `notify` | boolean | 是否发送系统通知 |
| `voice` | boolean | 是否语音播报 |
| `stats` | boolean | 是否显示统计信息 |

### 工具过滤

```yaml
events:
  PreToolUse:
    tools:
      Task:        # 仅对 Task 工具
        notify: true
      Bash:        # 仅对 Bash 工具
        notify: true
```

### 通知类型过滤

```yaml
events:
  Notification:
    types:
      permission_prompt:  # 权限请求
        notify: true
        voice: true
      idle_prompt:        # 空闲提示
        notify: true
        voice: false
```

## 跨平台支持

### 系统通知

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | terminal-notifier / osascript | terminal-notifier 需安装 |
| Linux | notify-send | libnotify |
| Windows | PowerShell Toast | PowerShell 3.0+ |

### 语音播报

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | say 命令 | 内置 |
| Linux | espeak/festival | 需安装 |
| Windows | PowerShell Speech API | .NET Framework |
