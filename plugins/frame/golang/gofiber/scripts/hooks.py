import json
import sys

from lib import logging
from lib.hooks import load_hooks

def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并记录。"""
    try:
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")
        logging.info(f"[Fiber] 接收到事件: {event_name}")

        # 根据事件类型执行特定逻辑
        if event_name == "SessionStart":
            on_session_start(hook_data)
        elif event_name == "UserPromptSubmit":
            on_user_prompt_submit(hook_data)

    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Hook 处理失败: {e}")
        sys.exit(1)

def on_session_start(hook_data: dict) -> None:
    """SessionStart 事件处理"""
    logging.info("[Fiber] 会话开始")

    # 检测项目是否使用 Fiber 框架
    import os
    from pathlib import Path

    project_root = hook_data.get("project_root", "")
    go_mod_path = Path(project_root) / "go.mod"

    if go_mod_path.exists():
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'github.com/gofiber/fiber' in content:
                    logging.info("[Fiber] 检测到 Fiber 项目")
                    # 可以在这里添加特定的初始化逻辑
        except Exception as e:
            logging.debug(f"[Fiber] 读取 go.mod 失败: {e}")

def on_user_prompt_submit(hook_data: dict) -> None:
    """UserPromptSubmit 事件处理"""
    # 可以在这里添加用户提示提交前的处理逻辑
    pass
