"""
通知和 TTS 功能模块

提供两个主要功能：
1. play_text_tts() - 通过 TTS 播放文本内容
2. show_system_notification() - 显示系统通知
"""

import hashlib
import os
import platform
import shutil
import subprocess
import tempfile
from typing import Optional

from lib import logging

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
	# 保留函数名用于兼容旧调用路径，但实现改为“可控时长的无焦点浮层提醒”。
	# 原因：macOS 通知横幅停留时长无法被系统通知 API 可靠控制，无法满足“强制 duration 秒”的要求。
	return _show_macos_overlay_notification(message=message, title=title, duration_seconds=duration_seconds, icon_path=icon_path)


_MACOS_OVERLAY_SWIFT_SOURCE = r'''
import AppKit
import Foundation

final class NonActivatingPanel: NSPanel {
	override var canBecomeKey: Bool { false }
	override var canBecomeMain: Bool { false }
}

func measureHeight(text: String, font: NSFont, width: CGFloat) -> CGFloat {
	let attributes: [NSAttributedString.Key: Any] = [.font: font]
	let rect = (text as NSString).boundingRect(
		with: NSSize(width: width, height: 10_000),
		options: [.usesLineFragmentOrigin, .usesFontLeading],
		attributes: attributes
	)
	return ceil(rect.height)
}

func main() -> Int32 {
	// argv: title message duration_seconds icon_path
	guard CommandLine.arguments.count >= 5 else {
		return 2
	}

	let title = CommandLine.arguments[1]
	let message = CommandLine.arguments[2]
	let durationSeconds = max(1, Int(CommandLine.arguments[3]) ?? 60)
	let iconPath = CommandLine.arguments[4]

	NSApplication.shared.setActivationPolicy(.accessory)

	guard let screen = NSScreen.main ?? NSScreen.screens.first else {
		return 3
	}

	let visible = screen.visibleFrame
	let margin: CGFloat = 16
	let padding: CGFloat = 14
	let gap: CGFloat = 10
	let iconSize: CGFloat = 44
	let width: CGFloat = 380

	let titleFont = NSFont.boldSystemFont(ofSize: 14)
	let messageFont = NSFont.systemFont(ofSize: 13)
	let textWidth = width - padding * 2 - iconSize - gap
	let titleHeight = max(18, measureHeight(text: title, font: titleFont, width: textWidth))
	let messageHeight = min(160, max(18, measureHeight(text: message, font: messageFont, width: textWidth)))
	let contentHeight = max(iconSize, titleHeight + 4 + messageHeight)
	let height: CGFloat = padding * 2 + contentHeight

	let x = visible.maxX - width - margin
	let y = visible.maxY - height - margin
	let rect = NSRect(x: x, y: y, width: width, height: height)

	let panel = NonActivatingPanel(
		contentRect: rect,
		styleMask: [.nonactivatingPanel, .borderless],
		backing: .buffered,
		defer: false
	)
	panel.isFloatingPanel = true
	panel.level = .statusBar
	panel.collectionBehavior = [.canJoinAllSpaces, .transient, .fullScreenAuxiliary]
	panel.backgroundColor = .clear
	panel.isOpaque = false
	panel.hasShadow = true
	panel.ignoresMouseEvents = true

	let background = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: width, height: height))
	background.material = .popover
	background.state = .active
	background.wantsLayer = true
	background.layer?.cornerRadius = 12
	background.layer?.masksToBounds = true

	let iconView = NSImageView(frame: NSRect(x: padding, y: height - padding - iconSize, width: iconSize, height: iconSize))
	iconView.imageScaling = .scaleProportionallyUpOrDown
	iconView.image = NSImage(contentsOfFile: iconPath)

	let titleField = NSTextField(labelWithString: title)
	titleField.font = titleFont
	titleField.textColor = .labelColor
	titleField.lineBreakMode = .byTruncatingTail
	titleField.maximumNumberOfLines = 1

	let messageField = NSTextField(wrappingLabelWithString: message)
	messageField.font = messageFont
	messageField.textColor = .secondaryLabelColor
	messageField.lineBreakMode = .byWordWrapping
	messageField.maximumNumberOfLines = 8

	titleField.frame = NSRect(
		x: padding + iconSize + gap,
		y: height - padding - titleHeight,
		width: textWidth,
		height: titleHeight
	)
	messageField.frame = NSRect(
		x: padding + iconSize + gap,
		y: padding,
		width: textWidth,
		height: height - padding * 2 - titleHeight - 4
	)

	background.addSubview(iconView)
	background.addSubview(titleField)
	background.addSubview(messageField)
	panel.contentView = background

	panel.orderFrontRegardless()

	DispatchQueue.main.asyncAfter(deadline: .now() + .seconds(durationSeconds)) {
		NSAnimationContext.runAnimationGroup({ ctx in
			ctx.duration = 0.18
			panel.animator().alphaValue = 0
		}, completionHandler: {
			NSApp.terminate(nil)
		})
	}

	NSApp.run()
	return 0
}

exit(main())
'''


