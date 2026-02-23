"""
通知和 TTS 功能模块

提供两个主要功能：
1. play_text_tts() - 通过 TTS 播放文本内容
2. show_system_notification() - 显示系统通知
"""

import base64
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

from icons import PREDEFINED_ICONS
from lib import logging
from lib.logging import error
from lib.utils import get_plugins_path, get_project_plugins_dir, get_app_name, get_project_dir


def _command_exists(cmd: str) -> bool:
	return shutil.which(cmd) is not None


def _file_md5(path: str) -> Optional[str]:
	try:
		h = hashlib.md5()
		with open(path, "rb") as f:
			for chunk in iter(lambda: f.read(1024 * 1024), b""):
				h.update(chunk)
		return h.hexdigest()
	except OSError as e:
		error(f"读取文件失败: {e}")
		return None


def _get_user_cache_dir(*parts: str) -> str:
	# Keep cache in the same family as existing config paths used by this plugin.
	base_dir = os.path.join(os.path.expanduser("~"), ".lazygophers", "ccplugin", "notify", "cache")
	return os.path.join(base_dir, *parts)


def _svg_to_png_cached(svg_path: str, size: int = 256) -> Optional[str]:
	"""Convert an SVG to a PNG with caching.

	Conversion backends (in order):
	- rsvg-convert
	- cairosvg
	- inkscape
	- ImageMagick (magick/convert)
	- macOS qlmanage (fallback; may produce opaque thumbnails)
	"""
	try:
		st = os.stat(svg_path)
	except OSError as e:
		error(f"读取 SVG 图标失败: {e}")
		return None

	cache_dir = _get_user_cache_dir("icons")
	os.makedirs(cache_dir, exist_ok=True)

	source_md5 = _file_md5(svg_path)
	if not source_md5:
		return None

	# 按“文件内容 md5”去重：同内容同尺寸只生成一次缓存文件，不重复覆盖/生成
	cached_png = os.path.join(cache_dir, f"svg_{source_md5}_{int(size)}.png")
	if os.path.exists(cached_png):
		return cached_png

	tmpdir = tempfile.mkdtemp(prefix="notify-icon-")
	try:
		out_path = os.path.join(tmpdir, "out.png")

		if _command_exists("rsvg-convert"):
			subprocess.run(
				["rsvg-convert", "-w", str(size), "-h", str(size), "-o", out_path, svg_path],
				check=True,
				capture_output=True,
			)
			generated = out_path
		elif _command_exists("cairosvg"):
			subprocess.run(
				["cairosvg", "-o", out_path, "-W", str(size), "-H", str(size), svg_path],
				check=True,
				capture_output=True,
			)
			generated = out_path
		elif _command_exists("inkscape"):
			# Compatible with Inkscape 1.x
			subprocess.run(
				["inkscape", svg_path, "-o", out_path, "-w", str(size), "-h", str(size)],
				check=True,
				capture_output=True,
			)
			generated = out_path
		elif _command_exists("magick"):
			subprocess.run(
				["magick", svg_path, "-background", "none", "-alpha", "on", "-resize", f"{size}x{size}", out_path],
				check=True,
				capture_output=True,
			)
			generated = out_path
		elif _command_exists("convert"):
			subprocess.run(
				["convert", svg_path, "-background", "none", "-alpha", "on", "-resize", f"{size}x{size}", out_path],
				check=True,
				capture_output=True,
			)
			generated = out_path
		elif platform.system() == "Darwin" and _command_exists("qlmanage"):
			subprocess.run(
				["qlmanage", "-t", "-s", str(size), "-o", tmpdir, svg_path],
				check=True,
				capture_output=True,
			)
			generated = os.path.join(tmpdir, os.path.basename(svg_path) + ".png")
		else:
			error("缺少 SVG 转 PNG 工具：请安装 rsvg-convert / inkscape / ImageMagick，或直接提供 PNG 图标")
			return None

		if not os.path.exists(generated):
			error(f"SVG 转 PNG 失败（未生成输出文件）: {svg_path}")
			return None

		# 若目标已存在（并发/重复触发），不覆盖，直接复用
		if os.path.exists(cached_png):
			return cached_png

		shutil.move(generated, cached_png)
		return cached_png
	except subprocess.CalledProcessError as e:
		error(f"SVG 转 PNG 失败: {e}")
		return None
	finally:
		shutil.rmtree(tmpdir, ignore_errors=True)


