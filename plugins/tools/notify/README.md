# Notify - 系统通知插件

> 通过系统通知向用户实时提示会话状态变更、权限请求等重要事件的 Claude Code 插件

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin notify@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install notify@ccplugin-market
```

## 功能特性

- 📢 **跨平台支持** - macOS、Linux (D-Bus)、Windows (Toast) 通知
- 🎙️ **语音播报** - 支持跨平台文本转语音（macOS/Linux/Windows）
- ⏱️ **会话统计** - Stop 事件时显示会话交互次数和时间戳
- 🎯 **智能通知** - 根据通知类型自动调整显示时间和格式
- ⚙️ **配置驱动** - YAML 配置文件灵活控制通知和语音行为
- 🔇 **无声集成** - Hook 错误处理，不中断主程序
- ⚡ **快速响应** - 使用 uvx 快速执行，无需预先安装

## Hook 事件

| Hook | 描述 |
|------|------|
| SessionStart | 会话开始，初始化配置 |
| SessionEnd | 会话结束，发送通知 |
| UserPromptSubmit | 用户提示提交，发送通知 |
| PreToolUse | 工具使用前，发送通知 |
| PostToolUse | 工具使用后，发送通知 |
| Notification | 系统通知事件（权限请求、空闲提示等） |
| Stop | 会话停止，显示统计 |
| SubagentStop | 子代理停止，发送通知 |

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

## 配置

配置文件位置：
- 用户级: `~/.lazygophers/ccplugin/notify/config.yaml`
- 项目级: `<project>/.lazygophers/ccplugin/notify/config.yaml`

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

  Notification:
    types:
      permission_prompt:
        notify: true
        voice: false
      idle_prompt:
        notify: true
        voice: false
```

## 故障排除

### macOS 未显示通知
- 检查系统通知设置中 Claude Code 的通知权限

### Linux 未显示通知
- 安装 libnotify: `sudo apt-get install libnotify-bin`

### Windows 未显示通知
- 确保 PowerShell 版本 3.0 或更高

## 许可证

AGPL-3.0-or-later
