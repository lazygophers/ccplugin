#!/usr/bin/env python3
"""
Notify CLI - 通知和语音播报命令行工具

提供系统通知、语音播报、声音克隆等功能。

用法:
    notify "消息内容" [--title "标题"] [--speak]
    speak "文本内容"
    voice list
    voice clone <voice_id> --audio <file>
    config show
"""
import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def cmd_notify(args):
    """发送系统通知（主命令）"""
    from lib.notify.notification import show_system_notification
    from lib.notify.tts import speak
    from lib.notify.config import load_config

    # 发送系统通知
    result = show_system_notification(
        message=args.message,
        title=args.title or "Claude Code",
        duration=args.duration or 5000,
        icon=args.icon or 'claude',
    )

    if result:
        console.print("[green]✓[/green] 通知已发送")
    else:
        console.print("[red]✗[/red] 通知发送失败")
        return 1

    # 如果需要语音播报
    if args.speak:
        config = load_config()
        if config.tts_enabled:
            console.print(f"[dim]正在播报:[/dim] {args.message}")
            speak(args.message, voice_id=args.voice, config=config, blocking=not args.non_blocking)
        else:
            console.print("[yellow]TTS 功能已禁用[/yellow]")

    return 0


def cmd_speak(args):
    """语音播报"""
    from lib.notify.tts import speak
    from lib.notify.config import load_config

    config = load_config()
    result = speak(
        text=args.text,
        voice_id=args.voice,
        config=config,
        blocking=not args.non_blocking
    )

    if result:
        console.print("[green]✓[/green] 语音播报完成")
    else:
        console.print("[red]✗[/red] 语音播报失败")
        return 1

    return 0


def cmd_voice_list(args):
    """列出所有音色"""
    from lib.notify.config import load_config
    from lib.notify.voice import VoiceCloner

    config = load_config()
    cloner = VoiceCloner()
    voices = cloner.list()

    if not voices:
        console.print("[dim]没有克隆音色[/dim]")
        return 0

    table = Table(title="[bold]克隆音色列表[/bold]", show_header=True)
    table.add_column("ID", style="cyan", width=20)
    table.add_column("名称", style="white", width=20)
    table.add_column("语言", style="yellow", width=10)
    table.add_column("引擎", style="green", width=10)
    table.add_column("默认", style="magenta", width=8)

    for voice in voices:
        is_default = "[green]✓[/green]" if config.default_voice_id == voice.id else ""
        table.add_row(
            voice.id,
            voice.name,
            voice.language,
            voice.engine,
            is_default
        )

    console.print(table)

    # 同时列出所有配置的音色
    if config.voices:
        console.print(f"\n[dim]总计: {len(config.voices)} 个音色[/dim]")

    return 0


def cmd_voice_clone(args):
    """克隆声音"""
    from lib.notify.voice import VoiceCloner

    cloner = VoiceCloner()

    if not args.audio:
        console.print("[red]错误: --audio 参数是必需的[/red]")
        return 1

    console.print(f"[cyan]正在克隆声音:[/cyan] {args.voice_id}")
    console.print(f"[dim]参考音频:[/dim] {args.audio}")

    result = cloner.clone(
        voice_id=args.voice_id,
        reference_audio=args.audio,
        name=args.name or args.voice_id,
        language=args.language or "zh"
    )

    if result:
        console.print(f"[green]✓[/green] 声音克隆成功: {args.voice_id}")
    else:
        console.print(f"[red]✗[/red] 声音克隆失败")
        return 1

    return 0


def cmd_voice_delete(args):
    """删除声音"""
    from lib.notify.voice import VoiceCloner

    cloner = VoiceCloner()
    result = cloner.delete(args.voice_id)

    if result:
        console.print(f"[green]✓[/green] 已删除音色: {args.voice_id}")
    else:
        console.print(f"[red]✗[/red] 删除失败: {args.voice_id}")
        return 1

    return 0


def cmd_voice_info(args):
    """显示声音信息"""
    from lib.notify.config import load_config

    config = load_config()
    voice = config.voices.get(args.voice_id)

    if not voice:
        console.print(f"[red]✗[/red] 音色不存在: {args.voice_id}")
        return 1

    console.print(Panel.fit(
        f"[bold cyan]音色信息[/bold cyan]\n\n"
        f"[dim]ID:[/dim] {voice.id}\n"
        f"[dim]名称:[/dim] {voice.name}\n"
        f"[dim]引擎:[/dim] {voice.engine}\n"
        f"[dim]语言:[/dim] {voice.language}\n"
        f"[dim]语速:[/dim] {voice.speed}x\n"
        f"[dim]音调:[/dim] {voice.pitch}x\n"
        f"[dim]是否克隆:[/dim] {'是' if voice.is_cloned else '否'}\n"
        f"[dim]参考音频:[/dim] {voice.speaker_wav or 'N/A'}\n"
    ))

    return 0


