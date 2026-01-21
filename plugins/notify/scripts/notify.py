"""
通知和 TTS 功能模块

提供两个主要功能：
1. play_text_tts() - 通过 TTS 播放文本内容
2. show_system_notification() - 显示系统通知
"""

import subprocess
import sys
import platform
from pathlib import Path
from typing import Optional

# 设置 sys.path 以找到 lib 模块
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.logging import error, debug


def play_text_tts(text: str, rate: int = 200) -> bool:
    """通过 TTS 播放文本内容

    使用系统默认的 TTS 引擎（macOS 使用 say，Linux 使用 espeak）

    Args:
        text: 要播放的文本内容
        rate: 播放速率（字/分钟），仅对 macOS 有效，默认 200

    Returns:
        bool: 播放成功返回 True，失败返回 False

    示例:
        play_text_tts("Hello, World!")
        play_text_tts("操作已完成", rate=150)
    """
    if not text or not isinstance(text, str):
        error("文本内容不能为空且必须是字符串类型")
        return False

    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # 使用 macOS 的 say 命令
            cmd = ["say", "-r", str(rate), text]
            subprocess.run(cmd, check=True, capture_output=True)
            return True

        elif system == "Linux":
            # 使用 Linux 的 espeak 命令
            cmd = ["espeak", text]
            subprocess.run(cmd, check=True, capture_output=True)
            return True

        elif system == "Windows":
            # 使用 Windows 的 PowerShell TTS
            ps_cmd = f"""
            Add-Type -AssemblyName System.Speech
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $speak.Speak('{text}')
            """
            subprocess.run(
                ["powershell", "-Command", ps_cmd],
                check=True,
                capture_output=True
            )
            return True

        else:
            error(f"不支持的操作系统: {system}")
            return False

    except subprocess.CalledProcessError as e:
        error(f"TTS 播放失败: {e}")
        return False
    except FileNotFoundError as e:
        error(f"TTS 工具未找到（可能未安装）: {e}")
        return False
    except Exception as e:
        error(f"TTS 播放过程中发生异常: {e}")
        return False


def show_system_notification(
    message: str,
    title: str = "Claude Code",
    duration: int = 5000
) -> bool:
    """显示系统通知

    根据操作系统调用相应的通知方式：
    - macOS: 使用 osascript (AppleScript)
    - Linux: 使用 notify-send
    - Windows: 使用 PowerShell Toast

    Args:
        message: 通知消息内容（必填）
        title: 通知标题，默认为 "Claude Code"
        duration: 通知显示时长（毫秒），仅对部分系统有效，默认 5000

    Returns:
        bool: 通知显示成功返回 True，失败返回 False

    示例:
        show_system_notification("操作已完成")
        show_system_notification("权限请求", title="Claude Code - Permission", duration=10000)
    """
    if not message or not isinstance(message, str):
        error("消息内容不能为空且必须是字符串类型")
        return False

    if not title or not isinstance(title, str):
        title = "Claude Code"

    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # 使用 osascript 执行 AppleScript
            applescript = f"""
            display notification "{message}" with title "{title}"
            """
            cmd = ["osascript", "-e", applescript]
            subprocess.run(cmd, check=True, capture_output=True)
            return True

        elif system == "Linux":
            # 使用 notify-send（需要 libnotify 库）
            cmd = ["notify-send", title, message]

            # 如果支持，添加超时参数
            if duration > 0:
                cmd.extend(["-t", str(duration)])

            subprocess.run(cmd, check=True, capture_output=True)
            return True

        elif system == "Windows":
            # 使用 PowerShell Toast Notification
            ps_cmd = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

            $APP_ID = 'ClaudeCode'
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
            "@

            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
            """
            subprocess.run(
                ["powershell", "-Command", ps_cmd],
                check=True,
                capture_output=True
            )
            return True

        else:
            error(f"不支持的操作系统: {system}")
            return False

    except subprocess.CalledProcessError as e:
        error(f"系统通知显示失败: {e}")
        return False
    except FileNotFoundError as e:
        error(f"通知工具未找到（可能未安装）: {e}")
        return False
    except Exception as e:
        error(f"系统通知过程中发生异常: {e}")
        return False


if __name__ == "__main__":
    # 简单测试
    debug("测试 TTS 功能...")
    if play_text_tts("Hello, this is a test"):
        debug("✓ TTS 播放成功")
    else:
        debug("✗ TTS 播放失败")

    debug("测试系统通知功能...")
    if show_system_notification("这是一条测试通知", title="Claude Code"):
        debug("✓ 系统通知显示成功")
    else:
        debug("✗ 系统通知显示失败")
