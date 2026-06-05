"""环境变量和路径工具"""

import os

app_name: str = os.getenv("PLUGIN_NAME", default="")


def set_app(name: str) -> None:
    """设置应用名称"""
    global app_name
    app_name = name


def get_app_name() -> str:
    """获取应用名称"""
    return app_name


def get_project_dir() -> str:
    """获取项目目录"""
    return os.getenv("CLAUDE_PROJECT_DIR", default=os.getcwd())


def get_project_plugins_dir() -> str:
    """获取项目插件目录"""
    return os.path.join(get_project_dir(), ".lazygophers", "ccplugin")


def get_project_plugins_gitignore_path() -> str:
    """获取项目插件 gitignore 路径"""
    return os.path.join(get_project_dir(), ".lazygophers", ".gitignore")


def get_plugins_path() -> str:
    """获取插件根目录"""
    return os.getenv("CLAUDE_PLUGIN_ROOT", default=os.getcwd())


def get_plugins_skills_dir() -> str:
    """获取 skills 目录"""
    return os.path.join(get_plugins_path(), "skills.bak")


def get_plugins_commands_dir() -> str:
    """获取 commands 目录"""
    return os.path.join(get_plugins_path(), "commands")


def get_plugins_hooks_dir() -> str:
    """获取 hooks 目录"""
    return os.path.join(get_plugins_path(), "hooks")


def get_plugins_agents_dir() -> str:
    """获取 agents 目录"""
    return os.path.join(get_plugins_path(), "agents.bak")


def get_user_home() -> str:
    """获取用户主目录"""
    return os.path.expanduser("~")


def get_user_dir() -> str:
    """获取用户目录"""
    return os.path.join(get_user_home(), ".lazygophers")


def get_user_plugins_dir() -> str:
    """获取用户插件目录"""
    return os.path.join(get_user_dir(), get_app_name(), "ccplugin")
