# 语音播报多平台支持文档

## 概述

notify插件支持跨平台的语音播报功能，在macOS、Linux和Windows上都能正常工作。

## 功能特性

- ✅ **系统通知** - 跨平台系统通知支持
- ✅ **语音播报** - 跨平台文本转语音支持
- ✅ **参数组合** - `--voice` 和 `--voice-only` 参数
- ✅ **配置驱动** - 根据YAML配置动态控制行为

## 平台支持详情

### macOS

**系统要求:**
- macOS 10.5+（内置 Notification Center）
- 内置 `say` 命令用于语音播报

**通知方式:** 系统通知中心
**语音方式:** `say` 命令

**测试命令:**
```bash
# 发送通知
uv run plugins/notify/scripts/notify.py '任务完成' '完成'

# 语音播报
uv run plugins/notify/scripts/notify.py '任务完成' --voice-only

# 同时通知和语音
uv run plugins/notify/scripts/notify.py '任务完成' '完成' 5000 --voice
```

**支持情况:** ✅ 完全支持

---

### Linux

**系统要求:**

#### DBus通知:
- 需要 `notify-send` 命令（大多数Linux发行版已预装）
- D-Bus 服务（通常已启用）

**安装方式:**
```bash
# Ubuntu/Debian
sudo apt-get install libnotify-bin espeak

# Fedora
sudo dnf install libnotify espeak

# Arch
sudo pacman -S libnotify espeak
```

#### 语音播报:
- 优先使用 `espeak`（推荐）
- 备选 `festival`

**配置 espeak:**
```bash
# 检查是否安装
which espeak

# 安装espeak
sudo apt-get install espeak  # Ubuntu/Debian
sudo dnf install espeak      # Fedora
sudo pacman -S espeak        # Arch
```

**配置 festival (备选):**
```bash
# 安装festival
sudo apt-get install festival   # Ubuntu/Debian
sudo dnf install festival       # Fedora
sudo pacman -S festival         # Arch
```

**测试命令:**
```bash
# 测试DBus通知
notify-send "测试" "通知正常"

# 测试espeak
espeak "测试语音"

# 使用notify脚本
uv run plugins/notify/scripts/notify.py '任务完成' --voice-only
```

**支持情况:** ✅ 完全支持（需安装依赖）

---

### Windows

**系统要求:**
- Windows 7+
- PowerShell（通常已预装）
- .NET Framework（通常已预装）

**通知方式:** Toast通知
**语音方式:** PowerShell Speech API

**依赖情况:**
- ✅ 内置支持，无需额外安装

**测试命令:**
```powershell
# PowerShell中测试
uv run plugins/notify/scripts/notify.py "任务完成" "完成" 5000 --voice
uv run plugins/notify/scripts/notify.py "任务完成" --voice-only
```

**支持情况:** ✅ 完全支持（无需额外配置）

---

## 使用指南

### 基本使用

```bash
# 仅发送通知（无语音）
uv run plugins/notify/scripts/notify.py '消息内容' '标题' 5000

# 发送通知并语音播报
uv run plugins/notify/scripts/notify.py '消息内容' '标题' 5000 --voice

# 仅语音播报（不显示通知）
uv run plugins/notify/scripts/notify.py '消息内容' --voice-only
```

### 高级用法

**与hooks集成:**
```json
{
  "PreToolUse": {
    "Task": { "notify": true, "voice": false },
    "Edit": { "notify": true, "voice": false }
  }
}
```

**在脚本中使用:**
```python
from lib.notify import notify, speak

# 发送通知
notify("标题", "消息", 5000)

# 语音播报
speak("播报内容")
```

## 故障排除

### macOS

**问题:** 语音播报无声音
- 检查系统音量是否已调高
- 验证 `say` 命令可用: `which say`
- 手动测试: `say "test"`

### Linux

**问题:** notify-send 不工作
```bash
# 检查D-Bus
ps aux | grep dbus

# 检查notify-send
which notify-send
which espeak
```

**问题:** espeak/festival 无声音
```bash
# 检查音频设备
aplay -l  # ALSA设备
pactl list short sinks  # PulseAudio设备

# 检查espeak是否可执行
espeak "test"
```

### Windows

**问题:** PowerShell Speech 不工作
```powershell
# 验证Speech API可用
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Speak("test")
```

**问题:** Toast通知不显示
- 检查Windows通知设置
- 验证PowerShell版本（5.1+推荐）
- 尝试以管理员身份运行

## 性能指标

| 功能 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 系统通知 | ✅ 快速 | ✅ 快速 | ✅ 快速 |
| 语音播报 | ✅ 3-5s | ✅ 2-4s | ✅ 2-4s |
| 超时处理 | ✅ 30s | ✅ 30s | ✅ 30s |
| 并发支持 | ✅ 是 | ✅ 是 | ✅ 是 |

## 最佳实践

1. **优先组合:** 建议同时使用通知和语音（--voice），便于用户感知
2. **文本长度:** 保持播报文本在50字以内，效果最佳
3. **声音音量:** 确保系统音量在50%以上
4. **测试:** 在生产前在目标平台测试语音功能

## 已知限制

- **Linux:** 需要手动安装espeak/festival
- **多语言:** macOS和Windows支持中文，Linux需配置
- **速度:** 长文本可能需要较长时间播报（最长30秒超时）

## 相关命令

```bash
# 查看帮助
uv run plugins/notify/scripts/notify.py -h

# 初始化配置
uv run plugins/notify/scripts/notify.py --mode init

# 测试基本功能
uv run plugins/notify/scripts/notify.py '测试通知'
uv run plugins/notify/scripts/notify.py '测试语音' --voice-only
```

## 贡献和反馈

如遇到平台特定问题，请提交Issue或PR！
