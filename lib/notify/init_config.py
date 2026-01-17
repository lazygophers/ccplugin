#!/usr/bin/env python3
"""
Notify插件配置初始化模块
处理配置文件的创建、读取和校验
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# 默认配置文件模板
DEFAULT_CONFIG_TEMPLATE = """# Claude Code 系统通知配置
# 控制各类操作是否需要系统通知和语音播报

# 配置说明：
# - notify: true/false - 是否需要系统通知
# - voice: true/false - 是否需要语音播报（仅在notify=true时有效）

events:
  # 会话开始通知
  SessionStart:
    description: "会话开始事件"
    notify: false
    voice: false

  # 会话结束通知
  SessionEnd:
    description: "会话结束事件"
    notify: false
    voice: false

  # 用户提示提交通知
  UserPromptSubmit:
    description: "用户提示提交事件"
    notify: false
    voice: false

  # 工具使用前的通知
  PreToolUse:
    description: "工具使用前的通知"
    tools:
      Task:
        notify: false
        voice: false
      Bash:
        notify: false
        voice: false
      Glob:
        notify: false
        voice: false
      Grep:
        notify: false
        voice: false
      Read:
        notify: false
        voice: false
      Edit:
        notify: false
        voice: false
      Write:
        notify: false
        voice: false
      WebFetch:
        notify: false
        voice: false
      WebSearch:
        notify: false
        voice: false

  # 工具使用后的通知
  PostToolUse:
    description: "工具使用后的通知"
    tools:
      Task:
        notify: false
        voice: false
      Bash:
        notify: false
        voice: false
      Glob:
        notify: false
        voice: false
      Grep:
        notify: false
        voice: false
      Read:
        notify: false
        voice: false
      Edit:
        notify: false
        voice: false
      Write:
        notify: false
        voice: false
      WebFetch:
        notify: false
        voice: false
      WebSearch:
        notify: false
        voice: false

  # 系统通知事件
  Notification:
    description: "系统通知事件"
    types:
      permission_prompt:
        notify: true
        voice: false
      idle_prompt:
        notify: true
        voice: false
      auth_success:
        notify: false
        voice: false
      elicitation_dialog:
        notify: false
        voice: false

  # 会话停止通知
  Stop:
    description: "会话停止事件"
    notify: false
    voice: false

  # 子代理停止通知
  SubagentStop:
    description: "子代理停止事件"
    notify: false
    voice: false
