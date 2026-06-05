# Notify - Claude Code Hooks 通知插件

> 通过系统通知和 TTS 语音实时提示会话状态变更、权限请求等重要事件

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin notify@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install notify@ccplugin-market
```

## 功能特性

- **全事件覆盖** - 支持全部 29 个 Claude Code 官方 Hook 事件
- **跨平台通知** - macOS (Swift/AppKit overlay)、Linux/Windows (Tk overlay)
- **语音播报** - 跨平台 TTS（macOS say / Linux espeak / Windows PowerShell）
- **Python 配置驱动** - 默认配置在 `scripts/config.py`，支持 YAML 覆盖
- **模板消息** - Jinja2 风格模板语法，支持变量替换

## 默认启用的 Hook

| Hook | 描述 |
|------|------|
| `stop` | 任务完成 |
| `stop_failure` | API 错误 |
| `permission_request` | 权限请求 |
| `pre_tool_use.askuserquestion` | 用户提问 |
| `notification.permission_prompt` | 权限提示通知 |

## 配置

配置仅支持加载，禁止写入。默认配置在 `scripts/config.py`。

用户可在以下位置覆盖：
- 用户级: `~/.lazygophers/ccplugin/notify/config.yaml`
- 项目级: `<project>/.lazygophers/ccplugin/notify/config.yaml`

详见 [配置指南](docs/configuration.md)。

## 架构

```
plugin.json (Hook 注册)
  └─ scripts/main.py hooks
      └─ scripts/config.py (默认配置)
          └─ scripts/notify.py
              ├─ TTS: macOS say / Linux espeak / Windows PowerShell
              └─ Notification: Swift overlay (macOS) / Tk (Linux/Win)
```

## 文档

- [概述](docs/index.md)
- [Hook 事件](docs/hooks.md)
- [配置指南](docs/configuration.md)
- [故障排除](docs/troubleshooting.md)

## 许可证

AGPL-3.0-or-later