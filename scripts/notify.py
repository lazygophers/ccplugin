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
import os
import sys
from pathlib import Path  # noqa: E402

# 添加项目根目录到 Python 路径
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

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
        icon=args.icon or "claude",
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
            speak(
                args.message,
                voice_id=args.voice,
                config=config,
                blocking=not args.non_blocking,
            )
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
        blocking=not args.non_blocking,
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
        table.add_row(voice.id, voice.name, voice.language, voice.engine, is_default)

    console.print(table)

    # 同时列出所有配置的音色
    if config.voices:
        console.print(f"\n[dim]总计: {len(config.voices)} 个音色[/dim]")

    return 0


def cmd_voice_clone(args):
    """克隆声音"""
    from lib.notify.voice import VoiceTrainer

    trainer = VoiceTrainer()

    # 支持通配符和多个音频文件
    audio_files = args.audio

    console.print(f"[cyan]正在克隆声音:[/cyan] {args.voice_id}")
    console.print(f"[dim]参考音频:[/dim] {', '.join(audio_files)}")

    # 检查是否使用深度微调
    if args.finetune:
        console.print("[yellow]使用 XTTS 深度微调模式[/yellow]")
        result = trainer.train_from_samples(
            voice_id=args.voice_id,
            sample_paths=audio_files,
            name=args.name,
            language=args.language or "zh",
            recursive=args.recursive,
        )

        if result:
            console.print("[cyan]开始 XTTS 深度微调...[/cyan]")
            finetune_result = trainer.finetune(
                voice_id=args.voice_id, epochs=args.epochs or 10, use_gpu=not args.cpu
            )
            if finetune_result:
                console.print(f"[green]✓[/green] XTTS 微调完成: {args.voice_id}")
            else:
                console.print("[yellow]⚠[/yellow] 微调失败，已使用参考音频模式")
                return 1
        else:
            console.print("[red]✗[/red] 准备训练数据失败")
            return 1
    else:
        # 使用参考音频模式
        if len(audio_files) == 1:
            # 单个文件
            result = trainer.clone(
                voice_id=args.voice_id,
                reference_audio=audio_files[0],
                name=args.name,
                language=args.language or "zh",
            )
        else:
            # 多个文件
            result = trainer.train_from_samples(
                voice_id=args.voice_id,
                sample_paths=audio_files,
                name=args.name,
                language=args.language or "zh",
                recursive=args.recursive,
            )

    if result:
        console.print(f"[green]✓[/green] 声音克隆成功: {args.voice_id}")
    else:
        console.print("[red]✗[/red] 声音克隆失败")
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


def cmd_voice_add_sample(args):
    """添加样本到已有音色"""
    from lib.notify.voice import VoiceTrainer
    from lib.notify.config import load_config

    trainer = VoiceTrainer()
    config = load_config()

    voice = config.voices.get(args.voice_id)
    if not voice:
        console.print(f"[red]✗[/red] 音色不存在: {args.voice_id}")
        return 1

    console.print(f"[cyan]添加样本到音色:[/cyan] {args.voice_id}")
    console.print(f"[dim]音频文件:[/dim] {', '.join(args.audio)}")

    result = trainer.add_sample(
        voice_id=args.voice_id, audio_path=" ".join(args.audio), config=config
    )

    if result:
        console.print("[green]✓[/green] 样本已添加")
        console.print(f"[dim]当前样本数量: {len(voice.samples)}[/dim]")
        return 0
    else:
        console.print("[red]✗[/red] 添加样本失败")
        return 1


def cmd_voice_remove_sample(args):
    """从音色中删除样本"""
    from lib.notify.voice import VoiceTrainer
    from lib.notify.config import load_config

    trainer = VoiceTrainer()
    config = load_config()

    voice = config.voices.get(args.voice_id)
    if not voice:
        console.print(f"[red]✗[/red] 音色不存在: {args.voice_id}")
        return 1

    console.print(f"[cyan]从音色中删除样本:[/cyan] {args.voice_id}")
    console.print(f"[dim]样本索引:[/dim] {args.index}")

    result = trainer.remove_sample(
        voice_id=args.voice_id, sample_index=args.index, config=config
    )

    if result:
        console.print("[green]✓[/green] 样本已删除")
        console.print(f"[dim]剩余样本数量: {len(voice.samples)}[/dim]")
        return 0
    else:
        console.print("[red]✗[/red] 删除样本失败")
        return 1


