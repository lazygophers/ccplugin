"""
通知和 TTS 功能模块

提供两个主要功能：
1. play_text_tts() - 通过 TTS 播放文本内容
2. show_system_notification() - 显示系统通知
"""

import os
import platform
import subprocess
from typing import Optional

from lib.logging import error
from lib.utils import get_plugins_path, get_project_plugins_dir, get_app_name, get_project_dir

# 预定义图标映射
PREDEFINED_ICONS = {
	'claude': 'claude.svg',  # Anthropic Claude AI 助手官方标志
}

def _resolve_icon_path(icon: str) -> Optional[str]:
	"""解析图标参数为完整路径。

	支持：
	1. 预定义名称 - 如 'claude'，映射到 assets/icons/claude.svg
	2. 绝对路径 - 直接使用
	3. 相对路径 - 按照优先级顺序搜索：
	   - assets/icons/ (用于预定义的项目资源)
	   - assets/ (用于自定义资源)
	   - 脚本目录 (向后兼容)

	Args:
		icon: 图标参数（路径或预定义名称）

	Returns:
		图标文件的完整路径字符串，或 None 如果找不到
	"""
	# 检查是否是预定义名称
	if icon in PREDEFINED_ICONS:
		icon = os.path.join(get_plugins_path(), "assets", "icons", PREDEFINED_ICONS[icon])

	# 如果是绝对路径，直接验证
	if os.path.isabs(icon):
		if os.path.exists(icon) and os.path.isfile(icon):
			return icon
		error(f"图标文件不存在: {icon}")
		return None

	# 相对路径：按优先级搜索
	search_paths = [
		os.path.join(get_project_plugins_dir(), get_app_name(), 'icons', icon),
		os.path.join(get_project_dir(), 'assets', "icons", "svg", icon),
		os.path.join(get_project_dir(), 'assets', "icons", icon),
		os.path.join(get_project_dir(), 'icons', icon),
		os.path.join(get_project_dir(), icon),
	]

	for path in search_paths:
		if os.path.exists(path) and os.path.isfile(path):
			return path

	# 如果找不到文件，记录错误但不中断执行
	error(f"图标文件不存在: {icon} (搜索位置: {', '.join(search_paths)})")
	return None


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
	duration: int = 5000,
	icon: str = 'claude'
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
		icon: 通知图标，可以是预定义名称（'claude'）或文件路径，默认为 'claude'

	Returns:
		bool: 通知显示成功返回 True，失败返回 False

	示例:
		show_system_notification("操作已完成")
		show_system_notification("权限请求", title="Claude Code - Permission", duration=10000)
		show_system_notification("已完成", icon='claude')
		show_system_notification("已完成", icon='/path/to/icon.png')
	"""
	if not message or not isinstance(message, str):
		error("消息内容不能为空且必须是字符串类型")
		return False

	if not title or not isinstance(title, str):
		title = "Claude Code"

	# 解析图标路径
	icon_path = _resolve_icon_path(icon)

	try:
		system = platform.system()

		if system == "Darwin":  # macOS
			# 使用 osascript 执行 AppleScript
			icon_part = ""
			if icon_path:
				# 转义路径中的特殊字符
				escaped_path = str(icon_path).replace("\\", "\\\\").replace('"', '\\"')
				icon_part = f' with icon POSIX file "{escaped_path}"'

			applescript = f"""
            display notification "{message}" with title "{title}"{icon_part}
            """
			cmd = ["osascript", "-e", applescript]
			subprocess.run(cmd, check=True, capture_output=True)
			return True

		elif system == "Linux":
			# 使用 notify-send（需要 libnotify 库）
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

		elif system == "Windows":
			# 使用 PowerShell Toast Notification
			# 构建 XML 模板（支持图标）
			image_element = ""
			if icon_path:
				# 转义路径中的反斜杠
				escaped_icon_path = str(icon_path).replace("\\", "\\\\")
				# Windows Toast 支持 image 元素，使用 file:// URI
				image_element = f'<image placement="appLogoOverride" src="file:///{escaped_icon_path}"/>'

			toast_template = f"""<toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
                {image_element}
            </toast>"""

			# 转义 PowerShell 中的双引号
			ps_template = toast_template.replace('"', '\"')

			ps_cmd = f"""
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