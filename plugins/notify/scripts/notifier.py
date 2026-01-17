#!/usr/bin/env python3
"""
跨平台系统通知实现
支持 macOS、Linux (D-Bus) 和 Windows (Toast)
"""

import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import Optional


class Notifier:
    """跨平台系统通知器"""

    def __init__(self):
        self.system = platform.system()

    def notify(
        self,
        title: str,
        message: str,
        timeout: int = 5000,
        icon: Optional[str] = None,
    ) -> bool:
        """
        显示系统通知

        Args:
            title: 通知标题
            message: 通知消息
            timeout: 超时时间（毫秒）
            icon: 图标路径（可选）

        Returns:
            是否成功发送通知
        """
        if self.system == "Darwin":
            return self._notify_macos(title, message)
        elif self.system == "Linux":
            return self._notify_linux(title, message, timeout)
        elif self.system == "Windows":
            return self._notify_windows(title, message)
        else:
            return False

    def _notify_macos(self, title: str, message: str) -> bool:
        """macOS 通知 (使用 osascript)"""
        try:
            script = f"""
            display notification "{message}" with title "{title}"
            """
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _notify_linux(self, title: str, message: str, timeout: int) -> bool:
        """Linux 通知 (使用 notify-send)"""
        try:
            subprocess.run(
                ["notify-send", title, message, "-t", str(timeout)],
                check=True,
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _notify_windows(self, title: str, message: str) -> bool:
        """Windows 通知 (使用 PowerShell Toast)"""
        try:
            ps_script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            
            $APP_ID = 'Claude Code'
            
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
                ["powershell", "-Command", ps_script],
                check=True,
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False


def notify(title: str, message: str, timeout: int = 5000) -> bool:
    """便捷函数：发送系统通知"""
    notifier = Notifier()
    return notifier.notify(title, message, timeout)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  notify <message> [title] [timeout]  # 显示系统通知")
        print("  notify -h, --help                   # 显示帮助信息")
        sys.exit(0)

    # 支持 -h/--help 标志
    if sys.argv[1] in ["-h", "--help"]:
        print("使用方法:")
        print("  notify <message> [title] [timeout]  # 显示系统通知")
        print("  notify -h, --help                   # 显示帮助信息")
        print()
        print("参数:")
        print("  message    通知消息（必填）")
        print("  title      通知标题（可选，默认: 'Claude Code'）")
        print("  timeout    显示时间（毫秒，可选，默认: 5000）")
        print()
        print("示例:")
        print("  notify '任务已完成'                          # 使用默认标题")
        print("  notify '任务已完成' '完成'                   # 指定标题")
        print("  notify '任务已完成' '完成' 8000              # 指定标题和超时")
        sys.exit(0)

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("错误: 缺少必要参数", file=sys.stderr)
        print("使用 -h 查看帮助")
        sys.exit(1)

    message = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "Claude Code"

    # 尝试将第三个参数解析为超时时间
    timeout = 5000
    if len(sys.argv) > 3:
        try:
            timeout = int(sys.argv[3])
        except ValueError:
            print(f"错误: 超时时间必须是整数，得到: {sys.argv[3]}", file=sys.stderr)
            sys.exit(1)

    # 发送通知
    success = notify(title, message, timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
