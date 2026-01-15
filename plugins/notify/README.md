# Notify - 系统通知插件

通过系统通知向用户实时提示会话状态变更、权限请求等重要事件的 Claude Code 插件。

## 特性

- 📢 **跨平台支持** - macOS、Linux (D-Bus)、Windows (Toast) 通知
- ⏱️ **会话统计** - Stop 事件时显示会话交互次数和时间戳
- 🎯 **智能通知** - 根据通知类型自动调整显示时间和格式
- 🔇 **无声集成** - Hook 错误处理，不中断主程序
- ⚡ **快速响应** - 使用 uvx 快速执行，无需预先安装

## 工作原理

### Hook 事件

#### 1. Stop Hook
在会话结束时触发，发送会话统计通知：
- **标题**: "Claude Code 会话已结束"
- **内容**: 会话时间戳和交互轮次数
- **示例**: "[10:30:45] 本次会话共有 15 轮交互"

#### 2. Notification Hook
处理 Claude Code 的各类通知事件：
- `permission_prompt` - 权限请求 (8秒)
- `warning` - 警告信息 (6秒)
- `info` - 常规提示 (4秒)
- `error` - 错误信息 (6秒)

### 跨平台实现

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | osascript | 内置 |
| Linux | notify-send | 需安装 libnotify |
| Windows | PowerShell Toast | PowerShell 3.0+ |

## 安装

该插件自动随 ccplugin 项目一起安装。

### 启用插件

```bash
# 如果插件未自动启用，在 Claude Code 设置中手动启用 notify 插件
```

## 使用

插件自动监听系统事件，无需手动操作。

### 查看通知

- **macOS**: 检查通知中心
- **Linux**: 查看桌面通知
- **Windows**: 检查操作中心

## 配置

### 目录结构

```
plugins/notify/
├── scripts/
│   ├── __init__.py           # Python 包初始化
│   ├── notifier.py           # 跨平台通知核心实现
│   ├── stop_hook.py          # Stop hook 处理脚本
│   └── notification_hook.py  # Notification hook 处理脚本
├── hooks/
│   └── hooks.json            # Hook 配置
├── .claude-plugin/
│   └── plugin.json           # 插件元数据
└── README.md                 # 本文件
```

## 故障排除

### macOS 未显示通知
- 检查系统通知设置中 Claude Code 的通知权限
- 尝试在"系统设置 > 通知"中重新配置

### Linux 未显示通知
- 确保已安装 `libnotify-bin`: `sudo apt-get install libnotify-bin`
- 检查通知守护进程是否运行: `pgrep -f notification-daemon`

### Windows 未显示通知
- 确保 PowerShell 版本 3.0 或更高
- 检查是否禁用了应用通知

## 开发

### 运行测试

```bash
# 测试 Stop hook
echo '{"session_id":"test123","transcript_path":"~/.claude/projects/test.jsonl"}' | uv run plugins/notify/scripts/stop_hook.py

# 测试 Notification hook
echo '{"session_id":"test123","message":"测试权限请求","notification_type":"permission_prompt"}' | uv run plugins/notify/scripts/notification_hook.py
```

### 添加新的通知类型

编辑 `scripts/notification_hook.py` 的 `NOTIFICATION_TYPE_MAPPING` 字典：

```python
NOTIFICATION_TYPE_MAPPING = {
    "custom_type": {
        "title": "自定义标题",
        "icon": "🎯",
        "timeout": 5000,
    },
    # ...
}
```

## 许可证

AGPL-3.0-or-later
