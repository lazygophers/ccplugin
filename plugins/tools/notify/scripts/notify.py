"""
通知和 TTS 功能模块

提供两个主要功能：
1. play_text_tts() - 通过 TTS 播放文本内容
2. show_system_notification() - 显示系统通知
"""

import hashlib
import math
import os
import platform
import shutil
import subprocess
import tempfile
from typing import Optional

from icons import PREDEFINED_ICONS
from lib.logging import error
from lib.utils import get_plugins_path, get_project_plugins_dir, get_app_name, get_project_dir


def _command_exists(cmd: str) -> bool:
	return shutil.which(cmd) is not None


def _get_user_cache_dir(*parts: str) -> str:
	# Keep cache in the same family as existing config paths used by this plugin.
	base_dir = os.path.join(os.path.expanduser("~"), ".lazygophers", "ccplugin", "notify", "cache")
	return os.path.join(base_dir, *parts)


def _svg_to_png_cached(svg_path: str, size: int = 256) -> Optional[str]:
	"""Convert an SVG to a PNG using macOS QuickLook (qlmanage), with caching."""
	try:
		st = os.stat(svg_path)
	except OSError as e:
		error(f"读取 SVG 图标失败: {e}")
		return None

	cache_dir = _get_user_cache_dir("icons")
	os.makedirs(cache_dir, exist_ok=True)

	cache_key = f"{svg_path}:{st.st_mtime_ns}:{st.st_size}:{size}"
	cache_name = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".png"
	cached_png = os.path.join(cache_dir, cache_name)
	if os.path.exists(cached_png):
		return cached_png

	tmpdir = tempfile.mkdtemp(prefix="notify-icon-")
	try:
		subprocess.run(
			["qlmanage", "-t", "-s", str(size), "-o", tmpdir, svg_path],
			check=True,
			capture_output=True,
		)
		generated = os.path.join(tmpdir, os.path.basename(svg_path) + ".png")
		if not os.path.exists(generated):
			error(f"SVG 转 PNG 失败（未生成输出文件）: {svg_path}")
			return None
		shutil.move(generated, cached_png)
		return cached_png
	except FileNotFoundError:
		error("qlmanage 未找到，无法将 SVG 转换为 PNG（macOS 特有）")
		return None
	except subprocess.CalledProcessError as e:
		error(f"SVG 转 PNG 失败: {e}")
		return None
	finally:
		shutil.rmtree(tmpdir, ignore_errors=True)


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


def _show_macos_notification_terminal_notifier(
	message: str,
	title: str,
	duration_seconds: int,
	icon_path: Optional[str],
) -> bool:
	if not _command_exists("terminal-notifier"):
		return False

	cmd = ["terminal-notifier", "-title", title, "-message", message]

	if duration_seconds and duration_seconds > 0:
		timeout_seconds = max(1, int(math.ceil(duration_seconds)))
		cmd.extend(["-timeout", str(timeout_seconds)])

	if icon_path:
		icon_for_notifier = icon_path
		if icon_path.lower().endswith(".svg") and _command_exists("qlmanage"):
			converted = _svg_to_png_cached(icon_path)
			if converted:
				icon_for_notifier = converted
			else:
				icon_for_notifier = None

		if icon_for_notifier:
			cmd.extend(["-appIcon", icon_for_notifier])

	try:
		subprocess.run(cmd, check=True, capture_output=True)
		return True
	except subprocess.CalledProcessError as e:
		error(f"terminal-notifier 通知失败: {e}")
		return False


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
	duration: int = 60,
	icon: str = 'claude'
) -> bool:
	"""显示系统通知

	根据操作系统调用相应的通知方式：
	- macOS: 优先使用 terminal-notifier（可选），否则使用 osascript (AppleScript)
	- Linux: 使用 notify-send
	- Windows: 使用 PowerShell Toast

	Args:
		message: 通知消息内容（必填）
		title: 通知标题，默认为 "Claude Code"
		duration: 通知显示时长（秒），仅对部分系统有效，默认 60
		icon: 通知图标，可以是预定义名称（'claude'）或文件路径，默认为 'claude'

	Returns:
		bool: 通知显示成功返回 True，失败返回 False

	示例:
		show_system_notification("操作已完成")
		show_system_notification("权限请求", title="Claude Code - Permission", duration=10)
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
			# 1) 优先 terminal-notifier：支持 icon/timeout（更接近“系统通知”期望）
			if _show_macos_notification_terminal_notifier(message, title, duration, icon_path):
				return True

			# 2) 回退到 osascript：仅支持 title/message（不支持 icon/timeout）
			cmd = [
				"osascript",
				"-e",
				"on run argv",
				"-e",
				"display notification (item 1 of argv) with title (item 2 of argv)",
				"-e",
				"end run",
				message,
				title,
			]
			subprocess.run(cmd, check=True, capture_output=True)
			return True

		elif system == "Linux":
			# 使用 notify-send（需要 libnotify 库）
			cmd = ["notify-send"]

			# 添加图标参数
			if icon_path:
				cmd.extend(["-i", str(icon_path)])

			# 添加超时参数（notify-send 单位为毫秒）
			if duration > 0:
				cmd.extend(["-t", str(int(duration * 1000))])

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


if __name__ == '__main__':
	show_system_notification("操作已完成")