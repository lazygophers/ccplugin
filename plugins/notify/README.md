# Notify - 系统通知插件

通过系统通知向用户实时提示会话状态变更、权限请求等重要事件的 Claude Code 插件。

## 特性

- 📢 **跨平台支持** - macOS、Linux (D-Bus)、Windows (Toast) 通知
- 🎙️ **语音播报** - 支持跨平台文本转语音（macOS/Linux/Windows）
- ⏱️ **会话统计** - Stop 事件时显示会话交互次数和时间戳
- 🎯 **智能通知** - 根据通知类型自动调整显示时间和格式
- ⚙️ **配置驱动** - YAML 配置文件灵活控制通知和语音行为
- 🔇 **无声集成** - Hook 错误处理，不中断主程序
- ⚡ **快速响应** - 使用 uvx 快速执行，无需预先安装

## 工作原理

### Hook 事件

#### 1. SessionStart Hook
在会话开始时触发，初始化通知和语音配置：
- 在用户目录创建配置文件: `~/.lazygophers/ccplugin/notify/config.yaml`
- 在项目目录创建配置文件: `<project>/.lazygophers/ccplugin/notify/config.yaml`
- 跳过已存在的配置文件

#### 2. PreToolUse Hook
在工具使用前触发，根据配置决定是否发送通知：
- 支持的工具: Task、Bash、Edit、Write
- 检查配置中的 notify 和 voice 设置
- 可选的语音播报提示

#### 3. PostToolUse Hook
在工具使用后触发，发送工具执行完成通知：
- 支持的工具: Task、Bash、Edit、Write
- 显示工具执行状态（成功/失败）
- 可选的语音播报确认

#### 4. Stop Hook
在会话结束时触发，发送会话统计通知：
- **标题**: "Claude Code 会话已结束"
- **内容**: 会话时间戳和交互轮次数
- **示例**: "[10:30:45] 本次会话共有 15 轮交互"

#### 5. Notification Hook
处理 Claude Code 的各类通知事件：
- `permission_prompt` - 权限请求 (8秒)
- `warning` - 警告信息 (6秒)
- `info` - 常规提示 (4秒)
- `error` - 错误信息 (6秒)
- 支持条件化语音播报

### 跨平台实现

#### 系统通知
| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | osascript | 内置 |
| Linux | notify-send | 需安装 libnotify |
| Windows | PowerShell Toast | PowerShell 3.0+ |

#### 语音播报
| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | say 命令 | 内置 |
| Linux | espeak/festival | 需安装（参考 VOICE_SUPPORT.md） |
| Windows | PowerShell Speech API | .NET Framework（通常预装） |

详细的平台特定配置和故障排除，请参考 [VOICE_SUPPORT.md](../../VOICE_SUPPORT.md)。

## 安装

该插件自动随 ccplugin 项目一起安装。

### 启用插件

```bash
# 如果插件未自动启用，在 Claude Code 设置中手动启用 notify 插件
```

## 使用

### 自动模式

插件自动监听系统事件，无需手动操作。

### 手动测试

可以直接使用 `notify.py` 脚本进行测试：

```bash
# 发送简单通知
uv run plugins/notify/scripts/notify.py '任务完成'

# 发送通知并指定标题
uv run plugins/notify/scripts/notify.py '任务完成' '完成'

# 发送通知并指定超时时间
uv run plugins/notify/scripts/notify.py '任务完成' '完成' 8000

# 发送通知并播放语音
uv run plugins/notify/scripts/notify.py '任务完成' '完成' 8000 --voice

# 仅播放语音，不显示通知
uv run plugins/notify/scripts/notify.py '任务完成' --voice-only

# 初始化配置文件
uv run plugins/notify/scripts/notify.py --mode init -v

# 启动 MCP 服务器
uv run plugins/notify/scripts/notify.py --mode mcp

# 显示帮助信息
uv run plugins/notify/scripts/notify.py -h
```

### 查看通知

- **macOS**: 检查通知中心
- **Linux**: 查看桌面通知
- **Windows**: 检查操作中心