"""


def get_project_root() -> Optional[Path]:
    """获取项目根目录"""
    try:
        current = Path.cwd()
        for _ in range(10):
            if (current / ".git").exists() or (current / "pyproject.toml").exists():
                return current
            current = current.parent
    except Exception:
        pass
    return None


def get_config_paths() -> tuple[Path, Path]:
    """获取用户和项目的配置文件路径"""
    user_config_dir = Path.home() / ".lazygophers" / "ccplugin" / "notify"
    project_config_dir = None

    # 尝试找到项目根目录
    project_root = get_project_root()
    if project_root is not None:
        project_config_dir = project_root / ".lazygophers" / "ccplugin" / "notify"

    if project_config_dir is None:
        # 如果找不到项目，使用当前工作目录的上层
        project_config_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "notify"

    return user_config_dir, project_config_dir


def get_user_config_path() -> Path:
    """获取用户级配置文件路径"""
    user_config_dir = Path.home() / ".lazygophers" / "ccplugin" / "notify"
    return user_config_dir / "config.yaml"


def get_project_config_path(project_root: Optional[Path] = None) -> Path:
    """获取项目级配置文件路径"""
    if project_root is None:
        project_root = Path.cwd()
    project_config_dir = project_root / ".lazygophers" / "ccplugin" / "notify"
    return project_config_dir / "config.yaml"


def create_config_file(config_path: Path, force: bool = False) -> bool:
    """
    创建配置文件

    Args:
        config_path: 配置文件路径
        force: 是否覆盖已存在的文件

    Returns:
        bool: 是否成功创建
    """
    if config_path.exists() and not force:
        return False

    # 创建目录
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入配置文件
    config_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding='utf-8')
    return True


def update_gitignore(config_path: Path) -> bool:
    """
    更新项目的 .gitignore 文件，添加 .lazygophers/ccplugin/notify

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 是否成功更新
    """
    try:
        # 找到项目根目录
        project_root = get_project_root()
        if project_root is None:
            return False

        # 获取 .gitignore 路径
        gitignore_path = project_root / ".lazygophers" / ".gitignore"

        # 需要添加的条目
        gitignore_entry = "/ccplugin/notify/\n"

        # 创建 .gitignore 目录
        gitignore_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有内容
        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding='utf-8')
        else:
            content = "# 忽略插件数据\n"

        # 检查是否已经包含这个条目
        if gitignore_entry.strip() in content:
            return True

        # 添加新条目
        if not content.endswith('\n'):
            content += '\n'
        content += gitignore_entry

        # 写入 .gitignore
        gitignore_path.write_text(content, encoding='utf-8')
        return True
    except Exception:
        return False


def load_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    加载YAML配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        dict: 配置字典，或None如果加载失败
    """
    if not config_path.exists():
        return None

    try:
        if yaml is None:
            # 如果yaml不可用，尝试使用json
            content = config_path.read_text(encoding='utf-8')
            return json.loads(content)
        else:
            content = config_path.read_text(encoding='utf-8')
            return yaml.safe_load(content)
    except Exception as e:
        print(f"加载配置文件失败 {config_path}: {e}", file=sys.stderr)
        return None


def init_notify_config(verbose: bool = False) -> bool:
    """
    初始化notify配置文件

    在两个位置检查并创建配置文件：
    1. ~/.lazygophers/ccplugin/notify/config.yaml (用户级)
    2. <项目根目录>/.lazygophers/ccplugin/notify/config.yaml (项目级)

    同时更新项目的 .gitignore 文件以忽略 .lazygophers/ccplugin/notify

    Args:
        verbose: 是否输出详细信息

    Returns:
        bool: 初始化是否成功
    """
    user_config_file = get_user_config_path()
    project_config_file = get_project_config_path()

    success = True

    # 初始化用户级配置
    if user_config_file.exists():
        if verbose:
            print(f"✓ 用户配置已存在: {user_config_file}")
    else:
        if create_config_file(user_config_file):
            if verbose:
                print(f"✓ 创建用户配置: {user_config_file}")
        else:
            if verbose:
                print(f"✗ 创建用户配置失败: {user_config_file}")
            success = False

    # 初始化项目级配置
    if project_config_file.exists():
        if verbose:
            print(f"✓ 项目配置已存在: {project_config_file}")
    else:
        if create_config_file(project_config_file):
            if verbose:
                print(f"✓ 创建项目配置: {project_config_file}")
        else:
            if verbose:
                print(f"✗ 创建项目配置失败: {project_config_file}")
            success = False

    # 更新项目 .gitignore
    if update_gitignore(project_config_file):
        if verbose:
            print(f"✓ 已更新 .gitignore 文件")
    else:
        if verbose:
            print(f"✗ 更新 .gitignore 文件失败")
        # 不影响整体成功状态，因为 .gitignore 更新是辅助操作

    return success


def get_effective_config() -> Optional[Dict[str, Any]]:
    """
    获取有效配置（优先级：项目级 > 用户级）

    Returns:
        dict: 合并后的配置，或None如果两个都不存在
    """
    user_config_file = get_user_config_path()
    project_config_file = get_project_config_path()

    # 优先使用项目级配置
    project_config = load_config(project_config_file)
    if project_config is not None:
        return project_config

    # 其次使用用户级配置
    user_config = load_config(user_config_file)
    if user_config is not None:
        return user_config

    return None


if __name__ == "__main__":
    # 测试脚本
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    success = init_notify_config(verbose=verbose)
    sys.exit(0 if success else 1)
