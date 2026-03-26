#!/usr/bin/env python3
"""通知 CLI - 供 hooks.mjs 调用的简单入口"""
import argparse

from notify import start_text_tts, show_system_notification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--message', required=True)
    parser.add_argument('--event', default='')
    parser.add_argument('--play-sound', action='store_true')
    args = parser.parse_args()

    tts_pid = None
    if args.play_sound:
        tts_pid = start_text_tts(args.message)

    show_system_notification(args.message, tts_pid=tts_pid, event=args.event)


if __name__ == '__main__':
    main()