def cmd_voice_samples(args):
    """列出音色的所有样本"""
    from lib.notify.voice import VoiceTrainer

    trainer = VoiceTrainer()
    samples = trainer.get_samples(args.voice_id)

    if not samples:
        console.print(f"[dim]音色 {args.voice_id} 没有样本[/dim]")
        return 0

    from rich.table import Table

    table = Table(title=f"[bold]音色 {args.voice_id} 的样本[/bold]")
    table.add_column("索引", style="cyan", width=8)
    table.add_column("文件名", style="white", width=30)
    table.add_column("时长", style="yellow", width=10)
    table.add_column("路径", style="dim", width=50)

    for i, sample in enumerate(samples):
        table.add_row(
            str(i),
            os.path.basename(sample.path),
            f"{sample.duration:.1f}秒",
            sample.path,
        )

    console.print(table)
    return 0


def cmd_voice_retrain(args):
    """使用所有样本重新训练音色"""
    from lib.notify.voice import VoiceTrainer

    trainer = VoiceTrainer()

    console.print(f"[cyan]重新训练音色:[/cyan] {args.voice_id}")

    result = trainer.retrain(voice_id=args.voice_id)

    if result:
        console.print("[green]✓[/green] 重新训练完成")
        return 0
    else:
        console.print("[red]✗[/red] 重新训练失败")
        return 1


def cmd_voice_finetune(args):
    """XTTS 深度微调"""
    from lib.notify.voice import VoiceTrainer

    trainer = VoiceTrainer()

    console.print(f"[cyan]XTTS 深度微调:[/cyan] {args.voice_id}")
    console.print(f"[dim]训练轮数:[/dim] {args.epochs}")
    console.print(f"[dim]使用 GPU:[/dim] {not args.cpu}")

    result = trainer.finetune(
        voice_id=args.voice_id, epochs=args.epochs, use_gpu=not args.cpu
    )

    if result:
        console.print("[green]✓[/green] 微调完成")
        return 0
    else:
        console.print("[red]✗[/red] 微调失败")
        return 1


def cmd_voice_info(args):
    """显示声音信息"""
    from lib.notify.config import load_config

    config = load_config()
    voice = config.voices.get(args.voice_id)

    if not voice:
        console.print(f"[red]✗[/red] 音色不存在: {args.voice_id}")
        return 1

    console.print(
        Panel.fit(
            f"[bold cyan]音色信息[/bold cyan]\n\n"
            f"[dim]ID:[/dim] {voice.id}\n"
            f"[dim]名称:[/dim] {voice.name}\n"
            f"[dim]引擎:[/dim] {voice.engine}\n"
            f"[dim]语言:[/dim] {voice.language}\n"
            f"[dim]语速:[/dim] {voice.speed}x\n"
            f"[dim]音调:[/dim] {voice.pitch}x\n"
            f"[dim]是否克隆:[/dim] {'是' if voice.is_cloned else '否'}\n"
            f"[dim]参考音频:[/dim] {voice.speaker_wav or 'N/A'}\n"
        )
    )

    return 0


def cmd_config_show(args):
    """显示配置"""
    from lib.notify.config import load_config

    config = load_config()

    console.print(
        Panel.fit(
            f"[bold cyan]通知配置[/bold cyan]\n\n"
            f"[dim]默认音色:[/dim] {config.default_voice_id or '未设置'}\n"
            f"[dim]TTS 引擎:[/dim] {config.tts_engine}\n"
            f"[dim]系统通知:[/dim] {'启用' if config.system_notification else '禁用'}\n"
            f"[dim]TTS 播报:[/dim] {'启用' if config.tts_enabled else '禁用'}\n"
            f"[dim]默认语言:[/dim] {config.language}\n"
            f"[dim]音色数量:[/dim] {len(config.voices)}\n"
        )
    )

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
            console.print("[red]✗[/red] 设置失败: 音色不存在")
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


def looks_like_message(text):
    """判断文本是否像消息内容

    Returns:
        True 如果看起来像消息，False 如果可能是拼写错误的命令
    """
    import difflib

    # 已知的所有子命令
    all_commands = [
        "notify",
        "speak",
        "voice",
        "config",
        "list",
        "clone",
        "delete",
        "info",
        "show",
        "set",
    ]

    # 检查第一个单词是否与已知命令高度相似（拼写错误）
    words = text.split()
    if words and len(words) < 3:  # 只检查短输入（1-2个单词）
        first_word = words[0].lower()
        # 使用 difflib 检查相似度（cutoff=0.7 要求 70% 相似）
        close_matches = difflib.get_close_matches(
            first_word, all_commands, n=1, cutoff=0.7
        )
        if close_matches:
            # 找到非常相似的命令，说明这很可能是拼写错误
            return False

    # 包含非 ASCII 字符（中文、日文、韩文等）→ 肯定是消息
    if any(ord(c) > 127 for c in text):
        return True

    # 包含空格（像句子）→ 是消息
    if " " in text:
        return True

    # 长度较长（像句子）→ 是消息
    if len(text) > 15:
        return True

    # 短英文单词，允许作为消息
    return True