def _ensure_macos_overlay_binary() -> Optional[str]:
	"""编译并缓存 macOS 浮层提醒二进制（用于强制 duration 秒）。"""
	cache_dir = _get_user_cache_dir("bin")
	os.makedirs(cache_dir, exist_ok=True)

	src_path = os.path.join(cache_dir, "notify_overlay.swift")
	bin_path = os.path.join(cache_dir, "notify_overlay")

	try:
		need_write = True
		if os.path.exists(src_path):
			try:
				with open(src_path, "r", encoding="utf-8") as f:
					need_write = (f.read() != _MACOS_OVERLAY_SWIFT_SOURCE)
			except OSError:
				need_write = True

		if need_write:
			with open(src_path, "w", encoding="utf-8") as f:
				f.write(_MACOS_OVERLAY_SWIFT_SOURCE)

		need_build = (not os.path.exists(bin_path)) or (os.path.getmtime(bin_path) < os.path.getmtime(src_path))
		if need_build:
			if not _command_exists("xcrun"):
				error("macOS 浮层提醒需要 xcrun/swiftc（请安装 Xcode Command Line Tools）")
				return None

			result = subprocess.run(
				["xcrun", "swiftc", "-O", src_path, "-o", bin_path],
				capture_output=True,
				text=True,
			)
			if result.returncode != 0:
				error(f"编译 macOS 浮层提醒失败: {result.stderr.strip()}")
				return None

			try:
				os.chmod(bin_path, 0o755)
			except OSError:
				pass

		return bin_path
	except Exception as e:
		error(f"准备 macOS 浮层提醒失败: {e}")
		return None


def _show_macos_overlay_notification(message: str, title: str, duration_seconds: int, icon_path: Optional[str]) -> bool:
	"""macOS：不抢焦点的右上角浮层提醒，强制展示 duration_seconds 秒。"""
	if not icon_path:
		error("macOS 通知要求提供可用的 icon_path，但未找到图标文件")
		return False

	icon_for_overlay = icon_path
	if icon_path.lower().endswith(".svg") and _command_exists("qlmanage"):
		converted = _svg_to_png_cached(icon_path)
		if converted:
			icon_for_overlay = converted

	bin_path = _ensure_macos_overlay_binary()
	if not bin_path:
		return False

	timeout_seconds = max(1, int(duration_seconds))
	try:
		subprocess.Popen(
			[bin_path, title, message, str(timeout_seconds), str(icon_for_overlay)],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		return True
	except Exception as e:
		error(f"启动 macOS 浮层提醒失败: {e}")
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
	- macOS: 使用不抢焦点的浮层提醒（保证 duration 秒 + 自定义 logo/title/message）
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
			# 强制要求：duration、logo、title、message
			if _show_macos_notification_terminal_notifier(message, title, duration, icon_path):
				return True
			return False

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
	logging.enable_debug()
	show_system_notification("操作已完成")