def _icon_for_overlay(icon_path: Optional[str]) -> Optional[str]:
	"""为 overlay 选择可用的 icon 文件路径（强制要求：必须能展示 logo）。"""
	if isinstance(icon_path, str) and icon_path and os.path.exists(icon_path):
		if icon_path.lower().endswith(".svg"):
			converted = _svg_to_png_cached(icon_path)
			if converted:
				return converted
			return None
		return icon_path

	return None


_TK_OVERLAY_SCRIPT = r'''
import sys
import os
import time

def main() -> int:
	if len(sys.argv) < 5:
		return 2

	title = sys.argv[1]
	message = sys.argv[2]
	duration_seconds = max(1, int(float(sys.argv[3])))
	icon_path = sys.argv[4]

	import tkinter as tk

	root = tk.Tk()
	root.overrideredirect(True)
	root.attributes("-topmost", True)
	try:
		root.wm_attributes("-type", "notification")
	except Exception:
		pass

	# Try to avoid focus stealing on Windows
	if sys.platform.startswith("win"):
		try:
			import ctypes
			from ctypes import wintypes

			GWL_EXSTYLE = -20
			WS_EX_TOOLWINDOW = 0x00000080
			WS_EX_NOACTIVATE = 0x08000000
			WS_EX_TRANSPARENT = 0x00000020

			hwnd = root.winfo_id()
			user32 = ctypes.windll.user32
			user32.GetWindowLongW.restype = wintypes.LONG
			exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
			user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT)
			# SW_SHOWNOACTIVATE = 4
			user32.ShowWindow(hwnd, 4)
		except Exception:
			pass

	root.configure(bg="#000000")
	frame = tk.Frame(root, bg="#1e1e1e", bd=0, highlightthickness=0)
	frame.pack(fill="both", expand=True)

	# Layout constants
	padding = 12
	gap = 10
	width = 380

	# Icon
	icon = None
	if icon_path and os.path.exists(icon_path):
		try:
			icon = tk.PhotoImage(file=icon_path)
			# downscale if too large
			while icon.width() > 64 and icon.height() > 64:
				icon = icon.subsample(2, 2)
		except Exception:
			icon = None

	row = 0
	if icon is not None:
		icon_label = tk.Label(frame, image=icon, bg="#1e1e1e")
		icon_label.image = icon
		icon_label.grid(row=0, column=0, rowspan=2, padx=(padding, 0), pady=padding, sticky="n")
		text_col = 1
	else:
		text_col = 0

	title_label = tk.Label(
		frame,
		text=title,
		bg="#1e1e1e",
		fg="#ffffff",
		font=("Segoe UI", 11, "bold") if sys.platform.startswith("win") else ("Sans", 11, "bold"),
		anchor="w",
	)
	title_label.grid(row=0, column=text_col, padx=(padding if text_col == 0 else gap, padding), pady=(padding, 0), sticky="we")

	message_label = tk.Label(
		frame,
		text=message,
		bg="#1e1e1e",
		fg="#dddddd",
		font=("Segoe UI", 10) if sys.platform.startswith("win") else ("Sans", 10),
		justify="left",
		anchor="nw",
		wraplength=width - padding * 2 - (64 + gap if text_col == 1 else 0),
	)
	message_label.grid(row=1, column=text_col, padx=(padding if text_col == 0 else gap, padding), pady=(6, padding), sticky="we")

	frame.grid_columnconfigure(text_col, weight=1)

	root.update_idletasks()
	win_w = max(width, frame.winfo_reqwidth())
	win_h = frame.winfo_reqheight()

	screen_w = root.winfo_screenwidth()
	screen_h = root.winfo_screenheight()
	x = screen_w - win_w - 16
	y = 16
	root.geometry(f"{win_w}x{win_h}+{x}+{y}")

	# auto close
	root.after(int(duration_seconds * 1000), root.destroy)
	root.mainloop()
	return 0

if __name__ == "__main__":
	raise SystemExit(main())
'''


