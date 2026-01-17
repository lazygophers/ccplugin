#!/usr/bin/env python3
"""Stop Hook wrapper

处理 Stop 事件，统计会话交互并发送通知
"""

import sys
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

from lib.notify.hooks import handle_stop_hook


def main() -> int:
    """
    处理 Stop hook

    从 stdin 读取 hook 输入 JSON，验证并发送会话统计通知

    Returns:
        int: 返回码（0 为成功）
    """
    try:
        exit_code = handle_stop_hook()
        return exit_code if exit_code in (0, 1) else 0
    except Exception:
        # 异常时不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
