"""
系统通知模块

提供跨平台系统通知功能，支持 macOS、Linux、Windows。
"""

import os
import platform
import subprocess
from typing import Optional

from lib.logging import error


def _resolve_icon_path(
    icon: str,
    plugin_path: Optional[str] = None
) -> Optional[str]:
    """解析图标路径

    Args:
        icon: 图标参数（预定义名称或文件路径）
        plugin_path: 插件路径，用于搜索相对路径

    Returns:
        图标文件的完整路径，或 None 如果找不到
    """
    # 预定义图标映射
    PREDEFINED_ICONS = {
        'claude': 'claude.svg',
        'info': 'info.svg',
        'warning': 'warning.svg',
        'error': 'error.svg',
        'success': 'success.svg',
    }

    # 如果是预定义名称
    if icon in PREDEFINED_ICONS:
        icon = f"assets/icons/{PREDEFINED_ICONS[icon]}"

    # 如果是绝对路径
    if os.path.isabs(icon):
        if os.path.exists(icon) and os.path.isfile(icon):
            return icon
        error(f"图标文件不存在: {icon}")
        return None

    # 相对路径搜索
    if plugin_path:
        search_paths = [
            os.path.join(plugin_path, 'icons', icon),
            os.path.join(plugin_path, 'assets', 'icons', icon),
            os.path.join(plugin_path, 'assets', icon),
        ]

        for path in search_paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path

    return None


def show_system_notification(
    message: str,
    title: str = "Claude Code",
    duration: int = 5000,
    icon: str = 'claude',
    plugin_path: Optional[str] = None
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
        icon: 通知图标，可以是预定义名称（'claude'）或文件路径
        plugin_path: 插件路径，用于搜索相对路径

    Returns:
        通知显示成功返回 True，失败返回 False
    """
    if not message or not isinstance(message, str):
        error("消息内容不能为空且必须是字符串类型")
        return False

    if not title or not isinstance(title, str):
        title = "Claude Code"

    # 解析图标路径
    icon_path = _resolve_icon_path(icon, plugin_path)

    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            return _show_macos_notification(message, title, icon_path)

        elif system == "Linux":
            return _show_linux_notification(message, title, icon_path, duration)

        elif system == "Windows":
            return _show_windows_notification(message, title, icon_path)

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


def _show_macos_notification(
    message: str,
    title: str,
    icon_path: Optional[str] = None
) -> bool:
    """显示 macOS 通知

    Args:
        message: 通知消息
        title: 通知标题
        icon_path: 图标路径

    Returns:
        成功返回 True
    """
    icon_part = ""
    if icon_path:
        # 转义路径中的特殊字符
        escaped_path = str(icon_path).replace("\\", "\\\\").replace('"', '\\"')
        icon_part = f' with icon POSIX file "{escaped_path}"'

    applescript = f'''
    display notification "{message}" with title "{title}"{icon_part}
    '''

    cmd = ["osascript", "-e", applescript]
    subprocess.run(cmd, check=True, capture_output=True)
    return True


def _show_linux_notification(
    message: str,
    title: str,
    icon_path: Optional[str] = None,
    duration: int = 5000
) -> bool:
    """显示 Linux 通知

    Args:
        message: 通知消息
        title: 通知标题
        icon_path: 图标路径
        duration: 显示时长（毫秒）

    Returns:
        成功返回 True
    """
    cmd = ["notify-send"]

    # 添加图标参数
    if icon_path:
        cmd.extend(["-i", str(icon_path)])

    # 添加超时参数
    if duration > 0:
        cmd.extend(["-t", str(duration)])

    cmd.extend([title, message])
    subprocess.run(cmd, check=True, capture_output=True)
    return True


def _show_windows_notification(
    message: str,
    title: str,
    icon_path: Optional[str] = None
) -> bool:
    """显示 Windows 通知

    Args:
        message: 通知消息
        title: 通知标题
        icon_path: 图标路径

    Returns:
        成功返回 True
    """
    # 构建 XML 模板（支持图标）
    image_element = ""
    if icon_path:
        # 转义路径中的反斜杠
        escaped_icon_path = str(icon_path).replace("\\", "\\\\")
        # Windows Toast 支持 image 元素，使用 file:// URI
        image_element = f'<image placement="appLogoOverride" src="file:///{escaped_icon_path}"/>'

    toast_template = f'''<toast>
        <visual>
            <binding template="ToastText02">
                <text id="1">{title}</text>
                <text id="2">{message}</text>
            </binding>
        </visual>
        {image_element}
    </toast>'''

    # 转义 PowerShell 中的双引号
    ps_template = toast_template.replace('"', '\"')

    ps_cmd = f'''
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

    $APP_ID = 'ClaudeCode'
    $template = @"
    {ps_template}
    "@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
    '''

    subprocess.run(
        ["powershell", "-Command", ps_cmd],
        check=True,
        capture_output=True
    )
    return True


def notify(
    message: str,
    title: str = "Claude Code",
    sound: bool = False,
    duration: int = 5000,
    plugin_path: Optional[str] = None
) -> bool:
    """便捷的通知函数

    Args:
        message: 通知消息
        title: 通知标题
        sound: 是否播放声音
        duration: 显示时长（毫秒）
        plugin_path: 插件路径

    Returns:
        成功返回 True
    """
    icon = 'claude' if not sound else 'success'
    return show_system_notification(
        message=message,
        title=title,
        duration=duration,
        icon=icon,
        plugin_path=plugin_path
    )
