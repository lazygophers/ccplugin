"""lrpc 插件 Hooks 处理"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import lib.logging as logging


def handle_session_start(event_data: dict) -> None:
    """SessionStart Hook 处理

    检测项目是否使用 lrpc 框架并记录相关信息。
    """
    cwd = event_data.get("cwd", os.getcwd())
    project_path = Path(cwd)

    # 检测 lrpc 项目
    go_mod = project_path / "go.mod"
    if not go_mod.exists():
        return

    content = go_mod.read_text()
    if "github.com/lazygophers/lrpc" not in content:
        return

    logging.info(f"[lrpc] 检测到 lrpc 项目: {project_path}")

    # 扫描项目结构
    lrpc_files = list(project_path.rglob("*.go"))
    lrpc_count = 0

    for go_file in lrpc_files:
        try:
            content = go_file.read_text()
            if "github.com/lazygophers/lrpc" in content:
                lrpc_count += 1
        except Exception:
            pass

    logging.info(f"[lrpc] 发现 {lrpc_count} 个使用 lrpc 的文件")