def _ensure_tk_overlay_script() -> Optional[str]:
	cache_dir = _get_user_cache_dir("bin")
	os.makedirs(cache_dir, exist_ok=True)
	source_md5 = hashlib.md5(_TK_OVERLAY_SCRIPT.encode("utf-8")).hexdigest()[:16]
	script_path = os.path.join(cache_dir, f"notify_overlay_tk_{source_md5}.py")

	try:
		# 文件名已包含源码 md5：同内容不重复写入/覆盖
		if not os.path.exists(script_path):
			with open(script_path, "w", encoding="utf-8") as f:
				f.write(_TK_OVERLAY_SCRIPT)

		return script_path
	except Exception as e:
		error(f"准备 Tk overlay 脚本失败: {e}")
		return None


def _tkinter_available() -> bool:
	"""不使用 try-import：用子进程检测 tkinter 是否可用。"""
	try:
		python_exe = sys.executable
		if not python_exe:
			python_exe = shutil.which("python3") or shutil.which("python") or "python"
		result = subprocess.run(
			[python_exe, "-c", "import tkinter"],
			capture_output=True,
			text=True,
		)
		return result.returncode == 0
	except Exception:
		return False


def _show_tk_overlay_notification(message: str, title: str, duration_seconds: int, icon_path: Optional[str]) -> bool:
	if not _tkinter_available():
		error("Tkinter 不可用，无法满足强制 duration/logo/title/message 的提醒需求")
		return False

	script_path = _ensure_tk_overlay_script()
	if not script_path:
		return False

	icon_for_overlay = _icon_for_overlay(icon_path)
	if not icon_for_overlay:
		error("无法获取可用图标，无法满足强制 logo 要求")
		return False
	logging.debug(f"Tk overlay 使用图标: {icon_for_overlay}")

	timeout_seconds = max(1, int(duration_seconds))
	try:
		subprocess.Popen(
			[sys.executable, script_path, title, message, str(timeout_seconds), str(icon_for_overlay)],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		return True
	except Exception as e:
		error(f"启动 Tk overlay 失败: {e}")
		return False


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
	return _show_macos_overlay_notification(message=message, title=title, duration_seconds=duration_seconds,
	                                        icon_path=icon_path)


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
	// argv: title message duration_seconds icon_b64_or_path
	guard CommandLine.arguments.count >= 5 else {
		return 2
	}

	let title = CommandLine.arguments[1]
	let message = CommandLine.arguments[2]
	let durationSeconds = max(1, Int(CommandLine.arguments[3]) ?? 60)
	let iconArg = CommandLine.arguments[4]

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

	var iconImage: NSImage? = nil
	if iconArg.hasPrefix("b64:") {
		let b64 = String(iconArg.dropFirst(4))
		if let data = Data(base64Encoded: b64, options: [.ignoreUnknownCharacters]) {
			iconImage = NSImage(data: data)
		}
	} else {
		iconImage = NSImage(contentsOfFile: iconArg)
		if iconImage == nil {
			let url = URL(fileURLWithPath: iconArg)
			if let data = try? Data(contentsOf: url) {
				iconImage = NSImage(data: data)
			}
		}
	}
	if let img = iconImage {
		img.isTemplate = false
	}

	let iconView = NSImageView(frame: NSRect(x: padding, y: height - padding - iconSize, width: iconSize, height: iconSize))
	iconView.imageScaling = .scaleProportionallyUpOrDown
	iconView.image = iconImage

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

	# 使用源码内容的 md5：只有源码变更才会生成新文件，尽可能减少重复生成
	source_md5_full = hashlib.md5(_MACOS_OVERLAY_SWIFT_SOURCE.encode("utf-8")).hexdigest()
	source_md5 = source_md5_full[:16]
	src_path = os.path.join(cache_dir, f"notify_overlay_{source_md5}.swift")
	ref_path = os.path.join(cache_dir, f"notify_overlay_{source_md5}.ref")

	try:
		# 如果已有源码->bin 的映射，直接复用，避免重复编译
		if os.path.exists(ref_path):
			try:
				with open(ref_path, "r", encoding="utf-8") as f:
					bin_name = f.read().strip()
				if bin_name:
					candidate = os.path.join(cache_dir, bin_name)
					if os.path.exists(candidate):
						return candidate
			except OSError:
				pass

		# 文件名已包含源码 hash：同二进制不重复生成/覆盖
		if not os.path.exists(src_path):
			with open(src_path, "w", encoding="utf-8") as f:
				f.write(_MACOS_OVERLAY_SWIFT_SOURCE)

		if not _command_exists("xcrun"):
			error("macOS 浮层提醒需要 xcrun/swiftc（请安装 Xcode Command Line Tools）")
			return None

		tmp_bin = os.path.join(cache_dir, f".notify_overlay_tmp_{os.getpid()}_{source_md5}")
		result = subprocess.run(
			["xcrun", "swiftc", "-O", src_path, "-o", tmp_bin],
			capture_output=True,
			text=True,
		)
		if result.returncode != 0:
			error(f"编译 macOS 浮层提醒失败: {result.stderr.strip()}")
			return None

		bin_md5_full = _file_md5(tmp_bin)
		if not bin_md5_full:
			try:
				os.remove(tmp_bin)
			except OSError:
				pass
			return None

		bin_name = f"notify_overlay_bin_{bin_md5_full[:16]}"
		bin_path = os.path.join(cache_dir, bin_name)

		if os.path.exists(bin_path):
			# 已有完全相同的二进制，删除临时文件即可
			try:
				os.remove(tmp_bin)
			except OSError:
				pass
		else:
			shutil.move(tmp_bin, bin_path)
			try:
				os.chmod(bin_path, 0o755)
			except OSError:
				pass

		# 写入映射：同源码后续不再编译
		if not os.path.exists(ref_path):
			try:
				with open(ref_path, "w", encoding="utf-8") as f:
					f.write(bin_name)
			except OSError:
				pass

		return bin_path
	except Exception as e:
		error(f"准备 macOS 浮层提醒失败: {e}")
		return None


def _show_macos_overlay_notification(message: str, title: str, duration_seconds: int, icon_path: Optional[str]) -> bool:
	"""macOS：不抢焦点的右上角浮层提醒，强制展示 duration_seconds 秒。"""
	icon_for_overlay = _icon_for_overlay(icon_path)
	if not icon_for_overlay:
		error("macOS 通知无法获取可用图标，无法满足强制 logo 要求")
		return False
	logging.debug(f"macOS overlay 使用图标: {icon_for_overlay}")

	bin_path = _ensure_macos_overlay_binary()
	if not bin_path:
		return False

	timeout_seconds = max(1, int(duration_seconds))
	try:
		with open(icon_for_overlay, "rb") as f:
			icon_b64 = base64.b64encode(f.read()).decode("ascii")

		subprocess.Popen(
			[bin_path, title, message, str(timeout_seconds), f"b64:{icon_b64}"],
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
	duration: int = 30,
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
	if not icon_path:
		error("通知要求提供可用的 icon，但未找到图标文件")
		return False

	logging.debug(f"解析到图标路径: {icon_path}")

	try:
		system = platform.system()

		if system == "Darwin":  # macOS
			# 强制要求：duration、logo、title、message
			return _show_macos_notification_terminal_notifier(message, title, duration, icon_path)

		elif system == "Linux":
			# 强制要求：duration、logo、title、message
			return _show_tk_overlay_notification(message=message, title=title, duration_seconds=duration,
			                                     icon_path=icon_path)

		elif system == "Windows":
			# 强制要求：duration、logo、title、message
			return _show_tk_overlay_notification(message=message, title=title, duration_seconds=duration,
			                                     icon_path=icon_path)

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
	show_system_notification("操作已完成", icon='./assets/icons/claude.svg')