### 语音播报

详细的语音播报配置、故障排除和平台特定信息，请参考 [VOICE_SUPPORT.md](../../VOICE_SUPPORT.md)。

## 配置

### 配置文件

通知和语音行为由 YAML 配置文件控制，存储在两个位置（优先级：项目级 > 用户级）：
- **用户级**: `~/.lazygophers/ccplugin/notify/config.yaml`
- **项目级**: `<project>/.lazygophers/ccplugin/notify/config.yaml`

配置会在 SessionStart hook 时自动初始化。

### 配置示例

```yaml
events:
  PreToolUse:
    description: "工具使用前的通知"
    tools:
      Task:
        notify: true
        voice: false
      Bash:
        notify: true
        voice: false
      Edit:
        notify: true
        voice: false

  PostToolUse:
    description: "工具使用后的通知"
    tools:
      Task:
        notify: true
        voice: false
      Bash:
        notify: true
        voice: false

  Notification:
    description: "系统通知事件"
    types:
      permission_prompt:
        notify: true
        voice: false
      idle_prompt:
        notify: true
        voice: false
```

### 目录结构

```
plugins/notify/
├── scripts/
│   ├── __init__.py                # Python 包初始化
│   ├── notify.py                  # 主 CLI 脚本
│   ├── pretooluse_hook.py         # PreToolUse hook 处理脚本
│   ├── posttooluse_hook.py        # PostToolUse hook 处理脚本
│   ├── notification_hook.py       # Notification hook 处理脚本
│   └── stop_hook.py               # Stop hook 处理脚本
├── hooks/
│   └── hooks.json                 # Hook 事件配置
├── .claude-plugin/
│   └── plugin.json                # 插件元数据
├── README.md                      # 本文件
└── VOICE_SUPPORT.md               # 语音播报支持文档（项目根目录）
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
# 测试 SessionStart hook（初始化配置）
uv run plugins/notify/scripts/notify.py --mode init -v

# 测试 PreToolUse hook
echo '{"tool_name":"Task","hook_event_name":"PreToolUse"}' | uv run plugins/notify/scripts/pretooluse_hook.py

# 测试 PostToolUse hook
echo '{"tool_name":"Bash","hook_event_name":"PostToolUse","success":true}' | uv run plugins/notify/scripts/posttooluse_hook.py

# 测试 Notification hook
echo '{"session_id":"test123","message":"测试权限请求","notification_type":"permission_prompt","cwd":"/tmp"}' | uv run plugins/notify/scripts/notification_hook.py

# 测试 Stop hook
echo '{"session_id":"test123","transcript_path":"~/.claude/projects/test.jsonl","hook_event_name":"Stop"}' | uv run plugins/notify/scripts/stop_hook.py

# 测试通知脚本的语音功能
uv run plugins/notify/scripts/notify.py '测试' --voice-only
uv run plugins/notify/scripts/notify.py '测试通知' '测试' 5000 --voice
```

### 修改配置

编辑配置文件以改变通知和语音行为：
- 用户配置: `~/.lazygophers/ccplugin/notify/config.yaml`
- 项目配置: `<project>/.lazygophers/ccplugin/notify/config.yaml`

修改 `notify` 和 `voice` 字段来控制每个工具和事件类型的行为。

### 添加新的事件类型

1. 编辑配置文件模板 `lib/notify/init_config.py` 中的 `DEFAULT_CONFIG_TEMPLATE`
2. 在 hook 处理器中添加相应的事件处理逻辑
3. 更新 `plugins/notify/hooks/hooks.json` 以注册新的 hook

### 语音功能开发

跨平台的语音播报实现在 `lib/notify/notifier.py` 中：
- `_speak_macos()` - macOS 实现（使用 `say` 命令）
- `_speak_linux()` - Linux 实现（使用 espeak 或 festival）
- `_speak_windows()` - Windows 实现（使用 PowerShell Speech API）

详见 [VOICE_SUPPORT.md](../../VOICE_SUPPORT.md) 了解平台特定的实现细节。

## 许可证

AGPL-3.0-or-later