def main():
    """主入口"""
    # 预处理：提取 --debug 参数（在 argparse 之前处理）
    debug_mode = False
    filtered_argv = [sys.argv[0]]
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] in ("--debug", "-D"):
            debug_mode = True
            i += 1
        else:
            filtered_argv.append(sys.argv[i])
            i += 1
    sys.argv = filtered_argv

    # 启用调试模式
    if debug_mode:
        from lib.logging import enable_debug

        enable_debug()
        console.print("[dim][DEBUG] 调试模式已启用[/dim]")

    # 先检查是否是子命令
    subcommands = ["notify", "speak", "voice", "config"]

    if (
        len(sys.argv) > 1
        and sys.argv[1] not in subcommands
        and not sys.argv[1].startswith("-")
    ):
        # 如果第一个参数不是子命令也不是选项，检查是否像消息内容
        message_parts = []
        options = []
        i = 1
        while i < len(sys.argv):
            if sys.argv[i].startswith("-"):
                # 这是一个选项，添加到选项列表
                options.append(sys.argv[i])
                i += 1
                # 检查是否有参数值
                if i < len(sys.argv) and not sys.argv[i].startswith("-"):
                    options.append(sys.argv[i])
                    i += 1
            else:
                # 这是消息内容的一部分
                message_parts.append(sys.argv[i])
                i += 1

        message = " ".join(message_parts)
        # 检查消息是否确实像消息内容
        if not looks_like_message(message):
            console.print(f"[red]错误:[/red] 未知的命令或参数: {message}")
            console.print("[dim]提示: 使用 'notify --help' 查看可用命令[/dim]")
            console.print("[dim]或者直接输入消息内容发送通知（支持中文、句子等）[/dim]")
            sys.exit(1)

        sys.argv = [sys.argv[0], "notify", message] + options

    parser = argparse.ArgumentParser(
        description="Notify CLI - 通知和语音播报工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  notify "操作完成"                          # 发送系统通知
  notify "操作完成" --title "标题"           # 带标题的通知
  notify "操作完成" --speak                  # 发送通知并语音播报
  notify speak "你好，世界"                  # 仅语音播报
  notify voice list                         # 列出所有音色
  notify voice clone my-voice --audio ref.wav                    # 克隆声音（单文件）
  notify voice clone my-voice --audio *.mp3   --recursive       # 克隆声音（通配符）
  notify voice clone my-voice --audio ~/Downloads/*.wav --finetune  # 增强参考音频优化
  notify voice samples my-voice              # 列出音色的所有样本
  notify voice add my-voice --audio new_sample.wav              # 添加新样本
  notify voice remove my-voice --index 0     # 删除样本
  notify voice retrain my-voice              # 重新训练
  notify voice finetune my-voice --epochs 20 # XTTS 微调（20 轮）
  notify config show                        # 显示配置
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 主命令 - 发送系统通知（当第一个参数是 notify 时）
    notify_parser = subparsers.add_parser("notify", help="发送系统通知")
    notify_parser.add_argument("message", help="通知消息")
    notify_parser.add_argument("--title", "-t", help="通知标题")
    notify_parser.add_argument("--duration", "-d", type=int, help="显示时长（毫秒）")
    notify_parser.add_argument("--icon", "-i", help="图标名称或路径")
    notify_parser.add_argument(
        "--speak", "-s", action="store_true", help="同时语音播报"
    )
    notify_parser.add_argument("--voice", "-v", help="播报时使用的音色 ID")
    notify_parser.add_argument(
        "--non-blocking", "-n", action="store_true", help="非阻塞模式（仅语音播报）"
    )
    notify_parser.set_defaults(func=cmd_notify)

    # speak 命令 - 语音播报
    speak_parser = subparsers.add_parser("speak", help="语音播报")
    speak_parser.add_argument("text", help="要播报的文本")
    speak_parser.add_argument("--voice", "-v", help="音色 ID")
    speak_parser.add_argument(
        "--non-blocking", "-n", action="store_true", help="非阻塞模式"
    )
    speak_parser.set_defaults(func=cmd_speak)

    # voice 命令组 - 声音管理
    voice_parser = subparsers.add_parser("voice", help="声音管理")
    voice_subparsers = voice_parser.add_subparsers(
        dest="voice_command", help="声音子命令"
    )

    # voice list
    voice_list_parser = voice_subparsers.add_parser("list", help="列出所有音色")
    voice_list_parser.set_defaults(func=cmd_voice_list)

    # voice clone
    voice_clone_parser = voice_subparsers.add_parser("clone", help="克隆声音")
    voice_clone_parser.add_argument("voice_id", help="音色 ID")
    voice_clone_parser.add_argument(
        "--audio",
        "-a",
        nargs="+",
        required=True,
        help="参考音频文件路径（支持通配符，如 *.mp3）",
    )
    voice_clone_parser.add_argument("--name", "-n", help="音色名称")
    voice_clone_parser.add_argument("--language", "-l", help="语言代码")
    voice_clone_parser.add_argument(
        "--recursive", "-r", action="store_true", help="递归展开通配符（**/*.mp3）"
    )
    voice_clone_parser.add_argument(
        "--finetune",
        "-f",
        action="store_true",
        help="使用增强的参考音频优化（响度标准化、降噪、淡入淡出）",
    )
    voice_clone_parser.add_argument(
        "--epochs", "-e", type=int, default=10, help="微调训练轮数（默认 10）"
    )
    voice_clone_parser.add_argument(
        "--cpu", action="store_true", help="使用 CPU 而非 GPU 进行微调"
    )
    voice_clone_parser.set_defaults(func=cmd_voice_clone)

    # voice delete
    voice_delete_parser = voice_subparsers.add_parser("delete", help="删除音色")
    voice_delete_parser.add_argument("voice_id", help="音色 ID")
    voice_delete_parser.set_defaults(func=cmd_voice_delete)

    # voice info
    voice_info_parser = voice_subparsers.add_parser("info", help="显示音色信息")
    voice_info_parser.add_argument("voice_id", help="音色 ID")
    voice_info_parser.set_defaults(func=cmd_voice_info)

    # voice samples
    voice_samples_parser = voice_subparsers.add_parser(
        "samples", help="列出音色的所有样本"
    )
    voice_samples_parser.add_argument("voice_id", help="音色 ID")
    voice_samples_parser.set_defaults(func=cmd_voice_samples)

    # voice add
    voice_add_parser = voice_subparsers.add_parser("add", help="添加样本到已有音色")
    voice_add_parser.add_argument("voice_id", help="音色 ID")
    voice_add_parser.add_argument(
        "--audio", "-a", nargs="+", required=True, help="音频文件路径（支持通配符）"
    )
    voice_add_parser.set_defaults(func=cmd_voice_add_sample)

    # voice remove
    voice_remove_parser = voice_subparsers.add_parser("remove", help="从音色中删除样本")
    voice_remove_parser.add_argument("voice_id", help="音色 ID")
    voice_remove_parser.add_argument("index", type=int, help="样本索引")
    voice_remove_parser.set_defaults(func=cmd_voice_remove_sample)

    # voice retrain
    voice_retrain_parser = voice_subparsers.add_parser(
        "retrain", help="使用所有样本重新训练"
    )
    voice_retrain_parser.add_argument("voice_id", help="音色 ID")
    voice_retrain_parser.set_defaults(func=cmd_voice_retrain)

    # voice finetune
    voice_finetune_parser = voice_subparsers.add_parser(
        "finetune", help="增强参考音频优化（响度标准化、降噪、淡入淡出）"
    )
    voice_finetune_parser.add_argument("voice_id", help="音色 ID")
    voice_finetune_parser.add_argument(
        "--epochs", "-e", type=int, default=10, help="训练轮数（默认 10）"
    )
    voice_finetune_parser.add_argument(
        "--cpu", action="store_true", help="使用 CPU 训练"
    )
    voice_finetune_parser.set_defaults(func=cmd_voice_finetune)

    # config 命令组 - 配置管理
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="配置子命令"
    )

    # config show
    config_show_parser = config_subparsers.add_parser("show", help="显示配置")
    config_show_parser.set_defaults(func=cmd_config_show)

    # config set
    config_set_parser = config_subparsers.add_parser("set", help="设置配置")
    config_set_parser.add_argument("--default-voice", help="设置默认音色")
    config_set_parser.add_argument(
        "--enable-tts", type=lambda x: x.lower() == "true", help="启用/禁用 TTS"
    )
    config_set_parser.add_argument(
        "--enable-notification",
        type=lambda x: x.lower() == "true",
        help="启用/禁用系统通知",
    )
    config_set_parser.set_defaults(func=cmd_config_set)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
