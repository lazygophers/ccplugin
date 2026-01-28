"""GORM 插件 CLI 入口"""
import click

@click.group()
def main():
    """GORM 插件"""
    pass

@main.command()
def hooks():
    """处理 hook 事件"""
    import json
    import sys
    from lib import logging
    from lib.hooks import load_hooks

    try:
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")
        logging.info(f"[gorm] 接收到事件: {event_name}")

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
    import os
    from pathlib import Path

    project_root = hook_data.get("project_root", "")
    go_mod_path = Path(project_root) / "go.mod"

    if go_mod_path.exists():
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'gorm.io/gorm' in content:
                    logging.info("[gorm] 检测到 GORM 项目")

                    # 检查是否有模型文件
                    model_files = list(Path(project_root).rglob("*model*.go"))
                    if model_files:
                        logging.info(f"[gorm] 发现 {len(model_files)} 个模型文件")

        except Exception as e:
            logging.debug(f"[gorm] 读取 go.mod 失败: {e}")

def on_user_prompt_submit(hook_data: dict) -> None:
    """UserPromptSubmit 事件处理"""
    pass

if __name__ == "__main__":
    main()