def cmd_config_show(args):
    """显示配置"""
    from lib.notify.config import load_config

    config = load_config()

    console.print(Panel.fit(
        f"[bold cyan]通知配置[/bold cyan]\n\n"
        f"[dim]默认音色:[/dim] {config.default_voice_id or '未设置'}\n"
        f"[dim]TTS 引擎:[/dim] {config.tts_engine}\n"
        f"[dim]系统通知:[/dim] {'启用' if config.system_notification else '禁用'}\n"
        f"[dim]TTS 播报:[/dim] {'启用' if config.tts_enabled else '禁用'}\n"
        f"[dim]默认语言:[/dim] {config.language}\n"
        f"[dim]音色数量:[/dim] {len(config.voices)}\n"
    ))

    return 0


def cmd_config_set(args):
    """设置配置"""
    from lib.notify.config import load_config, save_config, set_default_voice

    config = load_config()

    if args.default_voice:
        result = set_default_voice(config, args.default_voice)
        if result:
            console.print(f"[green]✓[/green] 默认音色已设置: {args.default_voice}")
            save_config(config)
        else:
            console.print(f"[red]✗[/red] 设置失败: 音色不存在")
            return 1

    if args.enable_tts is not None:
        config.tts_enabled = args.enable_tts
        status = "启用" if args.enable_tts else "禁用"
        console.print(f"[green]✓[/green] TTS 已{status}")
        save_config(config)

    if args.enable_notification is not None:
        config.system_notification = args.enable_notification
        status = "启用" if args.enable_notification else "禁用"
        console.print(f"[green]✓[/green] 系统通知已{status}")
        save_config(config)

    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Notify CLI - 通知和语音播报工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  notify "操作完成"                          # 发送系统通知
  notify "操作完成" --title "标题"           # 带标题的通知
  notify "操作完成" --speak                  # 发送通知并语音播报
  speak "你好，世界"                          # 仅语音播报
  voice list                                 # 列出所有音色
  voice clone my-voice --audio ref.wav       # 克隆声音
  config show                                # 显示配置
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 主命令 - 发送系统通知（默认）
    notify_parser = subparsers.add_parser('notify', help='发送系统通知')
    notify_parser.add_argument('message', help='通知消息')
    notify_parser.add_argument('--title', '-t', help='通知标题')
    notify_parser.add_argument('--duration', '-d', type=int, help='显示时长（毫秒）')
    notify_parser.add_argument('--icon', '-i', help='图标名称或路径')
    notify_parser.add_argument('--speak', '-s', action='store_true', help='同时语音播报')
    notify_parser.add_argument('--voice', '-v', help='播报时使用的音色 ID')
    notify_parser.add_argument('--non-blocking', '-n', action='store_true', help='非阻塞模式（仅语音播报）')
    notify_parser.set_defaults(func=cmd_notify)

    # speak 命令 - 语音播报
    speak_parser = subparsers.add_parser('speak', help='语音播报')
    speak_parser.add_argument('text', help='要播报的文本')
    speak_parser.add_argument('--voice', '-v', help='音色 ID')
    speak_parser.add_argument('--non-blocking', '-n', action='store_true', help='非阻塞模式')
    speak_parser.set_defaults(func=cmd_speak)

    # voice 命令组 - 声音管理
    voice_parser = subparsers.add_parser('voice', help='声音管理')
    voice_subparsers = voice_parser.add_subparsers(dest='voice_command', help='声音子命令')

    # voice list
    voice_list_parser = voice_subparsers.add_parser('list', help='列出所有音色')
    voice_list_parser.set_defaults(func=cmd_voice_list)

    # voice clone
    voice_clone_parser = voice_subparsers.add_parser('clone', help='克隆声音')
    voice_clone_parser.add_argument('voice_id', help='音色 ID')
    voice_clone_parser.add_argument('--audio', '-a', required=True, help='参考音频文件路径')
    voice_clone_parser.add_argument('--name', '-n', help='音色名称')
    voice_clone_parser.add_argument('--language', '-l', help='语言代码')
    voice_clone_parser.set_defaults(func=cmd_voice_clone)

    # voice delete
    voice_delete_parser = voice_subparsers.add_parser('delete', help='删除音色')
    voice_delete_parser.add_argument('voice_id', help='音色 ID')
    voice_delete_parser.set_defaults(func=cmd_voice_delete)

    # voice info
    voice_info_parser = voice_subparsers.add_parser('info', help='显示音色信息')
    voice_info_parser.add_argument('voice_id', help='音色 ID')
    voice_info_parser.set_defaults(func=cmd_voice_info)

    # config 命令组 - 配置管理
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='配置子命令')

    # config show
    config_show_parser = config_subparsers.add_parser('show', help='显示配置')
    config_show_parser.set_defaults(func=cmd_config_show)

    # config set
    config_set_parser = config_subparsers.add_parser('set', help='设置配置')
    config_set_parser.add_argument('--default-voice', help='设置默认音色')
    config_set_parser.add_argument('--enable-tts', type=lambda x: x.lower() == 'true', help='启用/禁用 TTS')
    config_set_parser.add_argument('--enable-notification', type=lambda x: x.lower() == 'true', help='启用/禁用系统通知')
    config_set_parser.set_defaults(func=cmd_config_set)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())