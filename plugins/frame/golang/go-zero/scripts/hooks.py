import json
import sys

from lib import logging
from lib.hooks import load_hooks

def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并记录。"""
    try:
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")
        logging.info(f"[go-zero] 接收到事件: {event_name}")

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

    # 检测项目是否使用 go-zero 框架
    from pathlib import Path

    project_root = hook_data.get("project_root", "")
    go_mod_path = Path(project_root) / "go.mod"

    if go_mod_path.exists():
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'github.com/zeromicro/go-zero' in content:
                    logging.info("[go-zero] 检测到 go-zero 项目")

                    # 检查是否有 goctl 工具
                    api_files = list(Path(project_root).rglob("*.api"))
                    if api_files:
                        logging.info(f"[go-zero] 发现 {len(api_files)} 个 API 定义文件")

                    proto_files = list(Path(project_root).rglob("*.proto"))
                    if proto_files:
                        logging.info(f"[go-zero] 发现 {len(proto_files)} 个 Proto 定义文件")

        except Exception as e:
            logging.debug(f"[go-zero] 读取 go.mod 失败: {e}")

def on_user_prompt_submit(hook_data: dict) -> None:
    """UserPromptSubmit 事件处理"""
    pass