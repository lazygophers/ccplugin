#!/usr/bin/env python3
"""SessionStart Hook wrapper

处理 SessionStart 事件，执行初始化配置
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 sys.path
script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent

if not (project_root / 'lib').exists():
    # 备选：向上查找
    current = script_path
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.notify.init_config import init_notify_config


def main() -> int:
    """
    处理 SessionStart hook

    从 stdin 读取 hook 输入 JSON，验证后执行初始化

    Returns:
        int: 返回码（0 为成功）
    """
    try:
        # 读取标准输入
        hook_input_str = sys.stdin.read()
        if not hook_input_str.strip():
            return 0

        # 解析 JSON
        try:
            hook_input = json.loads(hook_input_str)
        except json.JSONDecodeError:
            # JSON 解析失败，但不中断主程序
            return 0

        # 验证 hook_event_name
        if hook_input.get("hook_event_name") != "SessionStart":
            return 0

        # 执行初始化配置
        try:
            init_notify_config(verbose=False)
        except Exception:
            # 初始化失败时，不中断主程序
            pass

        return 0

    except Exception:
        # 所有异常都返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
