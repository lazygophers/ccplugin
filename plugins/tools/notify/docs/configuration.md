# 配置指南

Notify 插件配置。

## 配置文件位置

- 用户级: `~/.lazygophers/ccplugin/notify/config.yaml`
- 项目级: `<project>/.lazygophers/ccplugin/notify/config.yaml`

**只读配置**：插件配置仅支持加载，禁止写入。默认配置在 `scripts/config.py` 中定义。

## 配置选项

### 通用字段

| 字段 | 类型 | 默认 | 描述 |
|------|------|------|------|
| `enabled` | bool | false | 是否发送系统通知 |
| `play_sound` | bool | false | 是否语音播报 |
| `message` | string | - | 消息模板 |

### 配置合并

用户配置文件会与默认配置合并，未指定的字段继承默认值。

## 覆盖示例

只覆盖 `stop` 的消息，不改 enabled/play_sound：

```yaml
hooks:
  stop:
    message: "自定义消息: {{ project_name }}"
```

## 默认启用的事件

| Hook | enabled | play_sound | message |
|------|---------|------------|---------|
| `stop` | ✓ | ✓ | `{{ project_name }} 任务已完成` |
| `stop_failure` | ✓ | ✓ | `{{ project_name }} API 错误: {{ error }}` |
| `permission_request` | ✓ | ✓ | `{{ project_name }} 请求权限 ({{ tool_name }})` |
| `pre_tool_use.askuserquestion` | ✓ | ✓ | `{{ project_name }} 有问题需要你解决` |
| `notification.permission_prompt` | ✓ | ✓ | `权限请求: {{ message }}` |

其他所有 hook 默认关闭，message 始终有默认值。

## 完整配置示例

```yaml
hooks:
  stop:
    enabled: true
    play_sound: true
    message: "{{ project_name }} 任务完成"

  stop_failure:
    enabled: true
    play_sound: true
    message: "{{ project_name }} API 错误: {{ error }}"

  permission_request:
    enabled: true
    play_sound: true

  pre_tool_use:
    askuserquestion:
      enabled: true
      play_sound: true
      message: "{{ project_name }} 需要你回答问题"

  notification:
    permission_prompt:
      enabled: true
      play_sound: true
```

## 跨平台支持

### 系统通知

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | Swift/AppKit 无焦点浮层 | Xcode CLT |
| Linux | Tkinter 浮层 | python3-tk |
| Windows | Tkinter 浮层 | python3-tk |

### 语音播报

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | say 命令 | 内置 |
| Linux | espeak | 需安装 |
| Windows | PowerShell Speech API | .NET Framework |